import pandas as pd
import os
from scripts.constants import extractor, embedding, llm, embedding_conf, question_dictionary, default_answer_dictionary, prompt_dictionary, supplementary_info, questions_to_process
from scripts.utilities import get_procurement_content
from scripts.gen_results import gen_results
from scripts.vectorindex import QnAEngine

async def main_script(procurement_file_path, agreement_file_path, proc_report_csv_path, Proc_ID):   # What format are thse files expected as, paths or loaded in files?
    # Getting markdown text from procurement doc
    procurement_content = get_procurement_content(extractor, procurement_file_path, agreement_file_path)
    print("Retrieved procurement content")

    # Creating FAISS vector index for the procurement document
    qnaengine = QnAEngine(embedding,llm)
    print("Qnaengine loading")
    if embedding_conf["use_similar_chunks"] == True:
        await qnaengine.createIndex(
            procurement_content,
            "Procurement",
            chunk_size=embedding_conf["chunk_size"],
            chunk_overlap=embedding_conf["chunk_overlap"]
        )
    else:
        await qnaengine.load_text(procurement_content)   

    ### Generating results
    print("Generating results")
    results_table = gen_results(qnaengine, embedding_conf, question_dictionary, default_answer_dictionary, prompt_dictionary, supplementary_info, questions_to_process)
    
    # add "Iepirkuma ID" as procurement_id to results table
    # TODO still would be nice to move it inside gen_results
    for row in results_table:
            row.insert(0, Proc_ID)
    ### Save output
    data = pd.DataFrame(results_table, columns=["Iepirkuma ID", "Nr", "Atbilde", "Sagaidāmā atbilde", "Pamatojums"])
    data.drop(columns="Sagaidāmā atbilde", inplace=True)
    data.to_csv(proc_report_csv_path, 
    mode='a', 
    index=False, 
    header=True,
    encoding='utf-8')
