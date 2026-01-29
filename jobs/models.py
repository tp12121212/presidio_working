from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from common.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_name = Column(Text)
    file_hash = Column(String)
    error = Column(Text)
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    entities_found = Column(Integer, default=0)
    findings_created = Column(Integer, default=0)


class ProcessedFile(Base):
    __tablename__ = "processed_files"

    file_hash = Column(String, primary_key=True)
    path = Column(Text)
    last_scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
