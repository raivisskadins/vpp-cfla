from fastapi import FastAPI, File, UploadFile, HTTPException
from pathlib import Path
import shutil
import pandas as pd

app = FastAPI()

# Base dir inside the container where we’ll store uploads
UPLOAD_DIR = Path("/app/procurements")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/process_procurement")
async def process_procurement(
    Proc_ID: str,
    procurement_file: UploadFile = File(...),
    agreement_file: UploadFile = File(None),
):
    """
    Saves the uploaded files into /app/procurements/{Proc_ID}/
    and returns the path to the generated report.csv.
    """
    # Create procurement-specific directory
    procurement_dir = UPLOAD_DIR / Proc_ID
    procurement_dir.mkdir(parents=True, exist_ok=True)

    # Save procurement file
    proc_path = procurement_dir / procurement_file.filename
    with proc_path.open("wb") as buffer:
        shutil.copyfileobj(procurement_file.file, buffer)

    # (Optional) Save agreement file if provided
    if agreement_file:
        agr_path = procurement_dir / agreement_file.filename
        with agr_path.open("wb") as buffer:
            shutil.copyfileobj(agreement_file.file, buffer)

    # Here you’d call your processing script, e.g.:
    # report_path = main_script.generate_report(proc_path, agr_path, output_dir=procurement_dir)
    # For now let’s assume it writes report.csv into procurement_dir:
    report_path = procurement_dir / "report.csv"

    # Make sure the report actually exists
    if not report_path.exists():
        raise HTTPException(status_code=500, detail="Report not generated")

    return {"proc_report_path": str(report_path)}


@app.get("/get_csv_info")
async def get_csv_info(proc_report_path: str):
    """
    Reads the CSV at proc_report_path and returns a JSON array of rows.
    """
    path = Path(proc_report_path)
    if not path.exists() or not path.suffix == ".csv":
        raise HTTPException(status_code=404, detail="CSV not found")

    # Load CSV into a DataFrame
    df = pd.read_csv(path, keep_default_na=False, encoding="utf-8")

    # Convert each row to a dict and return
    data = df.to_dict(orient="records")
    return {"procurement_data": data}
