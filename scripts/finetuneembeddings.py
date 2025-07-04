import os

from extractmd import Extractor
from vectorindex import QnAEngine
from utilities import get_procurement_content

from llama_index.finetuning import EmbeddingQAFinetuneDataset
from llama_index.finetuning import SentenceTransformersFinetuneEngine
from llama_index.finetuning import generate_qa_embedding_pairs

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.azure_openai import AzureOpenAI

from sentence_transformers.evaluation import InformationRetrievalEvaluator
from sentence_transformers import SentenceTransformer
from pathlib import Path

import asyncio

embedding_conf = {
    "embeddingmodel": "BAAI/bge-m3",
    "fine_tuned": "bge-m3-procurements",
    "chunk_size": 1536,
    "chunk_overlap": 0,
}

embedding = HuggingFaceEmbedding(
    model_name=embedding_conf["embeddingmodel"], trust_remote_code=True
)

TRAIN_FILES = "../eis_files/train"
VAL_FILES = "../eis_files/val"

llmmodelAzure = {
    "model": "gpt-4o",
    "version": os.environ.get("AZURE_OPENAI_VERSION", ""),
    "azure_deployment": "gpt-4o",
    "azure_endpoint": os.environ.get("AZURE_ENDPOINT", ""),
    "api_key": os.environ.get("AZURE_OPENAI_KEY", ""),
}

llm = AzureOpenAI(
    azure_deployment=llmmodelAzure["azure_deployment"],
    azure_endpoint=llmmodelAzure["azure_endpoint"],
    temperature=0.0,
    api_version=llmmodelAzure["version"],
    api_key=llmmodelAzure["api_key"],
    timeout=120,
    max_retries=3,
    top_p=0.0001,
)

qnaengine = QnAEngine(embedding, llm)
extractor = Extractor()


async def load_corpus(directory, verbose=False):
    if verbose:
        print(f"Loading files in {directory}")

    nodes = []

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Getting markdown text from procurement doc
        file_content = get_procurement_content(extractor, file_path, "")

        documents = qnaengine.load_md(file_content)
        filenodes = await qnaengine.get_nodes(
            documents,
            "Procurement",
            embedding_conf["chunk_size"],
            embedding_conf["chunk_overlap"],
        )

        nodes.extend(filenodes)

    if verbose:
        print(f"Parsed {len(nodes)} nodes")

    return nodes


def evaluate_st(
    dataset,
    model_id,
    name,
):
    corpus = dataset.corpus
    queries = dataset.queries
    relevant_docs = dataset.relevant_docs

    evaluator = InformationRetrievalEvaluator(queries, corpus, relevant_docs, name=name)
    model = SentenceTransformer(model_id)
    output_path = "results/"
    Path(output_path).mkdir(exist_ok=True, parents=True)
    return evaluator(model, output_path=output_path)


async def main():
    train_nodes = await load_corpus(TRAIN_FILES, verbose=True)
    val_nodes = await load_corpus(VAL_FILES, verbose=True)

    train_dataset = generate_qa_embedding_pairs(train_nodes, llm=llm)
    train_dataset.save_json("train_dataset.json")

    train_dataset = EmbeddingQAFinetuneDataset.from_json("train_dataset.json")

    val_dataset = generate_qa_embedding_pairs(val_nodes, llm=llm)
    val_dataset.save_json("val_dataset.json")

    val_dataset = EmbeddingQAFinetuneDataset.from_json("val_dataset.json")

    finetune_engine = SentenceTransformersFinetuneEngine(
        train_dataset,  # Dataset to be trained on
        model_id=embedding_conf[
            "embeddingmodel"
        ],  # HuggingFace reference to base embeddings model
        model_output_path="bge-m3_procurements",  # Output directory for fine-tuned embeddings model
        val_dataset=val_dataset,  # Dataset to validate on
        epochs=2,  # Number of Epochs to train for
    )

    finetune_engine.finetune()

    finetuned_embedding_model = finetune_engine.get_finetuned_model()

    print(finetuned_embedding_model.to_json())

    acc1 = evaluate_st(val_dataset, embedding_conf["embeddingmodel"], name="bge")
    acc2 = evaluate_st(val_dataset, embedding_conf["fine_tuned"], name="finetuned")

    print(
        f"Original model {embedding_conf['embeddingmodel']}: {str(acc1)}\nFine-tuned model {embedding_conf['fine_tuned']}: {str(acc2)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
