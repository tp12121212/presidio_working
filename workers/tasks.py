from __future__ import annotations

import logging
from pathlib import Path

from common.db import SessionLocal, init_db
from ingestion.processor import FileProcessor, ProcessingStats, ScanOptions, should_skip_file
from jobs.repository import JobRepository
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="scan_file_job")
def scan_file_job(
    job_id: str,
    file_path: str,
    options: dict | None = None,
    virtual_root: str | None = None,
    root_dir: str | None = None,
) -> None:
    init_db()
    session = SessionLocal()
    stats = ProcessingStats()
    repo = JobRepository(session)
    repo.update_status(job_id, "running")
    path = Path(file_path)
    scan_options = ScanOptions(**(options or {}))
    processor = FileProcessor(session, job_id, scan_options)

    try:
        if should_skip_file(session, path) and not path.is_dir():
            repo.update_status(job_id, "skipped")
            return
        processor.process_path(
            path,
            stats,
            virtual_path=virtual_root,
            root_dir=Path(root_dir) if root_dir else None,
        )
        repo.update_counts(
            job_id,
            processed_files=stats.files_processed,
            entities_found=stats.entities_found,
            findings_created=stats.entities_found,
        )
        repo.update_status(job_id, "completed")
    except Exception as exc:  # noqa: BLE001
        logger.exception("scan_failed", extra={"job_id": job_id, "error": str(exc)})
        session.rollback()
        repo.update_status(job_id, "failed", error=str(exc))
    finally:
        session.close()
