import re
import os
import json
import yaml
import urllib.parse
import configparser
from pathlib import Path
from llama_index.readers.web import ReadabilityWebPageReader
from llama_index.core import Document
import pandas as pd
import asyncio

def get_extra_info(singleq, pilchapters, mk107chapters, nslchapters, mki3chapters):
    
    piltxtlist = []
    mk107txtlist = []
    nsltxtlist = []
    mki3txtlist = []
    extrainfo = ''
    
    if 'PIL' in singleq:
        
        for item in singleq['PIL']:
            
            if 'chapter' in item:
                chaptertxt = pilchapters[f"{item['chapter']}. pants"]
                piltxtlist.append(f"{item['chapter']}. pants.\n")
                if 'pt' in item:
                    pointstxt = ''
                    
                    for ptitem in item['pt']:
                        pattern = re.compile(rf'^\({ptitem}\)\s.*?(?=^\(\d\)\s|\Z)', re.DOTALL | re.MULTILINE)
                        match = pattern.search(chaptertxt)

                        if match:
                            pointstxt += match.group(0)
                        else:
                            break
                            
                    if len(pointstxt) > 0:
                       chaptertxt = pointstxt
                    
                piltxtlist.append(chaptertxt)
                
            elif 'appendix' in item:
                piltxtlist.append(pilchapters[f"{item['appendix']}. pielikums"])
                
    if 'MK107' in singleq:
        
        for item in singleq['MK107']:
            
            if 'chapter' in item:
                chaptertxt = mk107chapters[f"{item['chapter']}"]
                
                if 'pt' in item:
                    pointslist = chaptertxt.split('\n')
                    pointstxt = ''
                    
                    for ptitem in item['pt']:
                        for point in pointslist:
                            if point.find(f"{item['chapter']}.{ptitem}.") == 0:
                                pointstxt += point
                                break
                            
                    chaptertxt = f"\n{pointslist[0]} {pointstxt}"
                    
                mk107txtlist.append(chaptertxt)
    if 'MKI3' in singleq:
        
        for item in singleq['MKI3']:
            
            if 'chapter' in item:
                chaptertxt = mki3chapters[f"{item['chapter']}"]
                
                if 'pt' in item:
                    pointslist = chaptertxt.split('\n')
                    pointstxt = ''
                    
                    for ptitem in item['pt']:
                        for point in pointslist:
                            if point.find(f"{item['chapter']}.{ptitem}.") == 0:
                                pointstxt += point
                                break
                            
                    chaptertxt = f"\n{pointslist[0]} {pointstxt}"
                    
                mki3txtlist.append(chaptertxt)
    if 'NSL' in singleq:
        
        for item in singleq['NSL']:
            
            if 'chapter' in item:
                chaptertxt = nslchapters[f"{item['chapter']} pants"]
                
                if 'pt' in item:
                    pointstxt = ''
                    
                    for ptitem in item['pt']:
                        pattern = re.compile(rf'^\({ptitem}\)\s.*?(?=^\(\d\)\s|\Z)', re.DOTALL | re.MULTILINE)
                        match = pattern.search(chaptertxt)

                        if match:
                            pointstxt += match.group(0)
                        else:
                            break
                            
                    if len(pointstxt) > 0:
                       chaptertxt = pointstxt
                    
                nsltxtlist.append(chaptertxt)
                
    if len(piltxtlist) > 0:
        extrainfo += 'PIL\n' + ';\n'.join(piltxtlist) + '\n'
    if len(mk107txtlist) > 0:
        extrainfo += 'MK107\n' + ';\n'.join(mk107txtlist).replace(';;',';') + '\n'
    if len(mki3txtlist) > 0:
        extrainfo += 'MK instrukcija Nr. 3\n' + ';\n'.join(mki3txtlist).replace(';;',';') + '\n'
    if len(nsltxtlist) > 0:
        extrainfo += 'Nacionālo Sankciju Likums\n' + ';\n'.join(nsltxtlist) + '\n'
        
    if len(extrainfo) > 0:
        extrainfo = f"Izvilkumi no likumiem ietverti <law> tagos: \n<law>{extrainfo}</law>"
        
    return extrainfo
    
def extract_chapters(text, pattern):
    chapter_pattern = re.compile(pattern, re.MULTILINE)
    
    chapters = {}
    matches = list(chapter_pattern.finditer(text))
    
    for i, match in enumerate(matches):
        key = match.group('key')
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_content = text[start:end]
        chapter_content = re.sub(r'\(MK [^\)]+ redakcijā\);?',r'',chapter_content,re.DOTALL) #(MK 08.11.2022. noteikumu Nr. 691 redakcijā)
        chapter_content = re.sub(r'\(Ar grozījumiem, kas izdarīti[^\)]+\);?',r'',chapter_content,re.DOTALL) #(Ar grozījumiem, kas izdarīti ar 26.04.2018. likumu, kas stājas spēkā 01.06.2018.)
        chapters[key] = chapter_content.strip()

    return(chapters)

