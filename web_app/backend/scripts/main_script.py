import os
from .constants import extractor, embedding, llm, embedding_conf, question_dictionary, default_answer_dictionary, prompt_dictionary, supplementary_info, questions_to_process
from .utilities import get_procurement_content
from .gen_results import gen_results
from .vectorindex import QnAEngine
from .status_manager import send_status
from scripts.check_cancelation import check_cancellation

async def main_script(procurement_file_path, agreement_file_path, proc_report_csv_path, Proc_ID):   # What format are thse files expected as, paths or loaded in files?
    await send_status(Proc_ID, "Sakārto sniegto informāciju, pirms atbilžu ģenerēšanas...")
    if os.path.exists(proc_report_csv_path):
        os.remove(proc_report_csv_path)

    if check_cancellation(Proc_ID): return
    procurement_content = get_procurement_content(extractor, str(procurement_file_path), str(agreement_file_path) if agreement_file_path else '') #TODO: fix conversion to str
    
    if check_cancellation(Proc_ID): return
    await send_status(Proc_ID, "MI modeļu ielāde...")
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
    await send_status(Proc_ID, "Jautājumu apstrāde...")
    await gen_results(qnaengine, embedding_conf, question_dictionary, default_answer_dictionary, prompt_dictionary, supplementary_info, questions_to_process, proc_report_csv_path, Proc_ID)

