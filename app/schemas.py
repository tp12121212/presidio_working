from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobRead(BaseModel):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    file_name: Optional[str] = None
    file_hash: Optional[str] = None
    error: Optional[str] = None
    total_files: int
    processed_files: int
    entities_found: int
    findings_created: int

    class Config:
        from_attributes = True


class FindingRead(BaseModel):
    id: str
    job_id: str
    file_path: Optional[str] = None
    entity_type: str
    score: Optional[float] = None
    context: Optional[str] = None
    primary_regex: Optional[str] = None
    supporting_keywords: List[str] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class RulepackCreate(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    publisher: Optional[str] = None
    locale: Optional[str] = None


class RulepackRead(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str] = None
    publisher: Optional[str] = None
    locale: Optional[str] = None
    created_at: datetime
    selections: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RulepackSelectionUpdate(BaseModel):
    version_ids: List[str] = Field(default_factory=list)
