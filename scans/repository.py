from __future__ import annotations

import uuid
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from scans.models import ScanItem


class ScanItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_item(
        self,
        job_id: str,
        virtual_path: str,
        source_path: str | None,
        mime_type: str | None,
        extraction_method: str,
        ocr_used: bool,
        text_chars: int,
        text_preview: str | None,
        warnings: Iterable[str] | None = None,
    ) -> ScanItem:
        record = ScanItem(
            id=str(uuid.uuid4()),
            job_id=job_id,
            virtual_path=virtual_path,
            source_path=source_path,
            mime_type=mime_type,
            extraction_method=extraction_method,
            ocr_used=ocr_used,
            text_chars=text_chars,
            text_preview=text_preview,
            warnings=list(warnings) if warnings else [],
        )
        self.session.add(record)
        self.session.commit()
        return record

    def list_items(self, job_id: str) -> List[ScanItem]:
        stmt = select(ScanItem).where(ScanItem.job_id == job_id)
        return list(self.session.execute(stmt).scalars())
