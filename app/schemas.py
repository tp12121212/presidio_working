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
    entity_text: Optional[str] = None
    score: Optional[float] = None
    start: Optional[int] = None
    end: Optional[int] = None
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


class ScanEntityRead(BaseModel):
    entity_type: str
    start: int
    end: int
    text: Optional[str] = None
    score: Optional[float] = None


class RegexCandidateRead(BaseModel):
    id: str
    label: str
    start: int
    end: int
    text: Optional[str] = None
    entity_type: str
    score: Optional[float] = None
    regex: Optional[str] = None


class KeywordCandidateRead(BaseModel):
    keyword: str
    count: int
    entity_types: List[str] = Field(default_factory=list)


class ScanExtractionRead(BaseModel):
    method: str
    ocr_used: bool
    warnings: List[str] = Field(default_factory=list)
    text_chars: int = 0


class ScanFileRead(BaseModel):
    file_id: str
    virtual_path: str
    mime_type: Optional[str] = None
    text_preview: Optional[str] = None
    extraction: ScanExtractionRead
    entities: List[ScanEntityRead] = Field(default_factory=list)
    regex_candidates: List[RegexCandidateRead] = Field(default_factory=list)
    keyword_candidates: List[KeywordCandidateRead] = Field(default_factory=list)


class ScanRead(BaseModel):
    scan_id: str
    status: str
    error: Optional[str] = None
    files: List[ScanFileRead] = Field(default_factory=list)
