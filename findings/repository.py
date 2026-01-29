from __future__ import annotations

import uuid
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from findings.generator import FindingCandidate
from findings.models import ScanFinding


class FindingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_findings(
        self,
        job_id: str,
        file_path: str,
        findings: Iterable[FindingCandidate],
    ) -> None:
        for finding in findings:
            record = ScanFinding(
                id=str(uuid.uuid4()),
                job_id=job_id,
                file_path=file_path,
                entity_type=finding.entity_type,
                score=finding.score,
                start=finding.start,
                end=finding.end,
                context=finding.context,
                primary_regex=finding.primary_regex,
                supporting_keywords=finding.supporting_keywords,
            )
            self.session.add(record)
        self.session.commit()

    def list_findings(
        self,
        job_id: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[ScanFinding]:
        stmt = select(ScanFinding)
        if job_id:
            stmt = stmt.where(ScanFinding.job_id == job_id)
        if entity_type:
            stmt = stmt.where(ScanFinding.entity_type == entity_type)
        stmt = stmt.order_by(ScanFinding.created_at.desc())
        return list(self.session.execute(stmt).scalars())

    def get(self, finding_id: str) -> Optional[ScanFinding]:
        return self.session.get(ScanFinding, finding_id)
