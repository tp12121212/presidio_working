from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from common.db import Base


class ScanItem(Base):
    __tablename__ = "scan_items"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    virtual_path = Column(Text, nullable=False)
    source_path = Column(Text)
    mime_type = Column(String)
    extraction_method = Column(String)  # text | ocr | hybrid | container | none
    ocr_used = Column(Boolean, default=False, nullable=False)
    text_chars = Column(Integer, default=0, nullable=False)
    text_preview = Column(Text)
    warnings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
