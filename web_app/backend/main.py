from fastapi import FastAPI, File, UploadFile
import shutil
import os

#from scripts.web_report import build_web_report_html

app = FastAPI()

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

@app.get("/get_csv_info")
async def get_csv_info():
    #with open(get_csv_name, "wb") as buffer:
    return build_web_report_html({
        "Nr": "8",
        "Atbilde": "nē",
        "Pamatojums": "Nezinu"
    })

def build_web_report_html(data: dict) -> str:
    html = [
        "<table>",
        "  <thead><tr><th>Nr</th><th>Atbilde</th><th>Pamatojums</th></tr></thead>",
        "  <tbody>"
    ]

    html.append(f"    <tr>")
    html.append(f"      <td>{data['Nr']}</td>")
    html.append(f"      <td>{data['Atbilde']}</td>")
    html.append(f"      <td>{data['Pamatojums']}</td>")
    html.append(f"    </tr>")

    html.extend([
        "  </tbody>",
        "</table>",
    ])

    return html
    