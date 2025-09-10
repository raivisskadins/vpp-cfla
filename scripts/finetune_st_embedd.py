# Copyright 2025 State Research Programme project
# "Analysis of the Applicability of Artificial Intelligence Methods in the
# Field of European Union Fund Projects" (Project number: VPP-CFLA-Artificial
# Intelligence-2024/1-0003). The project is implemented by the University of Latvia.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments,
    SentenceTransformerModelCardData,
    InputExample,
)
from transformers import EarlyStoppingCallback
from sentence_transformers.losses import MultipleNegativesRankingLoss
from sentence_transformers.training_args import BatchSamplers
from datasets import Dataset

import json
import asyncio
import random
import re

embedding_conf = {
    "embeddingmodel": "BAAI/bge-m3", 
    "fine_tuned": "bge-m3-procurements",
    "fine_tuned_path": "../bge-m3-procurements",
    "chunk_size": 1536,
    "chunk_overlap": 0,
}

def load_json_samples(filepath: str):

    examples = []
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
        
    for qid,query in data["queries"].items():

        if qid in data["relevant_docs"] and not re.search("[^\s]{50,}",query): #without binary data
            chunkid = data["relevant_docs"][qid][0]
            examples.append({"text1": query, "text2": data["corpus"][chunkid]})
            
    random.shuffle(examples)
    
    return (len(examples),Dataset.from_list(examples))

	(numeval,eval_dataset) = load_json_samples("../eis_files/val_dataset.json")
	(numtrain,train_dataset) = load_json_samples("../eis_files/train_dataset.json")
    
	model = SentenceTransformer(embedding_conf["embeddingmodel"])

	loss = MultipleNegativesRankingLoss(model)
	print(f"Warmup steps: {int((numtrain/3)*0.2)}")
	args = SentenceTransformerTrainingArguments(
		output_dir=embedding_conf["fine_tuned_path"],
		num_train_epochs=2,
		per_device_train_batch_size=3,
		per_device_eval_batch_size=3,
		learning_rate=9e-6,
        warmup_steps=int((numtrain/3)*0.2), #~28600, 10% of num steps (numsteps = (numsamples/batch) * epochs)
		fp16=True,  # Set to False if you get an error that your GPU can't run on FP16
		bf16=False,  # Set to True if you have a GPU that supports BF16
		batch_sampler=BatchSamplers.NO_DUPLICATES,  # MultipleNegativesRankingLoss benefits from no duplicate samples in a batch
		load_best_model_at_end=True, 
        auto_find_batch_size=True,
		eval_strategy="steps",
		eval_steps=100,
		save_strategy="steps",
		save_steps=100,
		save_total_limit=1,
		logging_steps=100,
		run_name="finetuned_bge_m3",  # Will be used in W&B if `wandb` is installed
	)

	trainer = SentenceTransformerTrainer(
		model=model,
		args=args,
		train_dataset=train_dataset,
		eval_dataset=eval_dataset,
		loss=loss,
	)

	trainer.add_callback(EarlyStoppingCallback(early_stopping_patience=10))

	trainer.train()

	model.save_pretrained(f"{embedding_conf['fine_tuned_path']}/final")

if __name__ == "__main__":
    asyncio.run(main())