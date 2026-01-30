# Presidio - Data Protection and De-identification SDK

### Goals

- Help identify documents (Office, PDF, Archive (zip,7z,rar,etc), images (jpeg,gif,tiff,jpg,png) and image/scanned PDF via OCR that contain sensitive information.
- There are two modes, 
    - discovery mode: scan all files in a network share or local file path
    - Targeted Scan: this allows you to upload specific document(s) (i.e. New Employee on-barding form)
- Once documents are scanned regex matches and relevant keywords are generated and stored in a database 
- These can then be used to generate a purview xml sensitive information rulepack which can be imported into Microsoft Purview 
- The generated xml rulepack will support SITs with primary, supporting elements, character proximity, supporting element AND OR ANY groups.

## Presidio SIT Service (Custom Purview SIT generation)

This repo includes a FastAPI + Celery service which scans files for PII, stores scan findings,
curates SITs in a versioned repository, and exports Microsoft Purview rule packages from selected
SIT versions.

### Run with Docker Compose

```bash
docker compose -f docker-compose.sit-service.yml up --build
```

### Local development (venv + SQLite)

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

### Worker (local)

```bash
celery -A workers.celery_app worker --loglevel=info --concurrency=2
```

### Example API calls

```bash
curl -F "file=@/path/to/sample.pdf" http://localhost:8000/scan
curl http://localhost:8000/jobs/<job_id>
curl "http://localhost:8000/findings?job_id=<job_id>"
curl http://localhost:8000/sits
curl -X POST http://localhost:8000/rulepacks/<rulepack_id>/export
```

### UI screens

Open the UI for the guided workflow:
- `http://localhost:8000/ui/scans`
- `http://localhost:8000/ui/findings`
- `http://localhost:8000/ui/sits`
- `http://localhost:8000/ui/rulepacks`

