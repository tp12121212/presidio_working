from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from common.db import Base


class Rulepack(Base):
    __tablename__ = "rulepack"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(Text)
    publisher = Column(String)
    locale = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    selections = relationship(
        "RulepackSelection",
        back_populates="rulepack",
        cascade="all, delete-orphan",
    )


class RulepackSelection(Base):
    __tablename__ = "rulepack_selection"

    rulepack_id = Column(
        String, ForeignKey("rulepack.id", ondelete="CASCADE"), primary_key=True
    )
    sit_version_id = Column(
        String, ForeignKey("sit_version.id", ondelete="CASCADE"), primary_key=True
    )

    rulepack = relationship("Rulepack", back_populates="selections")
