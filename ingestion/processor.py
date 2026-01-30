from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from common.config import settings
from common.utils import file_hash
from ingestion.archive import ArchiveExtractionError, ExtractedItem, extract_archive
from ingestion.email_utils import EmailExtractedItem, extract_eml, extract_msg
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
from scans.repository import ScanItemRepository

logger = logging.getLogger(__name__)


class ProcessingStats:
    """Track scan statistics."""

    def __init__(self) -> None:
        self.entities_found = 0
        self.files_processed = 0


@dataclass
class ScanOptions:
    entities: Optional[List[str]] = None
    language: str = "en"
    score_threshold: Optional[float] = None
    ocr_mode: str = "auto"  # auto | force | off
    include_headers: bool = True
    parse_html: bool = True
    include_attachments: bool = True
    include_inline_images: bool = True


class FileProcessor:
    """Process files to extract text, detect PII, and store findings."""

    def __init__(self, session: Session, job_id: str, options: ScanOptions) -> None:
        self.session = session
        self.job_id = job_id
        self.engines = PIIEngines()
        self.findings = FindingsRepository(session)
        self.scan_items = ScanItemRepository(session)
        self.options = options

    def process_path(
        self,
        path: Path,
        stats: ProcessingStats,
        depth: int = 0,
        virtual_path: Optional[str] = None,
        root_dir: Optional[Path] = None,
    ) -> None:
        if depth > settings.max_archive_depth:
            logger.warning("archive_depth_exceeded", extra={"path": str(path)})
            return

        if path.is_dir():
            for child in path.iterdir():
                self.process_path(
                    child, stats, depth=depth, virtual_path=None, root_dir=root_dir
                )
            return

        if path.stat().st_size > settings.max_file_size_mb * 1024 * 1024:
            logger.warning("file_too_large", extra={"path": str(path)})
            return

        if should_skip_file(self.session, path):
            logger.info("file_skipped", extra={"path": str(path)})
            return

        if virtual_path is None and root_dir:
            virtual_path = str(path.relative_to(root_dir))
        if virtual_path is None:
            virtual_path = str(path)

        file_type = detect_type(path)
        stats.files_processed += 1
        if file_type == "archive":
            self._process_archive(path, stats, depth, virtual_path)
            return
        if file_type == "pdf":
            self._process_pdf(path, stats, virtual_path)
            return
        if file_type == "image":
            self._process_image(path, stats, virtual_path)
            return
        if file_type == "email":
            self._process_email(path, stats, depth, virtual_path)
            return
        if file_type in {"docx", "pptx", "xlsx"}:
            self._process_office(path, file_type, stats, virtual_path)
            return
        if file_type == "text":
            self._process_text_file(path, stats, virtual_path)
            return

        logger.info("unsupported_file_type", extra={"path": str(path)})
        mark_file_processed(self.session, path)

    def _process_archive(
        self, path: Path, stats: ProcessingStats, depth: int, virtual_path: str
    ) -> None:
        extract_dir = path.parent / f"extracted_{path.stem}"
        warnings: list[str] = []
        try:
            extracted = extract_archive(path, extract_dir)
        except ArchiveExtractionError as exc:
            warnings.append(str(exc))
            logger.warning(
                "archive_extract_failed",
                extra={"path": str(path), "error": str(exc)},
            )
            self._record_item(
                path,
                virtual_path,
                "container",
                ocr_used=False,
                warnings=warnings,
            )
            return
        self._record_item(
            path,
            virtual_path,
            "container",
            ocr_used=False,
            warnings=warnings,
        )
        for item in extracted:
            child_virtual = f"{virtual_path}::{item.relative_path}"
            self.process_path(
                item.path,
                stats,
                depth=depth + 1,
                virtual_path=child_virtual,
            )
        mark_file_processed(self.session, path)

    def _process_pdf(self, path: Path, stats: ProcessingStats, virtual_path: str) -> None:
        text = extract_text_pdf(path)
        ocr_mode = self.options.ocr_mode
        if text and text.strip() and ocr_mode != "force":
            self._analyze_text(text, virtual_path, stats)
            self._record_item(
                path,
                virtual_path,
                "text",
                ocr_used=False,
                text_preview=text,
            )
            mark_file_processed(self.session, path)
            return

        image_dir = path.parent / f"ocr_{path.stem}"
        images = render_pdf_to_images(path, image_dir, settings.ocr_max_pages)
        for image_path in images:
            self._process_image(
                image_path,
                stats,
                f"{virtual_path}::page_{image_path.stem}",
                parent_virtual=virtual_path,
            )
        if text and text.strip() and ocr_mode == "force":
            self._analyze_text(text, virtual_path, stats)
            self._record_item(
                path,
                virtual_path,
                "hybrid",
                ocr_used=True,
                text_preview=text,
            )
        else:
            self._record_item(
                path,
                virtual_path,
                "ocr",
                ocr_used=True,
            )
        mark_file_processed(self.session, path)

    def _process_image(
        self,
        path: Path,
        stats: ProcessingStats,
        virtual_path: str,
        parent_virtual: Optional[str] = None,
    ) -> None:
        if self.options.ocr_mode == "off":
            self._record_item(
                path,
                virtual_path,
                "none",
                ocr_used=False,
                warnings=["OCR disabled; image skipped."],
            )
            mark_file_processed(self.session, path)
            return
        ocr_text, results = self.engines.analyze_image(
            path,
            language=self.options.language,
            score_threshold=self.options.score_threshold,
        )
        if not ocr_text:
            self._record_item(
                path,
                virtual_path,
                "ocr",
                ocr_used=True,
                warnings=["No OCR text extracted."],
            )
            mark_file_processed(self.session, path)
            return
        self._analyze_results(results, ocr_text, virtual_path, stats)
        self._record_item(
            path,
            virtual_path,
            "ocr",
            ocr_used=True,
            text_preview=ocr_text,
        )
        mark_file_processed(self.session, path)

    def _process_office(
        self, path: Path, file_type: str, stats: ProcessingStats, virtual_path: str
    ) -> None:
        if file_type == "docx":
            text = extract_text_docx(path)
        elif file_type == "pptx":
            text = extract_text_pptx(path)
        else:
            text = extract_text_xlsx(path)
        self._analyze_text(text, virtual_path, stats)
        self._record_item(
            path,
            virtual_path,
            "text",
            ocr_used=False,
            text_preview=text,
        )
        mark_file_processed(self.session, path)

    def _process_text_file(
        self, path: Path, stats: ProcessingStats, virtual_path: str
    ) -> None:
        from common.utils import stream_file_chunks

        collected = []
        for chunk in stream_file_chunks(path):
            if chunk.strip():
                results = self.engines.analyze_text(
                    chunk,
                    entities=self.options.entities,
                    language=self.options.language,
                    score_threshold=self.options.score_threshold,
                )
                self._analyze_results(results, chunk, virtual_path, stats)
                if len(collected) < 3:
                    collected.append(chunk)
        preview = "".join(collected)[:4000]
        self._record_item(
            path,
            virtual_path,
            "text",
            ocr_used=False,
            text_preview=preview,
        )
        mark_file_processed(self.session, path)

    def _process_email(
        self, path: Path, stats: ProcessingStats, depth: int, virtual_path: str
    ) -> None:
        extract_dir = path.parent / f"email_{path.stem}"
        warnings: list[str] = []
        items: list[EmailExtractedItem] = []
        try:
            if path.suffix.lower() == ".eml":
                items, warnings = extract_eml(
                    path,
                    extract_dir,
                    include_headers=self.options.include_headers,
                    parse_html=self.options.parse_html,
                    include_attachments=self.options.include_attachments,
                    include_inline_images=self.options.include_inline_images,
                )
            else:
                items, warnings = extract_msg(
                    path,
                    extract_dir,
                    include_headers=self.options.include_headers,
                    parse_html=self.options.parse_html,
                    include_attachments=self.options.include_attachments,
                    include_inline_images=self.options.include_inline_images,
                )
        except Exception as exc:  # noqa: BLE001
            warnings.append(str(exc))
            logger.warning("email_extract_failed", extra={"path": str(path), "error": str(exc)})

        self._record_item(
            path,
            virtual_path,
            "container",
            ocr_used=False,
            warnings=warnings,
        )

        for item in items:
            child_virtual = f"{virtual_path}::{item.virtual_path}"
            self.process_path(
                item.path,
                stats,
                depth=depth + 1,
                virtual_path=child_virtual,
            )
        mark_file_processed(self.session, path)

    def _analyze_text(self, text: str, virtual_path: str, stats: ProcessingStats) -> None:
        results = self.engines.analyze_text(
            text,
            entities=self.options.entities,
            language=self.options.language,
            score_threshold=self.options.score_threshold,
        )
        self._analyze_results(results, text, virtual_path, stats)

    def _analyze_results(
        self,
        results: Iterable,
        text: str,
        virtual_path: str,
        stats: ProcessingStats,
    ) -> None:
        results_list = list(results)
        stats.entities_found += len(results_list)
        if not results_list:
            return
        findings = generate_findings_from_text(results_list, text)
        self.findings.add_findings(self.job_id, virtual_path, findings)

    def _record_item(
        self,
        path: Path,
        virtual_path: str,
        extraction_method: str,
        ocr_used: bool,
        warnings: Optional[List[str]] = None,
        text_preview: Optional[str] = None,
    ) -> None:
        preview = (text_preview or "")[:4000]
        self.scan_items.add_item(
            job_id=self.job_id,
            virtual_path=virtual_path,
            source_path=str(path),
            mime_type=detect_type(path),
            extraction_method=extraction_method,
            ocr_used=ocr_used,
            text_chars=len(text_preview or ""),
            text_preview=preview,
            warnings=warnings or [],
        )


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