def encode_url_file_name(url):
    filename=os.path.basename(url)
    encodedfilename=urllib.parse.quote(filename)
    newurl=url.replace(filename,encodedfilename)
    return(newurl)
    
async def text_from_url(url):
    
    try:
        loader = ReadabilityWebPageReader()
        loop = asyncio.get_event_loop()
        documents = loop.run_until_complete(loader.async_load_data(url=encode_url_file_name(url)))
        print(documents[0])
        return(documents)
    except Exception as error:
        print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
        return([Document(text="404: Not Found")])

def ask_question_save_answer(qnaengine, embedding_conf, prompt, question, nr, expectedanswer=''):
    result = qnaengine.askQuestion(prompt, 
                                   question, 
                                   usecontext=embedding_conf["use_similar_chunks"],
                                   n=embedding_conf["top_similar"],
                                   n4rerank=embedding_conf["n4rerank"],
                                   prevnext=embedding_conf["prevnext"])
    if result == "": # handeling case when result returns an exception
        query = ""
        record = [nr, 'Modelis neatgrieza atbildi', expectedanswer, result] 
        return query, record    
    
    query = result["query"]
    result = re.sub(r'\n\n+',r'\n',result["result"]).strip()

    answer = re.search(r'\{[^\{\}]+\}',result, re.IGNORECASE)
    if answer:
        try:
            jsonanswer=json.loads(answer.group(0))
            llmanswer = jsonanswer.get('answer','')
            record = [nr, llmanswer, expectedanswer, result]
            return query, record
        except:
            pass
            
    answer = re.search(r'\[\**(jā|nē|kontekstā nav informācijas|n/a)\**\]',result, re.IGNORECASE)
    
    if answer:
        llmanswer=answer.group(1)
        #result = result.replace(f"[{llmanswer}]","").replace(f"Atbilde:","")
        record = [nr, llmanswer, expectedanswer, result]
    else:
        answer = re.search(r"'?(jā|nē|kontekstā nav informācijas|n/a)'?", result, re.IGNORECASE)
        if not answer:
            answer = re.search(r'\[(ja|ne)\]', result, re.IGNORECASE)
        if answer:
            record = [nr, answer.group(1).lower(), expectedanswer, result]
        else:
            record = [nr, '', expectedanswer, result] 
    return query, record

# TODO needs a more logical name, more info seems to be similar
def get_supplementary_info():
    # Determine the directory containing this script, then go up one level to find 'supplementary_info'
    base_dir = Path(__file__).parent.parent / 'supplementary_info'

    pil_path = base_dir / 'PIL.txt'
    with open(pil_path, 'r', encoding='utf-8') as file:
        piltxt = file.read().strip()
    pattern = r'^(?P<key>(\d+\.\s+(pants|pielikums))|Pārejas noteikumi)'
    pilchapters = extract_chapters(piltxt, pattern)

    mk107_path = base_dir / 'MK107.md'
    with open(mk107_path, 'r', encoding='utf-8') as file:
        mk107txt = file.read().strip()
    pattern = r'^(?P<key>[# ]*\d+)\.\s+'
    mk107chapters = extract_chapters(mk107txt, pattern)

    nsl_path = base_dir / 'S_LR_NSL.txt'
    with open(nsl_path, 'r', encoding='utf-8') as file:
        nsltxt = file.read().strip()
    pattern = r'^(?P<key>(\d+\.(\d+)?\s+pants))'
    nslchapters = extract_chapters(nsltxt, pattern)

    mki3_path = base_dir / 'MK_I3.txt'
    with open(mki3_path, 'r', encoding='utf-8') as file:
        mki3txt = file.read().strip()
    pattern = r'^\*\* (?P<key>\d+(\.\d+)?)\.\s+'
    mki3chapters = extract_chapters(mki3txt, pattern)

    return pilchapters, mk107chapters, nslchapters, mki3chapters

