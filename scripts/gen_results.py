from .utilities import ask_question_save_answer, get_extra_info, get_supplementary_info



# TODO refactor this function so it's more readable
def gen_results(qnaengine, configfile, embedding_conf, question_dictonary, answer_dictonary, promptdict):
    results_table = []
    pilchapters, mk107chapters, nslchapters, mki3chapters = get_supplementary_info()
    # Generating output file
    with open("nodes.log", 'a', encoding='utf-8') as ofile:
        
        print(f"""\n*********************\n{configfile}, {configfile}
              \n{embedding_conf["embeddingmodel"]}, 
              top_similar: {embedding_conf["top_similar"]}, 
              chunk-size: {embedding_conf["chunk_size"]}, 
              chunk_overlap: {embedding_conf["chunk_overlap"]}""",
              file=ofile
              )
        
        for singleq, singlea in zip(question_dictonary,answer_dictonary):
            print(singleq['nr'],end=' ')
            bcontinue = True
            extrainfo = get_extra_info(singleq, pilchapters, mk107chapters, nslchapters, mki3chapters)    
            extrainfo = qnaengine.compressPrompt(extrainfo,3000)
            
            if 'question0' in singleq:
                result0 = ask_question_save_answer(qnaengine, 
                                                   embedding_conf, 
                                                   promptdict['0'] + extrainfo, 
                                                   singleq['question0'], 
                                                   f"{singleq['nr']}-0", 
                                                   singlea['answer0'])
                results_table.append(result0)
                if results_table[-1][1] != results_table[-1][2]:
                    nodes = qnaengine.getSimilarNodes(singleq['question0'],embedding_conf["top_similar"])
                    print(f"\nQ: {singleq['nr']}-0\n{nodes['text']}\n{nodes['metadata']}\n{nodes['score']}",file=ofile) 
        
                if result0[1] == 'nē':
                    bcontinue = False
            
            if bcontinue == False:
                if 'question' in singleq:
                    results_table.append([str(singleq['nr']),'n/a',singlea['answer'],''])
                elif 'questions' in singleq:
                    for listq, lista in zip(singleq['questions'],singlea['answers']):
                        results_table.append([str(listq['nr']),'n/a',lista['answer'],''])
            elif 'question' in singleq:
                results_table.append(ask_question_save_answer(qnaengine, 
                                                              embedding_conf,
                                                              promptdict[str(singleq['nr'])] + extrainfo, 
                                                              singleq['question'], 
                                                              str(singleq['nr']), 
                                                              singlea['answer']))
                if results_table[-1][1] != results_table[-1][2]: # TODO make this more readable; this check is in multiple ifs
                    nodes = qnaengine.getSimilarNodes(singleq['question'],embedding_conf["top_similar"])
                    print(f"\nQ: {singleq['nr']}\n{nodes['text']}\n{nodes['metadata']}\n{nodes['score']}",file=ofile) 
            elif 'questions' in singleq:
                for listq, lista in zip(singleq['questions'],singlea['answers']):
                    print(listq['nr'],end=' ')
                    bcontinue = True
                    extrainfo = get_extra_info(listq, pilchapters, mk107chapters, nslchapters, mki3chapters) 
                    extrainfo = qnaengine.compressPrompt(extrainfo,3000)
                    
                    if 'question0' in listq:
                        result0 = ask_question_save_answer(qnaengine, 
                                                           embedding_conf, 
                                                           promptdict['0'] + extrainfo, 
                                                           listq['question0'], 
                                                           f"{listq['nr']}-0", 
                                                           lista['answer0'])
                        results_table.append(result0)
                        if results_table[-1][1] != results_table[-1][2]:
                            nodes = qnaengine.getSimilarNodes(listq['question0'],embedding_conf["top_similar"])
                            print(f"\nQ: {listq['nr']}-0\n{nodes['text']}\n{nodes['metadata']}\n{nodes['score']}",file=ofile) 
                
                        if result0[1] == 'nē':
                            bcontinue = False
                            
                    if bcontinue == False:
                        results_table.append([str(listq['nr']),'n/a',lista['answer0'],''])
                    else:
                        results_table.append(ask_question_save_answer(qnaengine,
                                                                    embedding_conf,
                                                                    promptdict[str(listq['nr'])] + extrainfo, 
                                                                    listq['question'], # TODO
                                                                    str(listq['nr']), 
                                                                    lista['answer']))
                        if results_table[-1][1] != results_table[-1][2]:
                            nodes = qnaengine.getSimilarNodes(listq['question'],embedding_conf["top_similar"])
                            print(f"\nQ: {listq['nr']}\n{nodes['text']}\n{nodes['metadata']}\n{nodes['score']}",file=ofile)
    return results_table