from __future__ import annotations

import logging
from pathlib import Path

from common.db import SessionLocal, init_db
from ingestion.processor import FileProcessor, ProcessingStats, should_skip_file
from jobs.repository import JobRepository
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="scan_file_job")
def scan_file_job(job_id: str, file_path: str) -> None:
    init_db()
    session = SessionLocal()
    stats = ProcessingStats()
    repo = JobRepository(session)
    repo.update_status(job_id, "running")
    path = Path(file_path)

    try:
        if should_skip_file(session, path):
            repo.update_status(job_id, "skipped")
            return
        processor = FileProcessor(session, job_id)
        processor.process_path(path, stats)
        repo.update_counts(
            job_id,
            processed_files=stats.files_processed,
            entities_found=stats.entities_found,
            findings_created=stats.entities_found,
        )
        repo.update_status(job_id, "completed")
    except Exception as exc:  # noqa: BLE001
        logger.exception("scan_failed", extra={"job_id": job_id, "error": str(exc)})
        repo.update_status(job_id, "failed", error=str(exc))
    finally:
        session.close()
