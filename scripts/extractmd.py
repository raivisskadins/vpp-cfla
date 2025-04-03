import os
import sys
import mimetypes
import re
import pymupdf4llm
from io import BytesIO
import mammoth
from markdownify import markdownify as md

class Extractor:
    
    def usePymupdf4llm(self,file_path):
        try:
            return pymupdf4llm.to_markdown(file_path)
        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return ''
            
           
    def useMammothMarkdownify(self,file_path):
        try:
            with open(file_path, 'rb') as myfile:
                binarycontent = myfile.read()
                    
            result = mammoth.convert_to_html(BytesIO(binarycontent))
            htmlstr = result.value
                
            markdown_content = md(result.value) 
                
            image_pattern = re.compile(r'!\[\]\(data:image/(\w+);base64,([a-zA-Z0-9+/=]+)\)')
    
            updated_content = markdown_content
    
            for i, match in enumerate(image_pattern.finditer(markdown_content)):
    
                placeholder = f"<figure>![](figures/{i})</figure>"
                updated_content = updated_content.replace(match.group(0), placeholder, 1)
                            
            return updated_content  
        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return ''
    
    def useMarkdownify(self,file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as myfile:
                filecontent = myfile.read()
                
            markdown_content = md(filecontent) 
                
            image_pattern = re.compile(r'!\[\]\(data:image/(\w+);base64,([a-zA-Z0-9+/=]+)\)')
    
            updated_content = markdown_content
    
            for i, match in enumerate(image_pattern.finditer(markdown_content)):
    
                placeholder = f"<figure>![](figures/{i})</figure>"
                updated_content = updated_content.replace(match.group(0), placeholder, 1)
                
            updated_content=re.sub(r"(\n\r?\n\r?)(\n\r?)+", r"\1", updated_content)
            
            return updated_content  
        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return ''
    
    def useTxtFileReader(self,file_path):
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        return content
             
    def convert2markdown(self,file_path):
    
        if re.match(r".+\.pdf$", file_path):
            return(self.usePymupdf4llm(file_path))                                    
        elif re.match(r".+\.docx$", file_path):
            return(self.useMammothMarkdownify(file_path))
        elif re.match(r".+\.html$", file_path):
            return(self.useMarkdownify(file_path))
        elif re.match(r".+\.(txt|md|csv)$", file_path):
            return(self.useTxtFileReader(file_path))
        else:
            return("Not supported")

