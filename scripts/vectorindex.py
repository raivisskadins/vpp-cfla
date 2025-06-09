import os
import sys
import mimetypes
import re
from typing import Any, List
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import openai
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import  VectorStoreIndex, StorageContext, Document, Settings
from llama_index.core.schema import TextNode, MetadataMode, NodeWithScore
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.prompts import PromptTemplate
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.query_engine import CustomQueryEngine, RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer,BaseSynthesizer

from llama_index.core.llms.llm import LLM
from llama_index.core.utilities.token_counting import TokenCounter
from tqdm import tqdm
import json
from FlagEmbedding import FlagReranker

import nest_asyncio
nest_asyncio.apply()

text_qa_template_str = """Konteksta informācija ietverta <context> tagos:
<context>
{context_str}
</context>

Lietotāja apgalvojums vai jautājums ir šāds:
{query_str}"""

mddict={"#":"H1", "##":"H2", "###":"H3"}

class QnAEngine:
    
    def __init__(self, embedding: HuggingFaceEmbedding, llm: LLM):
        self.embeddingobject = embedding
        dim = len(self.embeddingobject._get_text_embedding("Test string"))
        faiss_index = faiss.IndexFlatL2(dim)
        self.vector_store = FaissVectorStore(faiss_index=faiss_index)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.newindex = None
        self.llm = llm
        Settings.llm = self.llm   #default language model for all functions
        Settings.embed_model = self.embeddingobject
        self.chached_responses = {}
        self._token_counter = TokenCounter()
        self.token_limit = self.llm.metadata.context_window * 0.5
        self.compressed_txt = {}
        self.alltext = ""
        self.reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
            
    def load_md(self,text) -> List[Document]:
        docs = []

        try:
            alllines=text.split('\n')
            segmentlines=[]
            metalist = {}
            othermeta = {}
  
            for start_line, currline in enumerate(alllines):
                txt2add = '\n'.join(segmentlines)

                if len(currline.strip())>0:
                    found = re.search(rf"^(##?#?)([^#]+)$",currline)
                    if found and len(found.group(2).strip())>0:
                        if (len(segmentlines)>1 and len(segmentlines[0].strip())>0) or (mddict[found.group(1)] == "H2" and "H2" in metalist): 
                            #more than 1 line before or new H2 and previousely was H2
                           
                            if found.group(2).strip() != txt2add: #new chunk if not only title but other text as well
                                newmeta={**metalist, **othermeta}
                                docs.append(Document(text=txt2add, extra_info=newmeta))
                                segmentlines.clear()    
                                
                        if mddict[found.group(1)] == "H1":
                            metalist.pop("H2", None)
                            metalist.pop("H3", None)
                        elif mddict[found.group(1)] == "H2":
                            metalist.pop("H3", None)

                        segmentlines.append(found.group(2).strip()) 
                        metalist[mddict[found.group(1)]]=found.group(2).strip()

                    elif re.search(rf"^####\s*$",currline): #chunk beak - line with 4 '#'

                        if len(txt2add) > 0:
                            newmeta={**metalist, **othermeta}
                            docs.append(Document(text=txt2add, extra_info=newmeta))
                            segmentlines.clear()
                            
                    elif re.search(rf"^####[^#]",currline):
                        found = re.search(rf"^ *([^\s:\[]+):(.+)$",currline[4:])

                        if found:
                            if found.group(1) in othermeta and len(txt2add)>0:  #new value for existing tag
                                if found.group(1) != "pg":
                                    newmeta={**metalist, **othermeta}
                                    docs.append(Document(text=txt2add, extra_info=newmeta))
                                    segmentlines.clear()
                                    othermeta[found.group(1)]=found.group(2).strip()
                                else:
                                    othermeta[found.group(1)]=found.group(2).strip()
                            else:
                                othermeta[found.group(1)]=found.group(2).strip()
                        else:
                            if len(txt2add) > 0:
                                newmeta={**metalist, **othermeta}
                                docs.append(Document(text=txt2add, extra_info=newmeta))
                                segmentlines.clear()
                            segmentlines.append(currline[4:])                                            
                    #elif len(txt2add)>1000 and (currline.strip().endswith(":") or currline.strip().endswith("?")) and currline[0].isupper():
                    #    newmeta={**metalist, **othermeta}
                    #    docs.append(Document(text=txt2add, extra_info=newmeta))
                    #    segmentlines.clear()
                    #    segmentlines.append(currline)
                    else:
                        found = re.search(rf"^\*\*(\d+\.)(\d+\.)?\*\* \*\*([^*\n]+)\*\*$",currline)
                        if found:
                            if found.group(2):
                                title = "H2"
                            else:
                                title = "H1"
                             
                            if (len(segmentlines)>1 and len(segmentlines[0].strip())>0) or (title == "H2" and "H2" in metalist): 
                                #more than 1 line before or new H2 and previousely was H2
                             
                                newmeta={**metalist, **othermeta}
                                docs.append(Document(text=txt2add, extra_info=newmeta))
                                segmentlines.clear()    
                                    
                            if title == "H1":
                                metalist.pop("H2", None)
                                metalist.pop("H3", None)
                                segmentlines.append(f"# {found.group(1)} {found.group(3)}") 
                                metalist[title]=f"{found.group(1)} {found.group(3)}"
                            else:
                                metalist.pop("H3", None)
                                segmentlines.append(f"## {found.group(1)}{found.group(2)} {found.group(3)}") 
                                metalist[title]=f"{found.group(1)}{found.group(2)} {found.group(3)}"
                        else:
                            segmentlines.append(currline)
                
            if len(segmentlines)>1:
                newmeta={**metalist, **othermeta}
                docs.append(Document(text='\n\n'.join(segmentlines), extra_info=newmeta))
            elif len(segmentlines)==1:
                docs[-1].text = docs[-1].text + '\n' + segmentlines[0]
                
        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return docs
    
        return docs

    async def get_nodes(self,documents,filetype,chunk_size,chunk_overlap) -> List[TextNode]:

        #chunk size is in tokenizer's tokens not characters
        node_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, paragraph_separator='\n') 
        #Parse text with a preference for complete sentences

        alltexts = []
        allkeys = []
        nodes = []
        n = 0
        
        for doc in documents:
                    
            doc.text=doc.text.strip()

            if len(doc.text)>0:

                doc.extra_info['FileType']=filetype   
                currtext = doc.text.replace(r'\\n',r'\n')
                cur_text_chunks = node_parser.split_text(currtext)
                     
                for idx,chunk in enumerate(cur_text_chunks):
                    alltexts.append(chunk)
                    node = TextNode(text=chunk, metadata=doc.metadata)                        
                    node.metadata['ChunkNr']=str(n)

                    if n>0 and nodes[-1].metadata.get('H1','')==node.metadata.get('H1','') and nodes[-1].metadata.get('H2','')==node.metadata.get('H2','') and nodes[-1].metadata.get('H3','')==node.metadata.get('H3',''):
                        node.metadata['PrevNodeTxt']=nodes[-1].text
                        nodes[-1].metadata['NextNodeTxt']=chunk
                        
                    if 'excerpt' in node.metadata:
                        node.metadata.pop('excerpt')
                    n = n + 1 
                    allkeys = list(node.metadata.keys())
                    if 'H1' in allkeys:
                        allkeys.remove('H1')
                    if 'H2' in allkeys:
                        allkeys.remove('H2')
                    if 'H3' in allkeys:
                        allkeys.remove('H3')

                    node.excluded_llm_metadata_keys = allkeys 
                    node.excluded_embed_metadata_keys = list(node.metadata.keys()) 
                    nodes.append(node)
  
        cur_batch = []
        result_embeddings = []
        
        with tqdm(total=len(alltexts), desc="Generating embeddings", bar_format="{l_bar}{bar} [ time left: {remaining} ]") as pbar:
            for idx, txt in enumerate(alltexts):
                cur_batch.append(txt)
                pbar.update(1)
                if idx == len(alltexts) - 1 or len(cur_batch) == 10:
                    embeddings = await self.embeddingobject._aget_text_embeddings(cur_batch)
                    result_embeddings.extend(embeddings)
                    cur_batch.clear()
            
        for idx, node in enumerate(nodes):
            nodes[idx].embedding = result_embeddings[idx]

        print(f"{len(nodes)} segments created and vectorized.")
        return nodes    
    # TODO would be good if all functions had the same case snake or camel case for consitency             
    async def createIndex(self,file_content,filetype,chunk_size=1024,chunk_overlap=0):
        try:
            self.alltext = file_content
            documents = self.load_md(file_content)
            nodes = await self.get_nodes(documents,filetype,chunk_size,chunk_overlap)
            with open ("tmp2.md", 'w',encoding='utf-8') as ofile:
                for node in nodes:
                    print(f"ChunkNr:{node.metadata['ChunkNr']}\n{node.text}", file = ofile)
            self.newindex = VectorStoreIndex(nodes, show_progress=False, use_async=True, storage_context=self.storage_context, embed_model=self.embeddingobject)
            print("Index is ready.")
            return True
            
        except Exception as error:
            print("**Failed to create index!**")
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return False

    def compressPrompt(self,prompt,size):
        
        if prompt in self.compressed_txt:
            return self.compressed_txt[prompt]
        elif self._token_counter.estimate_tokens_in_messages([ChatMessage(content=prompt, role=MessageRole.SYSTEM)])  < size:
            return prompt
            
        response = self.llm.complete(f"The following text exceeds context window token limit. Summarize it so its size does not exceed {size} tokens. Do not translate the text. The text is the following:\n{prompt}\nThe summaized text: ")
        newprompt = str(response)
        newprompt = re.sub(r'The summarized text is( as follows)?:','',newprompt).strip()
        print(f"Old size:{len(prompt)} New size:{len(newprompt)}")
        print(f"NEW PROMPT:\n{newprompt}\n--------------")
        self.compressed_txt[prompt] = newprompt
        return newprompt
        
    def askQuestion(self,query_prompt,q,usecontext=True,n=4,n4rerank=0,prevnext=False):

        if (query_prompt,q) in self.chached_responses:
            return self.chached_responses[(query_prompt,q)]
            
        if usecontext==True:
            numitemsinidx=self.newindex.vector_store.client.ntotal
            
            if numitemsinidx < n:              
                n=numitemsinidx
                n4rerank=0
            try: 
                if n4rerank > 0:
                    nodelist = self.getRerankedNodes(q,n4rerank, n,prevnext) #[.., .., ..]
             
                else:
                    nodedict = self.getSimilarNodes(q,n,prevnext) #{"text":texts, "score":scores, "metadata":metadata}
                                     
                    nodelist = [fragment for fragment in nodedict['text']] #[.., .., ..]
                    
                newquery = PromptTemplate(query_prompt+'\n'+text_qa_template_str).format(context_str = '\n'.join(nodelist), query_str = q)
                    
                result = self.llm.complete(newquery)
                    
                self.chached_responses[(query_prompt,q)] = str(result)
                return(str(result))
                
            except openai.BadRequestError as e:
                print(f"Q: {q}")
                print(f"{e.code} {e.args[0]}")
                return ''
            except openai.APITimeoutError as e:
                print("Request timed out")
                return ''
            except openai.APIError as e:
                print("API error")
                return ''
            except openai.APIConnectionError as e:
                print("Open API connection error")
                return ''
            except openai.RateLimitError as e:
                print("Open API rate limit error")
                return ''
            except Exception as error:
                print(f"An exception in askQuestion: {type(error).__name__} {error.args[0]}")
                return ''
        else:
            try:
                fullquery = PromptTemplate(query_prompt+'\n'+text_qa_template_str).format(context_str = self.alltext, query_str = q)
                result = self.llm.complete(fullquery)
                self.chached_responses[(query_prompt,q)] = str(result)
                return(str(result))
                
            except Exception as error:
                print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
                return ''

    def getRerankedNodes(self,q,n4rerank, n, prevnext=False):

        similarnodes = self.getSimilarNodes(q,n4rerank) #{"text":texts, "score":scores, "metadata":metadata}

        to_rerank = [[q, fragment] for fragment in similarnodes['text']]                                 

        scores = self.reranker.compute_score(to_rerank, normalize=True) #higher scores are better

        sortedlist = sorted(zip(scores, to_rerank), key=lambda x: x[0], reverse=True)
        topnodes = [text[1] for _, text in sortedlist[:n]]

        return topnodes
        
    
    def getSimilarNodes(self,q,n=4,prevnext=False):

        numitemsinidx=self.newindex.vector_store.client.ntotal
        
        if numitemsinidx < n:              
            n=numitemsinidx
        try:
            retriever = self.newindex.as_retriever(similarity_top_k=n)   
            retrieved_nodes = retriever.retrieve(q)
            #result = []
            texts = []
            scores = []
            metadata = []

            for item in  retrieved_nodes:
                tmpdict={keys:values for keys, values in item.metadata.items() if values is not None}

                if prevnext==True:
                    if 'PrevNodeTxt' in tmpdict and tmpdict['PrevNodeTxt'] not in texts:
                        texts.append(tmpdict['PrevNodeTxt'])
                        scores.append(item.get_score()) #use same score as for the next chunk
                        newtmpdict = tmpdict.copy()
                        newtmpdict.pop('NextNodeTxt', None)
                        newtmpdict.pop('PrevNodeTxt', None)
                        newtmpdict['ChunkNr'] = str(int(tmpdict['ChunkNr'])-1)
                        metadata.append(newtmpdict)

                if item.get_content() not in texts:
                    texts.append(item.get_content())
                    scores.append(item.get_score())
                    metadata.append(tmpdict)

                if prevnext==True:
                    if 'NextNodeTxt' in tmpdict and tmpdict['NextNodeTxt'] not in texts:
                        texts.append(tmpdict['NextNodeTxt'])
                        scores.append(item.get_score()) #use same score as for the previouse chunk
                        newtmpdict = tmpdict.copy()
                        newtmpdict.pop('NextNodeTxt', None)
                        newtmpdict.pop('PrevNodeTxt', None)
                        newtmpdict['ChunkNr'] = str(int(tmpdict['ChunkNr'])+1)
                        metadata.append(newtmpdict)
                                     
                #result.append({"text": item.get_content(), "score": str(item.get_score()), "metadata": tmpdict})
                
            return ({"text":texts, "score":scores, "metadata":metadata})
            
        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return []   

        
    