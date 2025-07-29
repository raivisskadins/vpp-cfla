FROM python:3.12-slim

WORKDIR /app

# context is whole repo now, so this brings in backend + scripts + anything else
COPY web_app/backend/requirements.txt ./requirements.txt
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install  --no-cache-dir python-multipart

# make sure /app (and its subfolders) are on the import path
ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
