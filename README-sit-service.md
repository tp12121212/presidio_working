# Presidio SIT Service

## Overview
This service scans files for PII with Presidio, stores scan findings, lets users curate SITs in a versioned repository, and exports Microsoft Purview XML rule packages from selected SIT versions.

## Local (venv) setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-sit-service.txt
```

## Run with Docker Compose
```bash
docker compose -f docker-compose.sit-service.yml up --build
```

## Run API locally (SQLite)
```bash
export PRESIDIO_SIT_DATABASE_URL=sqlite:///./presidio_sit.db
export PRESIDIO_SIT_REDIS_URL=redis://localhost:6379/0
export PRESIDIO_SIT_STORAGE_PATH=./data/uploads
export PRESIDIO_SIT_SCAN_ROOT=./data/uploads
uvicorn app.main:app --reload --port 8000
```

## Run worker locally
```bash
celery -A workers.celery_app worker --loglevel=info --concurrency=2
```

## Example workflow (API)
Upload a file to scan:
```bash
curl -F "file=@/path/to/sample.pdf" http://localhost:8000/scan
```

Check job status:
```bash
curl http://localhost:8000/jobs/<job_id>
```

Review scan findings:
```bash
curl "http://localhost:8000/findings?job_id=<job_id>"
```

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

## UI
Visit the UI for a guided workflow:
- Scans: `http://localhost:8000/ui/scans`
- Findings: `http://localhost:8000/ui/findings`
- SIT Repository: `http://localhost:8000/ui/sits`
- RulePacks: `http://localhost:8000/ui/rulepacks`

## Notes
- Archives are extracted with depth and file count limits (configurable via env vars).
- OCR uses Presidio image analyzer (Tesseract under the hood).
- Raw PII values are not stored in the database.
