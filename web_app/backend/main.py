from fastapi import FastAPI, File, UploadFile
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "/app/procurements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process_procurement")
async def process_procurement(Proc_ID, procurement_file: UploadFile = File(...), agreement_file: UploadFile = File(...)): 
    
    procurement_dir = UPLOAD_DIR / Proc_ID
    os.makedirs(procurement_dir, exist_ok=True)

    file_path = os.path.join(procurement_dir, procurement_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(procurement_file.file, buffer)

    if agreement_file:
        # Upload agreement file
        return
    
    # main script (pass in, proc_id, procurement_file, agreement_file, other data) -> generates csv file

    return {"proc_path": procurement_dir} # Get procurment_file path

@app.get("/get_csv_info")
async def get_csv_info(procurement_file_name):
    #with open(procurement_file_name, "wb") as buffer:
    df = pd.read_csv(procurement_file_name, keep_default_na=False, encoding="utf-8")
    # turn csv -> json list of objects
    # when extracting Pamatojums, get only the explanation key
    #     {
    #   ""answer"": ""jā"",
    #   ""rate"": ""augsta"",
    #   ""explanation"": ""Kontekstā ir norādīts, ka iepirkuma priekšmets nav sadalīts daļās. Iepirkuma priekšmets netiek dalīts daļās, jo ir viens pretendentu loks; viens būvobjekts; viens būvdarbu veikšanas laiks būvobjektā.""
    # }
    procurement_data = df.json
    return procurement_data
    # List of objects like these:
    #     {
    #     "Nr": "8",
    #     "Atbilde": "nē",
    #     "Pamatojums": "Nezinu"
    # }
    