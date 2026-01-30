from __future__ import annotations

import uuid
from typing import Iterable, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from sit.models import (
    KeywordList,
    KeywordListItem,
    SIT,
    SITPrimaryElement,
    SITSupportingGroup,
    SITSupportingItem,
    SITSupportingLogic,
    SITVersion,
)


class SitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_sits(self, name: Optional[str] = None) -> List[SIT]:
        stmt = select(SIT).options(joinedload(SIT.versions))
        if name:
            stmt = stmt.where(SIT.name.ilike(f"%{name}%"))
        stmt = stmt.order_by(SIT.created_at.desc())
        return list(self.session.execute(stmt).scalars().unique())

    def get_sit(self, sit_id: str) -> Optional[SIT]:
        stmt = (
            select(SIT)
            .where(SIT.id == sit_id)
            .options(
                joinedload(SIT.versions)
                .joinedload(SITVersion.primary_element),
                joinedload(SIT.versions)
                .joinedload(SITVersion.supporting_logic),
                joinedload(SIT.versions)
                .joinedload(SITVersion.supporting_groups)
                .joinedload(SITSupportingGroup.items)
                .joinedload(SITSupportingItem.keyword_list),
            )
        )
        return self.session.execute(stmt).scalars().unique().first()

    def create_sit(self, name: str, description: Optional[str]) -> SIT:
        sit = SIT(id=str(uuid.uuid4()), name=name, description=description)
        self.session.add(sit)
        self.session.commit()
        return sit

    def create_version(
        self,
        sit_id: str,
        entity_type: Optional[str],
        confidence: Optional[str],
        source: Optional[str],
        primary_element: dict,
        supporting_logic: dict,
        supporting_groups: list[dict],
    ) -> SITVersion:
        version_number = self._next_version_number(sit_id)
        version = SITVersion(
            id=str(uuid.uuid4()),
            sit_id=sit_id,
            version_number=version_number,
            entity_type=entity_type,
            confidence=confidence,
            source=source,
        )
        version.primary_element = SITPrimaryElement(
            id=str(uuid.uuid4()),
            element_type=primary_element["type"],
            value=primary_element["value"],
        )
        version.supporting_logic = SITSupportingLogic(
            id=str(uuid.uuid4()),
            mode=supporting_logic["mode"],
            min_n=supporting_logic.get("min_n"),
            max_n=supporting_logic.get("max_n"),
        )

        for index, group in enumerate(supporting_groups):
            group_model = SITSupportingGroup(
                id=str(uuid.uuid4()),
                name=group["name"],
                position=index,
            )
            for item_index, item in enumerate(group["items"]):
                group_model.items.append(
                    SITSupportingItem(
                        id=str(uuid.uuid4()),
                        item_type=item["type"],
                        value=item.get("value"),
                        keyword_list_id=item.get("keyword_list_id"),
                        position=item_index,
                    )
                )
            version.supporting_groups.append(group_model)

        self.session.add(version)
        self.session.commit()
        return version

    def _next_version_number(self, sit_id: str) -> int:
        stmt = select(func.max(SITVersion.version_number)).where(SITVersion.sit_id == sit_id)
        current = self.session.execute(stmt).scalar_one_or_none()
        return (current or 0) + 1

    def create_keyword_list(
        self, name: str, description: Optional[str], items: list[str]
    ) -> KeywordList:
        keyword_list = KeywordList(
            id=str(uuid.uuid4()), name=name, description=description
        )
        keyword_list.items = [
            KeywordListItem(id=str(uuid.uuid4()), value=item) for item in items
        ]
        self.session.add(keyword_list)
        self.session.commit()
        return keyword_list

    def list_keyword_lists(self) -> List[KeywordList]:
        stmt = select(KeywordList).options(joinedload(KeywordList.items))
        return list(self.session.execute(stmt).scalars().unique())

    def get_versions_by_ids(self, ids: Iterable[str]) -> List[SITVersion]:
        if not ids:
            return []
        stmt = (
            select(SITVersion)
            .where(SITVersion.id.in_(list(ids)))
            .options(
                joinedload(SITVersion.sit),
                joinedload(SITVersion.primary_element),
                joinedload(SITVersion.supporting_logic),
                joinedload(SITVersion.supporting_groups)
                .joinedload(SITSupportingGroup.items)
                .joinedload(SITSupportingItem.keyword_list)
                .joinedload(KeywordList.items),
            )
        )
        return list(self.session.execute(stmt).scalars().unique())
