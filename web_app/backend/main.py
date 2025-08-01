from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import JSONResponse
#from scripts import main_script
import shutil, os, json, re
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

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
async def get_csv_info(proc_report_path: str = Query(...)):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    proc_report_path = os.path.join(base_dir, "procurements/", proc_report_path)

    if not os.path.isfile(proc_report_path):
        raise FileNotFoundError(f"Fails {proc_report_path} nav atrasts")

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

    