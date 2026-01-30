from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable

from sqlalchemy.orm import Session

from common.config import settings
from common.utils import file_hash
from ingestion.archive import ArchiveExtractionError, extract_archive
from ingestion.extractors import (
    extract_text_docx,
    extract_text_pptx,
    extract_text_xlsx,
)
from ingestion.pdf_utils import extract_text_pdf, render_pdf_to_images
from ingestion.types import detect_type
from findings.generator import generate_findings_from_text
from findings.repository import FindingsRepository
from pii.engines import PIIEngines

logger = logging.getLogger(__name__)


class ProcessingStats:
    """Track scan statistics."""

    def __init__(self) -> None:
        self.entities_found = 0
        self.files_processed = 0


class FileProcessor:
    """Process files to extract text, detect PII, and store findings."""

    def __init__(self, session: Session, job_id: str) -> None:
        self.session = session
        self.job_id = job_id
        self.engines = PIIEngines()
        self.findings = FindingsRepository(session)

    def process_path(self, path: Path, stats: ProcessingStats, depth: int = 0) -> None:
        if depth > settings.max_archive_depth:
            logger.warning("archive_depth_exceeded", extra={"path": str(path)})
            return

        if path.is_dir():
            for child in path.iterdir():
                self.process_path(child, stats, depth=depth)
            return

        if path.stat().st_size > settings.max_file_size_mb * 1024 * 1024:
            logger.warning("file_too_large", extra={"path": str(path)})
            return

        if should_skip_file(self.session, path):
            logger.info("file_skipped", extra={"path": str(path)})
            return

        file_type = detect_type(path)
        stats.files_processed += 1
        if file_type == "archive":
            self._process_archive(path, stats, depth)
            return
        if file_type == "pdf":
            self._process_pdf(path, stats)
            return
        if file_type == "image":
            self._process_image(path, stats)
            return
        if file_type in {"docx", "pptx", "xlsx"}:
            self._process_office(path, file_type, stats)
            return
        if file_type == "text":
            self._process_text_file(path, stats)
            return

        logger.info("unsupported_file_type", extra={"path": str(path)})
        mark_file_processed(self.session, path)

    def _process_archive(self, path: Path, stats: ProcessingStats, depth: int) -> None:
        extract_dir = path.parent / f"extracted_{path.stem}"
        try:
            extracted = extract_archive(path, extract_dir)
        except ArchiveExtractionError as exc:
            logger.warning("archive_extract_failed", extra={"path": str(path), "error": str(exc)})
            return
        for item in extracted:
            self.process_path(item, stats, depth=depth + 1)
        mark_file_processed(self.session, path)

    def _process_pdf(self, path: Path, stats: ProcessingStats) -> None:
        text = extract_text_pdf(path)
        if text and text.strip():
            self._analyze_text(text, path, stats)
            mark_file_processed(self.session, path)
            return

        image_dir = path.parent / f"ocr_{path.stem}"
        images = render_pdf_to_images(path, image_dir, settings.ocr_max_pages)
        for image_path in images:
            self._process_image(image_path, stats)
        mark_file_processed(self.session, path)

    def _process_image(self, path: Path, stats: ProcessingStats) -> None:
        ocr_text, results = self.engines.analyze_image(path)
        if not ocr_text:
            mark_file_processed(self.session, path)
            return
        self._analyze_results(results, ocr_text, path, stats)
        mark_file_processed(self.session, path)

    def _process_office(self, path: Path, file_type: str, stats: ProcessingStats) -> None:
        if file_type == "docx":
            text = extract_text_docx(path)
        elif file_type == "pptx":
            text = extract_text_pptx(path)
        else:
            text = extract_text_xlsx(path)
        self._analyze_text(text, path, stats)
        mark_file_processed(self.session, path)

    def _process_text_file(self, path: Path, stats: ProcessingStats) -> None:
        from common.utils import stream_file_chunks

        for chunk in stream_file_chunks(path):
            if chunk.strip():
                results = self.engines.analyze_text(chunk)
                self._analyze_results(results, chunk, path, stats)
        mark_file_processed(self.session, path)

    def _analyze_text(self, text: str, path: Path, stats: ProcessingStats) -> None:
        results = self.engines.analyze_text(text)
        self._analyze_results(results, text, path, stats)

    def _analyze_results(
        self,
        results: Iterable,
        text: str,
        path: Path,
        stats: ProcessingStats,
    ) -> None:
        results_list = list(results)
        stats.entities_found += len(results_list)
        if not results_list:
            return
        findings = generate_findings_from_text(results_list, text)
        self.findings.add_findings(self.job_id, str(path), findings)


def should_skip_file(session: Session, path: Path) -> bool:
    from jobs.repository import ProcessedFileRepository

    repo = ProcessedFileRepository(session)
    digest = file_hash(path)
    return repo.is_hash_processed(digest)


def mark_file_processed(session: Session, path: Path) -> None:
    from jobs.repository import ProcessedFileRepository

    repo = ProcessedFileRepository(session)
    digest = file_hash(path)
    repo.mark_processed(str(path), digest)
