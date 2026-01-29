from __future__ import annotations

import uuid
from typing import Iterable, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from purview.models import Rulepack, RulepackSelection


class RulepackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_rulepack(
        self,
        name: str,
        version: str,
        description: Optional[str],
        publisher: Optional[str],
        locale: Optional[str],
    ) -> Rulepack:
        rulepack = Rulepack(
            id=str(uuid.uuid4()),
            name=name,
            version=version,
            description=description,
            publisher=publisher,
            locale=locale,
        )
        self.session.add(rulepack)
        self.session.commit()
        return rulepack

    def list_rulepacks(self) -> List[Rulepack]:
        stmt = select(Rulepack).options(joinedload(Rulepack.selections))
        stmt = stmt.order_by(Rulepack.created_at.desc())
        return list(self.session.execute(stmt).scalars().unique())

    def get_rulepack(self, rulepack_id: str) -> Optional[Rulepack]:
        stmt = (
            select(Rulepack)
            .where(Rulepack.id == rulepack_id)
            .options(joinedload(Rulepack.selections))
        )
        return self.session.execute(stmt).scalars().unique().first()

    def set_selections(self, rulepack_id: str, version_ids: Iterable[str]) -> None:
        self.session.execute(
            delete(RulepackSelection).where(RulepackSelection.rulepack_id == rulepack_id)
        )
        for version_id in version_ids:
            self.session.add(
                RulepackSelection(rulepack_id=rulepack_id, sit_version_id=version_id)
            )
        self.session.commit()
