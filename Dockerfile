FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr libtesseract-dev poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-sit-service.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY common /app/common
COPY ingestion /app/ingestion
COPY pii /app/pii
COPY sit /app/sit
COPY purview /app/purview
COPY workers /app/workers
COPY jobs /app/jobs

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
