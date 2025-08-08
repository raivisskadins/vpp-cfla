import os
from typing import List, Dict, Tuple
import uuid
import warnings
from tqdm import tqdm
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.schema import MetadataMode, TextNode
from llama_index.finetuning import SentenceTransformersFinetuneEngine

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from sentence_transformers.evaluation import InformationRetrievalEvaluator
from sentence_transformers import SentenceTransformer
from pathlib import Path
import re
import json
import asyncio
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

##### START Modified version of llama_index\finetuning\embeddings\common.py
##### Open file needs encoding="utf-8"


class EmbeddingQAFinetuneDataset(BaseModel):
    """Embedding QA Finetuning Dataset.

    Args:
        queries (Dict[str, str]): Dict id -> query.
        corpus (Dict[str, str]): Dict id -> string.
        relevant_docs (Dict[str, List[str]]): Dict query id -> list of doc ids.
    """

    queries: Dict[str, str]
    corpus: Dict[str, str]
    relevant_docs: Dict[str, List[str]]
    mode: str = "text"

    @property
    def query_docid_pairs(self) -> List[Tuple[str, List[str]]]:
        """Get query, relevant doc ids."""
        return [
            (query, self.relevant_docs[query_id])
            for query_id, query in self.queries.items()
        ]

    def save_json(self, path: str) -> None:
        """Save the dataset to a JSON file.

        Args:
            path (str): The file path to save the JSON.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)

    @classmethod
    def from_json(cls, path: str) -> "EmbeddingQAFinetuneDataset":
        """Load the dataset from a JSON file.

        Args:
            path (str): The file path to load the JSON from.

        Returns:
            EmbeddingQAFinetuneDataset: The loaded dataset.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


PREV_QA_GENERATE_PROMPT_TMPL = """\
Context information is below.

---------------------
{context_str}
---------------------

Given the context information and no prior knowledge generate only questions based on the below query.

You are a Teacher/ Professor. Your task is to setup {num_questions_per_chunk} questions for an upcoming quiz/examination. \
The questions should be diverse in nature across the document. \
Restrict the questions to the context information provided. The questions must be in Latvian. \
Do not enumerate questions. Your generated output must contain only question text as a single sentence.
"""

QA_GENERATE_PROMPT_TMPL = """\
Context information is below.

---------------------
{context_str}
---------------------

Given the context information and no prior knowledge generate a statement a question whose truth can be verified using context.

Your task is to generate {num_questions_per_chunk} questions or statements. They should be diverse in nature across the document. \
Restrict the questions or statements to the context information provided. The questions or statements must be in Latvian. \
Do not enumerate them. Your generated output must contain only question or statement text as a single sentence.
"""


def load_existing_data(
    path: str,
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, List[str]]]:
    """Load existing data from a JSON file if it exists.

    Args:
        path (str): The file path to load the JSON from.

    Returns:
        Tuple[Dict[str, str], Dict[str, str], Dict[str, List[str]]]: The loaded queries, corpus, and relevant_docs.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data["queries"], data["corpus"], data["relevant_docs"]
    except FileNotFoundError:
        return {}, {}, {}


##### END Modified version of llama_index\finetuning\embeddings\common.py

embedding_conf = {
    "embeddingmodel": "E:\\GPTQnAData\\bge-m3",  #"/tmp/Daiga/bge-m3",  # "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",  # "BAAI/bge-m3",
    "fine_tuned": "bge-m3-procurements_lr9e-6_warmup28600",  # "paraphrase-multilingual-procurements",  # "bge-m3-procurements",
    "fine_tuned_path": "E:\\eis_files_crawled\\finetuned\\bge-m3-procurements_lr9e-6_warmup28600",  # "../paraphrase-multilingual-procurements",
    "chunk_size": 1536,
    "chunk_overlap": 0,
}

embedding = HuggingFaceEmbedding(
    model_name=embedding_conf["embeddingmodel"], trust_remote_code=True
)

TRAIN_FILES = "../eis_files/train"
VAL_FILES = "../eis_files/val"

def evaluate_st(
    dataset,
    model_id,
    name,
):
    corpus = dataset.corpus
    queries = dataset.queries
    relevant_docs = dataset.relevant_docs

    evaluator = InformationRetrievalEvaluator(queries, corpus, relevant_docs, name=name)
    model = SentenceTransformer(model_name_or_path=model_id,device = device)
    output_path = "E:\\eis_files_crawled\\finetuned"
    Path(output_path).mkdir(exist_ok=True, parents=True)
    return evaluator(model, output_path=output_path)


async def train_only():
    train_dataset = EmbeddingQAFinetuneDataset.from_json(
        "../eis_files/train_dataset.json"
    )
    val_dataset = EmbeddingQAFinetuneDataset.from_json("../eis_files/val_dataset.json")
    
    finetune_engine = SentenceTransformersFinetuneEngine(
        train_dataset,  # Dataset to be trained on
        model_id=embedding_conf[
            "embeddingmodel"
        ],  # HuggingFace reference to base embeddings model
        model_output_path=embedding_conf[
            "fine_tuned_path"
        ],  # Output directory for fine-tuned embeddings model
        val_dataset=val_dataset,  # Dataset to validate on
        epochs=2,  # Number of Epochs to train for
        device = device,
        batch_size=3,
        evaluation_steps=100,
        use_all_docs=True,
        checkpoint_save_steps=500
    )

    finetune_engine.finetune(resume_from_checkpoint=True, save_checkpoints=True)
    print("Finished!!!")
    finetuned_embedding_model = finetune_engine.get_finetuned_model()

    print(finetuned_embedding_model.to_json())

    acc1 = evaluate_st(val_dataset, embedding_conf["embeddingmodel"], name="original")
    acc2 = evaluate_st(val_dataset, embedding_conf["fine_tuned_path"], name="finetuned")

    print(
        f"Original model {embedding_conf['embeddingmodel']}: {str(acc1)}\nFine-tuned model {embedding_conf['fine_tuned']}: {str(acc2)}"
    )

async def evaluate_only():
    val_dataset = EmbeddingQAFinetuneDataset.from_json("../eis_files/val_dataset.json")
    
    acc1 = evaluate_st(val_dataset, embedding_conf["embeddingmodel"], name="original")
    acc2 = evaluate_st(val_dataset, embedding_conf["fine_tuned_path"], name=embedding_conf['fine_tuned'])
    with open("E:\\eis_files_crawled\\finetuned\\results.txt", 'a') as fout:
        print(
        f"Original model {embedding_conf['embeddingmodel']}: {str(acc1)}\nFine-tuned model {embedding_conf['fine_tuned']}: {str(acc2)}", file = fout)
    
if __name__ == "__main__":
    asyncio.run(evaluate_only())
