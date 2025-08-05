from fastapi import FastAPI, File, UploadFile, Query, Form
from fastapi.responses import JSONResponse
#from scripts import main_script
import shutil, os, json, re
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from scripts.main_script import main_script

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/app/procurements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process_procurement")
async def process_procurement(Proc_ID: str = Form(...), procurement_file: UploadFile = File(...), agreement_file: UploadFile = File(None)): 
    print("Process procurement start")
    # Create or recreate new procurement directory
    procurement_dir = os.path.join(UPLOAD_DIR, Proc_ID)
    if os.path.exists(procurement_dir):
        shutil.rmtree(procurement_dir)
    os.makedirs(procurement_dir)

    # Upload procurement file
    proc_file_path = os.path.join(procurement_dir, procurement_file.filename)
    with open(proc_file_path, "wb") as buffer:
        shutil.copyfileobj(procurement_file.file, buffer)

    # Upload agreement file
    agreement_file_path = None
    if agreement_file:
        agreement_file_path = os.path.join(procurement_dir, agreement_file.filename)
        with open(agreement_file_path, "wb") as buffer:
            shutil.copyfileobj(agreement_file.file, buffer)

    print("main script start")
    proc_report_csv_path = os.path.join(procurement_dir, "report.csv")
    await main_script(proc_file_path, agreement_file_path, proc_report_csv_path, Proc_ID) # this generates a csv file; Make sure it's in the same procurement directory; 
    return {"proc_report_path": proc_report_csv_path} # Get procurement csv file path 

@app.get("/get_csv_info")
async def get_csv_info(proc_report_path: str = Query(...)):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    proc_report_path = os.path.join(base_dir, "procurements/", proc_report_path)

    if not os.path.isfile(proc_report_path):
        print("File still being created")
        return

    df = pd.read_csv(proc_report_path, keep_default_na=False, encoding="utf-8")
    output = []

    for _, row in df.iterrows():
        # Extracting Pamatojums, get only the explanation key
        raw_text = row["Pamatojums"]
        cleaned = re.sub(r'```json\s*|```', '', raw_text).strip()
        cleaned = cleaned.replace('""', '"')
        try:
            data = json.loads(cleaned)
            explanation = data.get("explanation", "")
        except json.JSONDecodeError:
            explanation = "Nav pamatojuma"

        output.append({
            "Nr": row["Nr"],
            "Atbilde": row["Atbilde"],
            "Pamatojums": explanation
        })

    return JSONResponse(content=output)

    
