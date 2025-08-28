from llama_index.finetuning import generate_qa_embedding_pairs
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from typing import Dict, List
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
import re
import asyncio
import os

from extractmd import Extractor
from vectorindex import QnAEngine

TRAIN_FILES = "../eis_files/train"
VAL_FILES = "../eis_files/val"

QA_GENERATE_PROMPT_TMPL = """\
Context information is below.

---------------------
{context_str}
---------------------

Given the context information and no prior knowledge generate a statement a question whose truth can be verified using context.

Your task is to generate {num_questions_per_chunk} questions or statements. They should be diverse in nature across the document. \
Restrict the questions or statements to the context information provided. DO not include phone numbers, person names, e-mails or other sensitive information. The questions or statements must be in Latvian. \
Do not enumerate them. Your generated output must contain only question or statement text as a single sentence.
"""

embedding=HuggingFaceEmbedding(model_name="BAAI/bge-m3",trust_remote_code=True)

llm=AzureOpenAI(azure_deployment="gpt-4o",
                    azure_endpoint=os.environ.get('AZURE_ENDPOINT',''),
                    temperature=0.0,
                    api_version=os.environ.get('AZURE_OPENAI_VERSION',''), 
                    api_key=os.environ.get('AZURE_OPENAI_KEY',''),
                    timeout=120,max_retries=3,top_p=0.0001)

extractor = Extractor()

##### START Modified version of llama_index\finetuning\embeddings\common.py function save_json
##### Open file needs encoding="utf-8"
class EmbeddingQAFinetuneDataset(BaseModel):

    queries: Dict[str, str]
    corpus: Dict[str, str]
    relevant_docs: Dict[str, List[str]]
    mode: str = "text"

    def save_json(self, path: str) -> None:

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)

##### END Modified version of llama_index\finetuning\embeddings\common.py
        
   
def get_nodes(documents, chunk_size, chunk_overlap) -> List[TextNode]:
    # chunk size is in tokenizer's tokens not characters
    node_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, paragraph_separator="\n") # Parse text with a preference for complete sentences

    nodes = []

    for doc in documents:
        currtext = doc.text
        currtext = re.sub(r"(\*\*SATURS\*\*)([^\*]+)", r"", currtext, flags=re.IGNORECASE)  # Remove content, no usefull information for the RAG
            
        if len(currtext) > 0:
            currtext = currtext.replace(r"\\n", r"\n")
            cur_text_chunks = node_parser.split_text(currtext)

            for idx, chunk in enumerate(cur_text_chunks):
                node = TextNode(text=chunk, metadata=doc.metadata)
                nodes.append(node)
                
    return nodes
    
def load_corpus(directory, verbose=False):
    if verbose:
        print(f"Loading files in {directory}")

    qnaengine = QnAEngine(embedding,llm)
    nodes = []
    
    for filename in os.listdir(directory):
    
        file_path = os.path.join(directory, filename)
        file_content = extractor.convert2markdown(file_path)
        
        try:
            documents = qnaengine.load_md(file_content)
            filenodes = get_nodes(documents, 1536, 0)
            nodes.extend(filenodes)

        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            pass
            
    if verbose:
        print(f"Parsed {len(nodes)} nodes")

    return nodes

async def main():

    val_nodes = load_corpus(VAL_FILES, verbose=True)
    val_dataset = generate_qa_embedding_pairs(val_nodes, llm=llm, qa_generate_prompt_tmpl=QA_GENERATE_PROMPT_TMPL,output_path="val_dataset.json")
    
    train_nodes = load_corpus(TRAIN_FILES, verbose=True)
    train_dataset = generate_qa_embedding_pairs(train_nodes, llm=llm, qa_generate_prompt_tmpl=QA_GENERATE_PROMPT_TMPL,output_path="train_dataset.json")
  
if __name__ == "__main__":
    asyncio.run(main())
