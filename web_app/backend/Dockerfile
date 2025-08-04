# web_app/backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir python-multipart

# Copy backend source (main.py, modules, etc.)
COPY . .

# Ensure /app is on the import path
ENV PYTHONPATH="${PYTHONPATH:-}:/app"

# Launch Uvicorn pointing at main.py in /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
