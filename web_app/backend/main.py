from fastapi import FastAPI, File, UploadFile
import shutil
import os
from scripts import main_script

app = FastAPI()

UPLOAD_DIR = "/app/procurements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process_procurement")
async def process_procurement(Proc_ID, procurement_file: UploadFile = File(...), agreement_file: UploadFile = File(...)): 
    
    # Create new procurement directory
    procurement_dir = UPLOAD_DIR / Proc_ID
    os.makedirs(procurement_dir, exist_ok=True)

    # Upload procurement file
    file_path = os.path.join(procurement_dir, procurement_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(procurement_file.file, buffer)

    # Upload agreement file
    if agreement_file:
        # Upload agreement file
        return
    
    # main_script(procurement_file, agreement_file) # this generates a csv file; Make sure it's in the same procurement directory; 
    
    return {"proc_report_path": procurement_dir / "report.csv"} # Get procurement csv file path 

@app.get("/get_csv_info")
async def get_csv_info(proc_report_path):
    
    # Read in the report csv file

    # df = pd.read_csv(proc_report_path, keep_default_na=False, encoding="utf-8")
    
    # turn csv into json list of objects

    # List of objects like these:
    #     {
    #     "Nr": "8",
    #     "Atbilde": "nē",
    #     "Pamatojums": "Nezinu"
    # }

    # when extracting Pamatojums, get only the explanation key
    #     {
    #   ""answer"": ""jā"",
    #   ""rate"": ""augsta"",
    #   ""explanation"": ""Kontekstā ir norādīts, ka iepirkuma priekšmets nav sadalīts daļās. Iepirkuma priekšmets netiek dalīts daļās, jo ir viens pretendentu loks; viens būvobjekts; viens būvdarbu veikšanas laiks būvobjektā.""
    # }
    
    # procurement_data = df.json
    # return procurement_data