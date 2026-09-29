# Runs the FastAPI app inside docker-compose alongside a standalone Chroma
# server (see docker-compose.yml) — the "remote/server mode" deployment
# path referenced in config.py's CHROMA_HOST switch and in the README.
FROM python:3.12-slim

WORKDIR /app

# Install deps first so this layer is cached across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "ragagent.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
