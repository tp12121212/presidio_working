from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text

from common.db import Base


class ScanFinding(Base):
    __tablename__ = "scan_findings"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    file_path = Column(Text)
    entity_type = Column(String, nullable=False)
    entity_text = Column(Text)
    score = Column(Float)
    start = Column(Integer)
    end = Column(Integer)
    context = Column(Text)
    primary_regex = Column(Text)
    supporting_keywords = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
