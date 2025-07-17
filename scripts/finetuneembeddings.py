import os

from extractmd import Extractor
from vectorindex import QnAEngine
from utilities import get_procurement_content
from llama_index.core.node_parser import SentenceSplitter
from typing import List, Dict, Tuple
import uuid
import warnings
from tqdm import tqdm
from llama_index.core.bridge.pydantic import BaseModel
from llama_index.core.llms.utils import LLM
from llama_index.core.schema import MetadataMode, TextNode
from llama_index.finetuning import SentenceTransformersFinetuneEngine

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.azure_openai import AzureOpenAI

from sentence_transformers.evaluation import InformationRetrievalEvaluator
from sentence_transformers import SentenceTransformer
from pathlib import Path
import re
import json
import asyncio

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


def generate_qa_embedding_pairs(
    nodes: List[TextNode],
    llm: LLM,
    qa_generate_prompt_tmpl: str = QA_GENERATE_PROMPT_TMPL,
    num_questions_per_chunk: int = 2,
    retry_limit: int = 3,
    on_failure: str = "continue",  # options are "fail" or "continue"
    save_every: int = 500,
    output_path: str = "qa_finetune_dataset.json",
    verbose: bool = True,
) -> EmbeddingQAFinetuneDataset:
    """Generate QA pairs from a set of nodes and save periodically.

    Args:
        nodes (List[TextNode]): List of TextNode objects to process.
        llm (LLM): The large language model to use for generating questions.
        qa_generate_prompt_tmpl (str): The template for generating QA prompts.
        num_questions_per_chunk (int): Number of questions to generate per chunk of text.
        retry_limit (int): Number of times to retry on failure.
        on_failure (str): Action to take on repeated failures ('fail' or 'continue').
        save_every (int): Number of nodes to process before saving the dataset.
        output_path (str): The file path to save the JSON output.
        verbose (bool): If True, print debugging messages.

    Returns:
        EmbeddingQAFinetuneDataset: The generated dataset.
    """
    queries, corpus, relevant_docs = load_existing_data(output_path)

    node_dict = {
        node.node_id: node.get_content(metadata_mode=MetadataMode.NONE)
        for node in nodes
    }

    start_index = len(corpus)

    save_counter = start_index

    for node_id, text in tqdm(
        list(node_dict.items())[start_index:], initial=start_index
    ):
        query = qa_generate_prompt_tmpl.format(
            context_str=text, num_questions_per_chunk=num_questions_per_chunk
        )

        retry_count = 0
        success = False
        while retry_count < retry_limit:
            try:
                response = llm.complete(query)
                success = True
                break
            except Exception as e:
                retry_count += 1
                if verbose:
                    print(
                        f"Error querying LLM: {e}. Retrying {retry_count}/{retry_limit}..."
                    )

        if not success:
            if on_failure == "fail":
                raise RuntimeError(f"Failed to query LLM after {retry_limit} retries.")
            elif on_failure == "continue":
                if verbose:
                    print(f"Skipping node {node_id} after {retry_limit} retries.")
                continue

        result = str(response).strip().split("\n")
        questions = [
            re.sub(r"^\d+[\).\s]", "", question).strip() for question in result
        ]
        questions = [question for question in questions if len(question) > 0][
            :num_questions_per_chunk
        ]

        num_questions_generated = len(questions)
        if num_questions_generated < num_questions_per_chunk:
            warnings.warn(
                f"Fewer questions generated ({num_questions_generated}) "
                f"than requested ({num_questions_per_chunk})."
            )

        for question in questions:
            question_id = str(uuid.uuid4())
            queries[question_id] = question
            relevant_docs[question_id] = [node_id]

        corpus[node_id] = text

        save_counter += 1
        if save_counter % save_every == 0:
            dataset = EmbeddingQAFinetuneDataset(
                queries=queries, corpus=corpus, relevant_docs=relevant_docs
            )
            dataset.save_json(output_path)
            if verbose:
                print(f"Saved progress at {save_counter} entries.")

    # Save final dataset
    dataset = EmbeddingQAFinetuneDataset(
        queries=queries, corpus=corpus, relevant_docs=relevant_docs
    )
    dataset.save_json(output_path)
    if verbose:
        print("Final dataset saved.")

    return dataset


##### END Modified version of llama_index\finetuning\embeddings\common.py

embedding_conf = {
    "embeddingmodel": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",  # "BAAI/bge-m3",
    "fine_tuned": "paraphrase-multilingual-procurements",  # "bge-m3-procurements",
    "fine_tuned_path": "../paraphrase-multilingual-procurements",
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


async def get_nodes(documents, chunk_size, chunk_overlap) -> List[TextNode]:
    # chunk size is in tokenizer's tokens not characters
    node_parser = SentenceSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, paragraph_separator="\n"
    )
    # Parse text with a preference for complete sentences

    nodes = []

    for doc in documents:
        if len(doc.text) > 0:
            currtext = doc.text.replace(r"\\n", r"\n")
            cur_text_chunks = node_parser.split_text(currtext)

            for idx, chunk in enumerate(cur_text_chunks):
                node = TextNode(text=chunk, metadata=doc.metadata)

                node.excluded_embed_metadata_keys = list(node.metadata.keys())
                nodes.append(node)

    return nodes


async def load_corpus(directory, verbose=False):
    if verbose:
        print(f"Loading files in {directory}")

    nodes = []

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Getting markdown text from procurement doc
        file_content = get_procurement_content(extractor, file_path, "")

        documents = qnaengine.load_md(file_content)
        filenodes = await get_nodes(
            documents,
            embedding_conf["chunk_size"],
            embedding_conf["chunk_overlap"],
        )

        if verbose:
            print(f"{len(filenodes)} nodes in {filename}")

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
    model = SentenceTransformer(model_name_or_path=model_id)
    output_path = "../emb_eval_results/"
    Path(output_path).mkdir(exist_ok=True, parents=True)
    return evaluator(model, output_path=output_path)


async def main():
    train_nodes = await load_corpus(TRAIN_FILES, verbose=True)
    train_dataset = generate_qa_embedding_pairs(
        train_nodes,
        llm=llm,
        qa_generate_prompt_tmpl=QA_GENERATE_PROMPT_TMPL,
        output_path="../eis_files/train_dataset.json",
    )

    val_nodes = await load_corpus(VAL_FILES, verbose=True)
    val_dataset = generate_qa_embedding_pairs(
        val_nodes,
        llm=llm,
        qa_generate_prompt_tmpl=QA_GENERATE_PROMPT_TMPL,
        output_path="../eis_files/val_dataset.json",
    )

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
    )

    finetune_engine.finetune(resume_from_checkpoint=True, save_checkpoints=True)

    finetuned_embedding_model = finetune_engine.get_finetuned_model()

    print(finetuned_embedding_model.to_json())

    acc1 = evaluate_st(val_dataset, embedding_conf["embeddingmodel"], name="original")
    acc2 = evaluate_st(val_dataset, embedding_conf["fine_tuned_path"], name="finetuned")

    print(
        f"Original model {embedding_conf['embeddingmodel']}: {str(acc1)}\nFine-tuned model {embedding_conf['fine_tuned']}: {str(acc2)}"
    )


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
        epochs=4,  # Number of Epochs to train for
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


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(train_only())
