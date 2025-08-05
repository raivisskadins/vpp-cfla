import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from datetime import date
from pathlib import Path
from .extractmd import Extractor
from .utilities import get_prompt_dict, get_questions, get_answers, get_supplementary_info

embedding_conf = {
    "embeddingmodel": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", #"sentence-transformers/paraphrase-multilingual-mpnet-base-v2",  # "BAAI/bge-m3" "nomic-ai/nomic-embed-text-v2-moe" # "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    "chunk_size": 1536,
    "chunk_overlap": 0,
    "top_similar": 5,
    "n4rerank": 0, #How many nodes to retrieve for reranking. If 0, reranker is not used
    "use_similar_chunks": True, #To use similar chunks or the whole document as the context
    "prevnext": True #to include in the context also the previouse and the next chunk of the current similar chunk
}
embedding=HuggingFaceEmbedding(model_name=embedding_conf["embeddingmodel"],trust_remote_code=True)

# LLM Setup 
llmmodelAzure = { "model": "gpt-4o",
                "version":os.environ.get('AZURE_OPENAI_VERSION',''),
                "azure_deployment":"gpt-4o",
                "azure_endpoint":os.environ.get('AZURE_ENDPOINT',''),
                "api_key":os.environ.get('AZURE_OPENAI_KEY','')}

llm=AzureOpenAI(azure_deployment=llmmodelAzure["azure_deployment"],
                azure_endpoint=llmmodelAzure["azure_endpoint"],temperature=0.0,
                api_version=llmmodelAzure["version"], api_key=llmmodelAzure["api_key"],
                timeout=120,max_retries=3,top_p=0.0001)

extractor = Extractor() # Markdown doc extractor

# Script dir for getting relative paths for notebook file
script_dir = Path(".").resolve()

# Document paths
question_file_path = script_dir / "questions" / "questions.yaml" # original.yaml
prompt_file = script_dir / "questions" / "prompts.tsv"
report_dir = script_dir / "reports"
answer_file_dir = script_dir / "answers" # Only necessary for the answer file template

overwrite = True # TODO figure out if we are keeping it
            # If true this will delete the existing report and generate a new one;
            # Else - new data will be appended only if it isn't in the CSV file.

question_dictionary = get_questions(question_file_path)
prompt_dictionary = get_prompt_dict(prompt_file)
supplementary_info = get_supplementary_info()

default_answer_file_path = script_dir / 'template.yaml'
default_answer_dictionary = get_answers(default_answer_file_path)

# questions_to_process = ["7", "9", "13", "24"]
questions_to_process = ["7", "9", "13", "24"]