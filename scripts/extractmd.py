import os
import sys
import mimetypes
import re
import pymupdf4llm
from io import BytesIO
import mammoth
from markdownify import markdownify as md
import docx2txt
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

class Extractor:

    def fromPdfText2mdText(self,filetxt):

        filetxt = re.sub(r"^ *\d+ *\r?\n", "", filetxt) # page numbers
        filetxt = re.sub(r"\n *\d+ *\r?\n ", "\n", filetxt) # page numbers
        filetxt = re.sub(r"([a-zāēīūķļņčžšģ,\d] *)(\r?\n)+ ?([a-zāēīūķļņčžšģ\(]{2,})", r"\1 \3", filetxt) #line divided, merge it
        filetxt = re.sub(r"([‒-])\r?\n", r"\1", filetxt) #hyphen at the end or line, merge with the next line
        filetxt = re.sub(r"(\([^\n\(\)]+)\r?\n([^\n\)\(]+\))", r"\1\2", filetxt) # line divided '(' on first line, merge it
        filetxt = re.sub(r"([„“][^\n„“”]+)\r?\n([^\n„“”]+”)", r"\1\2", filetxt) # line divided '„' on first line, merge it
        while re.search(r"^\s*([A-ZĀĒĪŪĶĻŅČŽŠĢ,“”][A-Z ĀĒĪŪĶĻŅČŽŠĢ,\.“”\d]+\s*)(\r?\n\s*)+([A-ZĀĒĪŪĶĻŅČŽŠĢ,“”][A-Z ĀĒĪŪĶĻŅČŽŠĢ,\.“”\d]+\s*)\r?\n", filetxt):
            filetxt = re.sub(r"^\s*([A-ZĀĒĪŪĶĻŅČŽŠĢ,“”][A-Z ĀĒĪŪĶĻŅČŽŠĢ,\.“”\d]+\s*)(\r?\n\s*)+([A-ZĀĒĪŪĶĻŅČŽŠĢ,“”][A-Z ĀĒĪŪĶĻŅČŽŠĢ,\.“”\d]+\s*)\r?\n", r"# \1 \3\n", filetxt) # broken first line
        filetxt = re.sub(r"^\s*([A-ZĀĒĪŪĶĻŅČŽŠĢ,“”][A-Z ĀĒĪŪĶĻŅČŽŠĢ,\.“”\d]+)\s*\r?\n", r"# \1\n\n", filetxt, 1) # title
        filetxt = re.sub(r"\n\s*(\d+\. *[A-ZĀĒĪŪĶĻŅČŽŠĢ][\w“” ,\-]+)\s*\r?\n *(\([^\(\)\n]+\))( *\r?\n)?", r"\n\1 \2\n", filetxt) # broken line with (..) on second line
        while re.search(r"\r?\n( *([a-zāēīūķļņčžšģA-ZĀĒĪŪĶĻŅČŽŠĢ]|k\.|un) *\r?\n)", filetxt):
            filetxt = re.sub(r"\r?\n( *([a-zāēīūķļņčžšģA-ZĀĒĪŪĶĻŅČŽŠĢ]|k\.|un) *\r?\n)", r"\1", filetxt) # single letter in line, merge with previouse
        filetxt = re.sub(r"[,] *\r?\n(ka|kā|bet|vai|kas|kur|cik) ", r", \1 ", filetxt) # broken sentence
        filetxt = re.sub(r" *(\x7F|▪||•|●|•) ?", r"\n* ", filetxt) # bullet missing, inserting *
        filetxt = re.sub(r"\n\- ", "\n\t- ", filetxt) # second level list
        filetxt = re.sub(r"\no ", "\n\t\t- ", filetxt) # third level list
        filetxt = re.sub(r"([;:\.]) *\r?\n *([^\n])", r"\1\n\n\2", filetxt) # inserting empty line after bulleted line
        filetxt = re.sub(r"[:;] ([a-z1-9]\))", r";\n\n\1", filetxt) # bullet point a) 1) on same line
        filetxt = re.sub(r" (1[\)]) ?([^\n,;]+[;,])", r"\n\n\1 \2", filetxt) # inserting empty lines befor the first bulleted line
        filetxt = re.sub(r"\b(\d+[\)]) ?([^\n,\.]+[,\.])", r"\1 \2\n\n", filetxt) # inserting empty lines after bulleted line
        filetxt = re.sub(r";\n\s+([\w ]+[;.]\r?\n)", r";\n\n* \1", filetxt) # bullet missing, inserting *
        filetxt = re.sub(r"(\n[\*a-z\d]+[\.\)][^\n]+[^;\.]) *\r?\n(\w[\w ]+[;\.:])\r?\n", r"\1 \2\n", filetxt) # bulleted line divided, merge it
        filetxt = re.sub(r"(/| )w ?w ?w ?\.", r"\1www.", filetxt) # extra space in link
        filetxt = re.sub(r"(\.[\. ]+\. *\d+) *\r?\n", r"\1\n\n", filetxt) # empty line after TOC items
        filetxt = re.sub(r"\n\s+(\*)", r"\n\1", filetxt) #removing extra space before bullet
        filetxt = re.sub(r"((Atsauces|References|Satura rādītājs|Saturs) *\r?\n)", r"\1\n", filetxt)
        filetxt = re.sub(r"(\n[\*a-z\d]+[\.\)][^\n]+[;\.] *\r?\n) *([A-ZĀĒĪŪĶĻŅČŽŠĢ])", r"\1\n\2", filetxt) # inserting empty line after bulleted line
        filetxt = re.sub(r"([a-zāēīū''kļņčžšģ]\.) +([A-ZĀĒĪŪĶĻŅČŽŠĢ][a-zāēīū''kļņčžšģ ]+ [–-] )", r"\1\n\n\2", filetxt) # term list, insert newline 'ssdf. Asdfsdf - ' 
        filetxt = re.sub(r"([a-zāēīū''kļņčžšģ]\.) +(\d+\. [A-ZĀĒĪŪĶĻŅČŽŠĢ]+)", r"\1\n\n\2", filetxt) # new title, insert newline 'ssdf. 2. ASASF'     
        filetxt = re.sub(r" ([a-zāēīū]+)([A-ZĀĒĪŪĶĻŅČŽŠĢ]+)", r" \1 \2", filetxt) # words togeather 'izglītībaAIC'  
        filetxt = re.sub(r"([A-ZĀĒĪŪĶĻŅČŽŠĢ]+)\*\*([ĀĒĪŪĶĻŅČŽŠĢ]+)\*\*([A-ZĀĒĪŪĶĻŅČŽŠĢ]+)", r" \1\2\3", filetxt) # diacritic letters in ** ** 'APDROŠIN**Ā**T**Ā**JS' 
        filetxt = re.sub(r"\n-----\n", r"", filetxt)
        
        while re.search(r"( *\r\n *\r\n)( *\r\n *\r\n)+", filetxt):
            filetxt = re.sub(r"( *\r\n *\r\n)( *\r\n *\r\n)+", r"\1", filetxt)
            
        filetxt = re.sub(r"(\r?\n)([^\n]+\r?\n)[=]+ *\n", r"\1# \2\n\n", filetxt)
        filetxt = re.sub(r"(\r?\n)\*\*(\d+\.)(\*\*)? *(\*\*)?([^\n]+)\*\*(\r?\n)", r"\1\1## \2 \5\6\6", filetxt) 
        return filetxt
    
    def usePymupdf4llm(self,file_path):
        try:
            result = pymupdf4llm.to_markdown(file_path)
            result = re.sub(r'(\r?\n)+\#\s\d+(\r?\n)+(---+(\r?\n)+)?',r'\n\n',result)
            
            return self.fromPdfText2mdText(result)
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
    
                #placeholder = f"<figure>![](figures/{i})</figure>"
                updated_content = updated_content.replace(match.group(0), '', 1)
            updated_content = re.sub(r"\n\*\*([IVX]+ NODAĻA)\*\*(\r?\n)", r"\n## \1 \2", updated_content) 
            updated_content = re.sub(r"\n(\d+\.) \*\*([^*]+)\*\*(\r?\n)", r"\n### \1 \2 \3", updated_content) 
          
            return self.fromPdfText2mdText(updated_content)  
        except Exception as error:
            print(f"An exception occurred: {type(error).__name__} {error.args[0]}")
            return ''

    def useMammoth(self,file_path):
        try:
            with open(file_path, 'rb') as myfile:
                binarycontent = myfile.read()
                    
            result = mammoth.convert_to_html(BytesIO(binarycontent))
            htmlstr = result.value
                                           
            return htmlstr  
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

    def useDocx2txt(self, file_path):
        try:
            doc = docx2txt.process(file_path)
            return doc
        except:
            return ''

    def useMarkerPDF(self, file_path):
        try:
            converter = PdfConverter(artifact_dict=create_model_dict(),)
            rendered = converter(file_path)
            text, _, images = text_from_rendered(rendered)
            return text
        except:
            return ''
            
    def convert2markdown(self,file_path):
    
        if re.match(r".+\.pdf$", file_path):
            #return(self.usePymupdf4llm(file_path))    
            return(self.useMarkerPDF(file_path))   
        elif re.match(r".+\.docx$", file_path):
            return(self.useMammothMarkdownify(file_path))
            #return(self.useDocx2txt(file_path))
        elif re.match(r".+\.html$", file_path):
            return(self.useMarkdownify(file_path))
        elif re.match(r".+\.(txt|md|csv)$", file_path):
            return(self.useTxtFileReader(file_path))
        else:
            return("Not supported")

    def convert2html(self,file_path):
    
        if re.match(r".+\.docx$", file_path):
            return(self.useMammoth(file_path))
        else:
            return("Not supported")

