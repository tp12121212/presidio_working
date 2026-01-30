from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class KeywordListItemRead(BaseModel):
    id: str
    value: str

    class Config:
        from_attributes = True


class KeywordListRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    items: List[KeywordListItemRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class KeywordListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    items: List[str] = Field(default_factory=list)


class PrimaryElementCreate(BaseModel):
    type: str
    value: str


class SupportingItemCreate(BaseModel):
    type: str
    value: Optional[str] = None
    keyword_list_id: Optional[str] = None


class SupportingGroupCreate(BaseModel):
    name: str
    items: List[SupportingItemCreate] = Field(default_factory=list)


class SupportingLogicCreate(BaseModel):
    mode: str
    min_n: Optional[int] = None
    max_n: Optional[int] = None


class SitVersionCreate(BaseModel):
    entity_type: Optional[str] = None
    confidence: Optional[str] = None
    source: Optional[str] = None
    primary_element: PrimaryElementCreate
    supporting_logic: SupportingLogicCreate
    supporting_groups: List[SupportingGroupCreate] = Field(default_factory=list)


class SitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: SitVersionCreate


class SitRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PrimaryElementRead(BaseModel):
    element_type: str
    value: str

    class Config:
        from_attributes = True


class SupportingItemRead(BaseModel):
    item_type: str
    value: Optional[str] = None
    keyword_list_id: Optional[str] = None

    class Config:
        from_attributes = True


class SupportingGroupRead(BaseModel):
    name: str
    items: List[SupportingItemRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SupportingLogicRead(BaseModel):
    mode: str
    min_n: Optional[int] = None
    max_n: Optional[int] = None

    class Config:
        from_attributes = True


class SitVersionRead(BaseModel):
    id: str
    version_number: int
    entity_type: Optional[str] = None
    confidence: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    primary_element: Optional[PrimaryElementRead] = None
    supporting_logic: Optional[SupportingLogicRead] = None
    supporting_groups: List[SupportingGroupRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SitDetailRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    versions: List[SitVersionRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SitExportRequest(BaseModel):
    version_ids: list[str] = Field(default_factory=list)
