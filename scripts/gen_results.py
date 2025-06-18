from .utilities import ask_question_save_answer, get_extra_info, get_supplementary_info 

def skip_answer(singlea): 
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

def _process_single_question(question_data, answer_data, qnaengine, embedding_conf, promptdict, pilchapters, mk107chapters, nslchapters, mki3chapters, ofile, results_table): 
    if 'check' in question_data: 
        return True 

    extrainfo = set_extra_info(question_data, pilchapters, mk107chapters, nslchapters, mki3chapters, qnaengine) 
    bcontinue_main_question = True
 
    if 'question0' in question_data: 
        if skip_answer(answer_data): 
            return True
        
        result0 = ask_question_save_answer( 
            qnaengine, embedding_conf, promptdict['0'] + extrainfo, 
            question_data['question0'], f"{question_data['nr']}-0", answer_data['answer0'] 
        ) 
        results_table.append(result0) 
        
        if result0[1] != result0[2]:
            get_singleq_nodes(qnaengine, question_data, 'question0', embedding_conf, ofile) 
        
        if result0[1] == 'nē': 
            bcontinue_main_question = False 
    
    if not bcontinue_main_question: 
        q_nr_to_add = str(question_data['nr']) 
        answer_to_add = answer_data.get('answer', answer_data.get('answer0', ''))  
        results_table.append([q_nr_to_add, 'n/a', answer_to_add, '']) 
    elif 'question' in question_data: 
        if skip_answer(answer_data): 
            return False
            
        result = ask_question_save_answer( 
            qnaengine, embedding_conf, promptdict[str(question_data['nr'])] + extrainfo, 
            question_data['question'], str(question_data['nr']), answer_data['answer'] 
        ) 
        results_table.append(result) 
        
        if result[1] != result[2]:
            get_singleq_nodes(qnaengine, question_data, 'question', embedding_conf, ofile) 
    
    return False 

def gen_results(qnaengine, configfile, embedding_conf, question_dictionary, answer_dictionary, promptdict): 
    results_table = []
    pilchapters, mk107chapters, nslchapters, mki3chapters = get_supplementary_info()  #Jābūt ārpus inifile cikla 
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
                if skip_answer(singlea): 
                    continue 
    
                for listq, lista in zip(singleq['questions'], singlea['answers']): 
                    _process_single_question(listq, lista, qnaengine, embedding_conf, promptdict, 
                                            pilchapters, mk107chapters, nslchapters, mki3chapters, ofile, results_table) 
 
    return results_table 
 