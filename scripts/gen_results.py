from .utilities import ask_question_save_answer, get_extra_info

def is_skip_answer(singlea): 
    return ('answer' in singlea and '?' in singlea['answer']) or ('answer0' in singlea and '?' in singlea['answer0']) 

def get_singleq_nodes(qnaengine, question_data, qtype, embedding_conf, ofile): 
    nodes = qnaengine.getSimilarNodes(question_data[qtype], embedding_conf["top_similar"]) 
    q_nr = f"{question_data['nr']}-0" if qtype == 'question0' else question_data['nr']  
    print(f"\nQ: {q_nr}\n{nodes['text']}\n{nodes['metadata']}\n{nodes['score']}", file=ofile) 

def set_extra_info(question_data, pilchapters, mk107chapters, nslchapters, mki3chapters, qnaengine): 
    print(question_data['nr'], end=' ')
    info = get_extra_info(question_data, pilchapters, mk107chapters, nslchapters, mki3chapters) 
    info = qnaengine.compressPrompt(info, 3000) 
    return info 

def add_result(qtype, qnaengine, embedding_conf, promptdict, extrainfo, question_data, answer_data, ofile, results_table):
    bcontinue_main_question = True
    if qtype == 'question0':
        current_prompt = promptdict['0']
        suffix = '0'
    else:
        current_prompt = promptdict[str(question_data['nr'])]
        suffix = ''

    result = ask_question_save_answer( 
        qnaengine, embedding_conf, current_prompt + extrainfo, 
        question_data[qtype], f"{question_data['nr']}-{suffix}", answer_data[f"answer{suffix}"]
    ) 
    results_table.append(result)

    if result[1] != result[2]:
        get_singleq_nodes(qnaengine, question_data, qtype, embedding_conf, ofile) 
    
    if qtype == 'question0' and result[1] == 'nē': 
        bcontinue_main_question = False  
         
    return results_table, bcontinue_main_question
    

def _process_single_question(question_data, answer_data, qnaengine, embedding_conf, promptdict, pilchapters, mk107chapters, nslchapters, mki3chapters, ofile, results_table): 
    if 'check' in question_data: 
        return True 

    extrainfo = set_extra_info(question_data, pilchapters, mk107chapters, nslchapters, mki3chapters, qnaengine) 
    bcontinue_main_question = True
 
    if 'question0' in question_data: 
        if is_skip_answer(answer_data): 
            return True 
        results_table, bcontinue_main_question = add_result('question0', qnaengine, embedding_conf, promptdict, extrainfo, question_data, answer_data, ofile, results_table)
    
    if not bcontinue_main_question: 
        q_nr_to_add = str(question_data['nr']) 
        answer_to_add = answer_data.get('answer', answer_data.get('answer0', ''))  
        results_table.append([q_nr_to_add, 'n/a', answer_to_add, '']) 

    elif 'question' in question_data: 
        if is_skip_answer(answer_data): 
            return False  
        results_table, bcontinue_main_question = add_result('question', qnaengine, embedding_conf, promptdict, extrainfo, question_data, answer_data, ofile, results_table)
    return False 

def gen_results(qnaengine, configfile, embedding_conf, question_dictionary, answer_dictionary, promptdict, supplementary_info): 
    results_table = []
    pilchapters, mk107chapters, nslchapters, mki3chapters = supplementary_info  
    # Generating output file
    with open("nodes.log", 'a', encoding='utf-8') as ofile: 
        print(f"""\n*********************\n{configfile}, {configfile} 
            \n{embedding_conf["embeddingmodel"]}, 
            top_similar: {embedding_conf["top_similar"]}, 
            chunk-size: {embedding_conf["chunk_size"]}, 
            chunk_overlap: {embedding_conf["chunk_overlap"]}""", 
            file=ofile 
        ) 
 
        for singleq, singlea in zip(question_dictionary, answer_dictionary): 
            if 'question' in singleq or 'question0' in singleq:  
                if _process_single_question(singleq, singlea, qnaengine, embedding_conf, promptdict, 
                                        pilchapters, mk107chapters, nslchapters, mki3chapters, ofile, results_table): 
                    continue 
            
            elif 'questions' in singleq: 
                if is_skip_answer(singlea): 
                    continue 
    
                for listq, lista in zip(singleq['questions'], singlea['answers']): 
                    _process_single_question(listq, lista, qnaengine, embedding_conf, promptdict, 
                                            pilchapters, mk107chapters, nslchapters, mki3chapters, ofile, results_table) 
 
    return results_table 
