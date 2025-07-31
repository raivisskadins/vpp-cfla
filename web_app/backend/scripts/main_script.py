import pandas as pd

from scripts.constants import *
from scripts.utilities import get_procurement_content
from scripts.gen_results import gen_results
from scripts.vectorindex import QnAEngine

async def main_script(procurement_file, agreement_file):   # What format are thse files expected as, paths or loaded in files?

    # Fix overwrite
    if overwrite: # overwrtitting report; Delete and create new
        if report_path_csv.exists():
                report_path_csv.unlink()
                    
    if not os.path.exists(report_dir_path):
        os.makedirs(report_dir_path)

    # Getting markdown text from procurement doc
    procurement_content = get_procurement_content(extractor, procurement_file, agreement_file)

    # Creating FAISS vector index for the procurement document
    qnaengine = QnAEngine(embedding,llm)
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
    results_table = gen_results(qnaengine, procurement_file, embedding_conf, question_dictionary, default_answer_dictionary, prompt_dictionary, supplementary_info, questions_to_process)
         
    for row in results_table:
        filename = procurement_file.split('/')[-1].split('\\')[-1]
        row.insert(0, filename)
    
    ### Save output
    data = pd.DataFrame(results_table, columns=["Iepirkuma ID", "Nr", "Atbilde", "Sagaidāmā atbilde", "Pamatojums", "Uzvedne"])
    data.drop(columns="Sagaidāmā atbilde", inplace=True)

    # Drop other unnecessary columns?

    data.to_csv(report_path_csv, 
    mode='a', 
    index=False, 
    header=not report_path_csv.exists(), # only adding one header
    encoding='utf-8')
