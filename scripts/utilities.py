import re
import os
import urllib.parse
from llama_index.readers.web import ReadabilityWebPageReader
from llama_index.core import Document

import asyncio

def get_extra_info(singleq,pilchapters):
    
    piltxtlist = []
    extrainfo = ''
    
    if 'PIL' in singleq:
        
        for pilitem in singleq['PIL']:
            
            if 'chapter' in pilitem:
                chaptertxt = pilchapters[f"{pilitem['chapter']}. pants"]
                
                if 'pt' in pilitem:
                    pointstxt = ''
                    
                    for ptitem in pilitem['pt']:
                        pattern = re.compile(rf'^\({ptitem}\)\s.*?(?=^\(\d\)\s|\Z)', re.DOTALL | re.MULTILINE)
                        match = pattern.search(chaptertxt)

                        if match:
                            pointstxt += match.group(0)
                        else:
                            break
                            
                    if len(pointstxt) > 0:
                       chaptertxt = pointstxt
                    
                piltxtlist.append(chaptertxt)
                
            elif 'appendix' in pilitem:
                piltxtlist.append(pilchapters[f"{pilitem['appendix']}. pielikums"])
    
    if len(piltxtlist) > 0:
        extrainfo = 'Papildu informācija atbildes ģenerēšanai: PIL ' + ';'.join(piltxtlist) + '\n'
        
    return extrainfo
    
def extract_chapters(text, pattern):
    chapter_pattern = re.compile(pattern, re.MULTILINE)
    
    chapters = {}
    matches = list(chapter_pattern.finditer(text))
    
    for i, match in enumerate(matches):
        key = match.group('key')
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_content = text[start:end].strip()
        chapters[key] = chapter_content

    return(chapters)

def encodeUrlFileName(url):
    filename=os.path.basename(url)
    encodedfilename=urllib.parse.quote(filename)
    newurl=url.replace(filename,encodedfilename)
    return(newurl)
    
async def text_from_url(url):
    
    try:
        loader = ReadabilityWebPageReader()
        loop = asyncio.get_event_loop()
        documents = loop.run_until_complete(loader.async_load_data(url=encodeUrlFileName(url)))
        print(documents[0])
        return(documents)
    except Exception as error:
        print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
        return([Document(text="404: Not Found")]) 