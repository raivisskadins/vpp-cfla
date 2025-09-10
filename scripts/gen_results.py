# Copyright 2025 State Research Programme project
# "Analysis of the Applicability of Artificial Intelligence Methods in the
# Field of European Union Fund Projects" (Project number: VPP-CFLA-Artificial
# Intelligence-2024/1-0003). The project is implemented by the University of Latvia.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .utilities import ask_question_save_answer, get_extra_info
SUFFIX = {"question0": "0", "question": ""}

def is_skip_question(question, answer):
    is_missing_answer = ('answer' in answer and '?' in answer['answer']) or ('answer0' in answer and '?' in answer['answer0'])
    question_marked_to_skip = 'check' in question
    skip_question = is_missing_answer or question_marked_to_skip
    # print(f"Skipping question: {question['nr']}") # for debugging
    return skip_question 

def get_question_nodes(qnaengine, question_data, qtype, embedding_conf, ofile):
    # Serves only for logging? 
    nodes = qnaengine.getSimilarNodes(question_data[qtype], embedding_conf["top_similar"]) 
    q_nr = f"{question_data['nr']}-0" if qtype == 'question0' else question_data['nr']  
    print(f"\nQ: {q_nr}\n{nodes['text']}\n{nodes['metadata']}\n{nodes['score']}", file=ofile)
    return nodes

def set_extra_info(question_data, supplementary_info, qnaengine):
    # Gets extra information that can be attached to the question 
    pilchapters, mk107chapters, nslchapters, mki3chapters = supplementary_info
    info = get_extra_info(question_data, pilchapters, mk107chapters, nslchapters, mki3chapters) 
    info = qnaengine.compressPrompt(info, 3000) 
    return info 

def add_result(qtype, qnaengine, embedding_conf, promptdict, extrainfo, question_data, answer_data, ofile, results_table):
    suffix = SUFFIX[qtype]
    if qtype == 'question0':
        question_id = f"{question_data['nr']}-{suffix}"
        current_prompt = promptdict.get(question_data["nr"]+"-0",promptdict.get("0"))
    else:
        question_id = f"{question_data['nr']}{suffix}"
        if "prompt" in question_data: # Deprecated
            current_prompt = question_data.get("prompt","")
        else:
            current_prompt = promptdict[str(question_data['nr'])]

    full_prompt = current_prompt + extrainfo
    answer_id = answer_data[f"answer{suffix}"]
    query, result = ask_question_save_answer(qnaengine, embedding_conf, full_prompt,
                                      question_data[qtype], question_id, answer_id)
    result.append(query)
    results_table.append(result)
    
    llm_answer = result[1]
    expected_answer = result[2]
    
    answer_main_question = None
    if qtype == 'question0':
        answer_main_question = llm_answer
         
    return results_table, answer_main_question

def question_replace_w_na(question_data, answer_data, results_table):
    # Manually adds answers to main questions where answer0 was "nē"
    q_nr = str(question_data['nr'])
    ans  = answer_data['answer']
    results_table.append([q_nr, 'n/a', ans, ''])

def questions_replace_w_na(questions_data, answers_data, results_table):
    # Goes through all child questions and accounts for questions_0
    for q_data, a_data in zip(questions_data, answers_data):
        if is_skip_question(q_data, a_data): continue

        if 'question0' in q_data:
            q_nr0 = f"{q_data['nr']}-0"
            ans0  = a_data['answer0']
            results_table.append([q_nr0, 'nē', ans0, ''])

        if 'question' in q_data:
            question_replace_w_na(q_data, a_data, results_table)

def question_replace_w_x(question_data, answer_data, results_table):
    # Manually adds 'X' as answers to main questions where answer0 was "kontekstā nav informācijas"
    q_nr = str(question_data['nr'])
    ans  = answer_data['answer']
    results_table.append([q_nr, 'X', ans, ''])

def questions_replace_w_x(questions_data, answers_data, results_table):
    # Goes through all child questions
    for q_data, a_data in zip(questions_data, answers_data):
        if is_skip_question(q_data, a_data): continue

        if 'question0' in q_data:
            q_nr0 = f"{q_data['nr']}-0"
            ans0  = a_data['answer0']
            results_table.append([q_nr0, 'nē', ans0, ''])

        if 'question' in q_data:
            question_replace_w_x(q_data, a_data, results_table)

qcounter = 0

def process_question(question_data, answer_data, qnaengine, embedding_conf, promptdict, supplementary_info, ofile, results_table, questions_to_process): 
    
    if is_skip_question(question_data, answer_data): return
        
    extrainfo = set_extra_info(question_data, supplementary_info, qnaengine)

    print(question_data['nr'], end=' ')
    global qcounter
    qcounter += 1
    if qcounter % 20 == 0:
        print("")

    # Handle optional question0; If it returns "nē" we replace all child questions with "n/a" and skip to next question
    if 'question0' in question_data:
        results_table, q0_answer = add_result('question0', qnaengine, embedding_conf, promptdict, extrainfo,question_data, answer_data, ofile, results_table)

        if not q0_answer:
            return
        if q0_answer == 'nē':
            if 'question' in question_data:
                question_replace_w_na(question_data, answer_data,
                                        results_table)
            if 'questions' in question_data:
                questions_replace_w_na(question_data['questions'],answer_data.get('answers'),results_table)
            return
        if q0_answer == 'kontekstā nav informācijas':
            if 'question' in question_data:
                question_replace_w_x(question_data, answer_data,
                                        results_table)
            if 'questions' in question_data:
                questions_replace_w_x(question_data['questions'],answer_data.get('answers'),results_table)
            return

    # Otherwise just handle questions normally
    if 'question' in question_data:
        results_table, _ = add_result(
            'question', qnaengine, embedding_conf, promptdict, extrainfo,
            question_data, answer_data, ofile, results_table
        )
    
    if 'questions' in question_data:
        for nested_question, nested_answer in zip(question_data.get('questions'),answer_data.get('answers')):
            # If questions_to_process is empty, process all questions. If not, process only those questions that are in the list
            if not questions_to_process or nested_question['nr'] in questions_to_process:
                process_question(nested_question, nested_answer, qnaengine, embedding_conf, promptdict,supplementary_info,ofile, results_table, questions_to_process)

def gen_results(qnaengine, configfile, embedding_conf, question_dictionary, answer_dictionary, promptdict, supplementary_info, questions_to_process): 
    results_table = []  
    # Generating log file
    with open("nodes.log", 'a', encoding='utf-8') as ofile: 
        print(f"""\n*********************\n{configfile}, {configfile} 
            \n{embedding_conf["embeddingmodel"]}, 
            top_similar: {embedding_conf["top_similar"]}, 
            chunk-size: {embedding_conf["chunk_size"]}, 
            chunk_overlap: {embedding_conf["chunk_overlap"]}""", 
            file=ofile 
        )
        # TODO add tqdm; however you would need count all of the questions that will be answered - non trivial filtering
        for question, answer in zip(question_dictionary, answer_dictionary):
            # If questions_to_process is empty, process all questions. If not, process only those questions that are in the list
            if not questions_to_process or question['nr'] in questions_to_process:
                process_question(question, answer, qnaengine, embedding_conf, promptdict, supplementary_info, ofile, results_table, questions_to_process)
    return results_table 
