# Presidio - Data Protection and De-identification SDK

## Overview
This repo provides:
- Presidio Analyzer/Anonymizer/Image Redactor APIs
- A SIT Service (FastAPI + Celery) that scans files for PII, stores findings, curates SITs, and exports Purview rulepacks
- A modern web UI (React) that mirrors the Hugging Face Presidio demo and adds full scan -> results -> SIT build -> export workflows

## Quick start (Docker)

### 1) Presidio services (Analyzer/Anonymizer/Image Redactor)
```bash
docker compose -f docker-compose.yml up --build
```
Ports:
- Analyzer: http://localhost:5002
- Anonymizer: http://localhost:5001
- Image Redactor: http://localhost:5003

### 2) SIT Service
```bash
docker compose -f docker-compose.sit-service.yml up --build
```
Port:
- SIT Service: http://localhost:8000

### 3) Web UI
```bash
cd web-ui
npm install
npm run dev
```
Open http://localhost:5173

### Optional environment overrides (UI)
If you run services on different ports/hosts:
```bash
export VITE_ANALYZER_URL=http://localhost:5002
export VITE_ANONYMIZER_URL=http://localhost:5001
export VITE_SIT_API_URL=http://localhost:8000
```
The dev server proxies `/api/analyzer`, `/api/anonymizer`, `/api/sit`, `/api/scan`, and `/api/presidio` to avoid CORS.

## Local dev (venv + SQLite)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-sit-service.txt

export PRESIDIO_SIT_DATABASE_URL=sqlite:///./presidio_sit.db
export PRESIDIO_SIT_REDIS_URL=redis://localhost:6379/0
export PRESIDIO_SIT_STORAGE_PATH=./data/uploads
export PRESIDIO_SIT_SCAN_ROOT=./data/uploads

uvicorn app.main:app --reload --port 8000
```

Worker:
```bash
celery -A workers.celery_app worker --loglevel=info --concurrency=2
```

## Web UI

### Presidio Demo (text analyze + redact)
- Preserves the Hugging Face demo flow
- Analyze text, review entities, redact output

### Scan Files (full workflow)
1) Upload file, directory, archive, or email
2) Extract text + OCR (as needed)
3) Review results grouped by virtual path
4) Build SITs from findings
5) Export rulepacks

Navigation:
- Presidio Demo
- Scan Files
- Scan Results
- SIT Builder
- Entity Types
- SIT Library
- Rulepack Export

### UI endpoints (SIT Service legacy UI)
- http://localhost:8000/ui/scans
- http://localhost:8000/ui/findings
- http://localhost:8000/ui/sits
- http://localhost:8000/ui/rulepacks

## Scan API (SIT Service)

### Single file
```bash
curl -F "file=@/path/to/sample.pdf" http://localhost:8000/scan/file
```

### Batch (directory upload)
```bash
curl -F "files=@/path/to/file1.pdf" -F "paths=subdir/file1.pdf" \
     -F "files=@/path/to/file2.docx" -F "paths=file2.docx" \
     http://localhost:8000/scan/batch
```

### Archive
```bash
curl -F "archive_file=@/path/to/archive.zip" http://localhost:8000/scan/archive
```

### Email
```bash
curl -F "email_file=@/path/to/email.eml" http://localhost:8000/scan/email
```

### Scan status + results
```bash
curl http://localhost:8000/scan/<scan_id>
```

## SIT API (examples)

Create a SIT with an initial version:
```bash
curl -X POST http://localhost:8000/sits \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manual SSN",
    "description": "Manual entry",
    "version": {
      "entity_type": "SSN",
      "confidence": "medium",
      "primary_element": {
        "type": "regex",
        "value": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
      },
      "supporting_logic": {"mode": "ANY"},
      "supporting_groups": [
        {"name": "context", "items": [{"type": "keyword", "value": "social"}]}
      ]
    }
  }'
```

Create a rulepack and select SIT versions:
```bash
curl -X POST http://localhost:8000/rulepacks \
  -H "Content-Type: application/json" \
  -d '{"name": "Finance Pack", "version": "1", "publisher": "Security"}'

curl -X POST http://localhost:8000/rulepacks/<rulepack_id>/selections \
  -H "Content-Type: application/json" \
  -d '{"version_ids": ["<sit_version_id>"]}'
```

Export the rulepack:
```bash
curl -X POST http://localhost:8000/rulepacks/<rulepack_id>/export
```

## Dependencies

OCR + PDFs:
- Tesseract (OCR)
- Poppler (PDF rendering)

Archive support:
- 7zip for `.7z`
- unrar/bsdtar for `.rar`

Email parsing:
- `extract-msg` (for `.msg`)
- `beautifulsoup4` (HTML to text)

macOS example:
```bash
brew install tesseract poppler p7zip unrar
```

## Supported types
- Office: docx/xlsx/pptx
- PDFs (text + image-based with OCR)
- Images: jpeg/jpg/png/gif/tiff/bmp
- Archives: zip/7z/rar/tar/tgz (nested)
- Emails: .eml / .msg (body + attachments + inline images)

## Guardrails
- Max archive depth: `PRESIDIO_SIT_MAX_ARCHIVE_DEPTH`
- Max archive files: `PRESIDIO_SIT_MAX_ARCHIVE_FILES`
- Max archive bytes: `PRESIDIO_SIT_MAX_ARCHIVE_BYTES`
- Max email attachments: `PRESIDIO_SIT_MAX_EMAIL_ATTACHMENTS`
- Max email bytes: `PRESIDIO_SIT_MAX_EMAIL_BYTES`

Restart the SIT service after changing env vars.

## Notes
- Presidio detection logic is unchanged; new scanning funnels into existing Presidio analyze/redact.
- Raw PII values are not stored in the database beyond short previews for scan UI.