def get_prompt_dict(prompt_file, question_dict):
    try:
        with open(prompt_file, 'r', encoding='utf-8') as file:
            prompts_loaded = yaml.load(file, Loader=yaml.BaseLoader)
            print("Prompts loaded")
    except FileNotFoundError:
        print(f"Error: File '{prompt_file}' not found.")
        exit
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        exit
    
    promptdict = {}

    # Map id's to prompts directly
    prompt_dict_by_id = {}
    for prompt in prompts_loaded:
        prompt_dict_by_id[prompt["id"]] = prompt["prompt"]
        # Also get default prompt
        if prompt.get("default"):
            promptdict["0"] = prompt["prompt"]

    for question in question_dict:
        if "questions" in question:
            for subquestion in question.get("questions"):
                if "prompt-id" in subquestion:
                    promptdict[subquestion["nr"]] = prompt_dict_by_id[subquestion["prompt-id"]]
                if "prompt0-id" in subquestion:
                    promptdict[subquestion["nr"]+"-0"] = prompt_dict_by_id[subquestion["prompt0-id"]]
        else:
            if "prompt-id" in question:
                promptdict[question["nr"]] = prompt_dict_by_id[question["prompt-id"]]
            if "prompt0-id" in question:
                promptdict[question["nr"]+"-0"] = prompt_dict_by_id[question["prompt0-id"]]

    return promptdict

def get_questions(question_file_path):
    try:
        with open(question_file_path, 'r', encoding='utf-8') as file:
            question_dictonary = yaml.load(file, Loader=yaml.BaseLoader)
            print("Questions loaded")
    except FileNotFoundError:
        print(f"Error: File '{question_file_path}' not found.")
        exit
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        exit
    return question_dictonary

def get_answers(answer_file_path):
    try:
        with open(answer_file_path, 'r', encoding='utf-8') as file:
            answer_dictonary = yaml.load(file, Loader=yaml.BaseLoader)
    except FileNotFoundError:
        print(f"Error: File '{answer_file_path}' not found.")
        exit
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        exit
    return answer_dictonary

def get_config_data(configfile, procurement_file_dir, answer_file_dir):
    config = configparser.ConfigParser()
    config.read(configfile,encoding='utf-8')
    # EIS_URL = config.get('Procurement', 'EIS_URL')
    procurement_id = config.get('Procurement', 'procurement_id')
    procurement_file_name = config.get('Procurement', 'procurement_file_name')
    answer_file_name = config.get('Procurement', 'answer_file_name')
    procurement_file = str(procurement_file_dir / procurement_file_name)
    answer_file = str(answer_file_dir / answer_file_name)

    if 'agreement_file_name' in config['Procurement']:
        agreement_file_name = (config.get('Procurement', 'agreement_file_name'))
        agreement_file = str(procurement_file_dir / agreement_file_name)
    else:
        agreement_file = ''

    return procurement_id, procurement_file, agreement_file, answer_file

def get_procurement_content(extractor, procurement_file_path, agreement_file_path):
    print(f"Processing file: {procurement_file_path}")
    procurement_content = extractor.convert2markdown(procurement_file_path)
    if len(agreement_file_path) > 0: # If agreement file was added
        print(f"Processing file: {agreement_file_path}")
        agreement_content = extractor.convert2markdown(agreement_file_path)
        procurement_content = procurement_content + "\n\n# IEPIRKUMA LĪGUMA PROJEKTS\n\n" + agreement_content
        with open("tmp3.md", 'w', encoding='utf-8') as fout:
            print(procurement_content,file=fout)

    return procurement_content

def get_ini_files(config_dir, overwrite, report_path_csv):
    # Getting a list of ini files from a directory without extension
    # If we are not overwritting we don't append already existing data to the report
    ini_files = {p.stem for p in Path(config_dir).glob("*.ini")}
    print(f"Found {len(ini_files)} config files in {config_dir}")
    if not overwrite and report_path_csv.exists():
        existing = pd.read_csv(report_path_csv, usecols=["Iepirkuma ID"], dtype=str)
        done_ids = set(existing["Iepirkuma ID"].unique())
        remaining = ini_files - done_ids
        skipped = ini_files & done_ids
        print(f"Skipping {len(skipped)} already-processed files: {sorted(skipped)}")
        ini_files = remaining
    return sorted(ini_files)

def get_questions_without_q0(questions):
    # This function returns a list of nr's for questions that potentially cannot be answered; I.e. expected answer = "n/a", but LLM can't give such an answer
    # There are a few propmts that however do allow it, so the filter is a little bit more complicated
    
    questions_wout_0q = []

    for q in questions:
        if 'allows_na' in q:
            continue

        # If "question0" is not present, add this question's number
        if 'question0' not in q:
            if 'nr' in q:
                questions_wout_0q.append(q['nr'])

        # If it has nested questions, recurse into them
        if 'questions' in q and 'question0' not in q:
            nested = get_questions_without_q0(q['questions'])
            questions_wout_0q.extend(nested)

    return questions_wout_0q