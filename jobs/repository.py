from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs.models import Job, ProcessedFile


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, job_id: str, file_name: str | None = None) -> Job:
        job = Job(id=job_id, status="queued", file_name=file_name)
        self.session.add(job)
        self.session.commit()
        return job

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        job = self.session.get(Job, job_id)
        if not job:
            return
        job.status = status
        job.error = error
        job.updated_at = datetime.utcnow()
        self.session.commit()

    def update_counts(
        self,
        job_id: str,
        processed_files: int,
        entities_found: int,
        findings_created: int,
        total_files: int | None = None,
    ) -> None:
        job = self.session.get(Job, job_id)
        if not job:
            return
        job.total_files = total_files if total_files is not None else processed_files
        job.processed_files = processed_files
        job.entities_found = entities_found
        job.findings_created = findings_created
        job.updated_at = datetime.utcnow()
        self.session.commit()

    def get(self, job_id: str) -> Optional[Job]:
        return self.session.get(Job, job_id)

    def list_jobs(self, limit: int = 20) -> list[Job]:
        stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars())


class ProcessedFileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_hash_processed(self, digest: str) -> bool:
        stmt = select(ProcessedFile).where(ProcessedFile.file_hash == digest)
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def mark_processed(self, path: str, digest: str) -> None:
        record = ProcessedFile(file_hash=digest, path=path)
        self.session.merge(record)
        self.session.commit()
