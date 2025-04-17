import re
import os
import urllib.parse
from llama_index.readers.web import ReadabilityWebPageReader
from llama_index.core import Document

import asyncio

def get_extra_info(singleq, pilchapters, mk107chapters):
    
    piltxtlist = []
    mk107txtlist = []
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
                
    elif 'MK107' in singleq:
        
        for mk107item in singleq['MK107']:
            
            if 'chapter' in mk107item:
                chaptertxt = mk107chapters[f"{mk107item['chapter']}"]
                
                if 'pt' in mk107item:
                    pointslist = chaptertxt.split('\n')
                    pointstxt = ''
                    
                    for ptitem in mk107item['pt']:
                        for point in pointslist:
                            if point.find(f"{mk107item['chapter']}.{ptitem}.") == 0:
                                pointstxt += point
                                break
                            
                    chaptertxt = f"\n{pointslist[0]} {pointstxt}"
                    
                mk107txtlist.append(chaptertxt)
    
    if len(piltxtlist) > 0:
        extrainfo += 'PIL\n' + ';\n'.join(piltxtlist) + '\n'

    if len(mk107txtlist) > 0:
        extrainfo += 'MK107\n' + ';\n'.join(mk107txtlist).replace(';;',';') + '\n'

    if len(extrainfo) > 0:
        extrainfo = 'Likumdošanas prasības: \n' + extrainfo
        
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