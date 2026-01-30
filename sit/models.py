from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from common.db import Base


class SIT(Base):
    __tablename__ = "sit"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    versions = relationship(
        "SITVersion",
        back_populates="sit",
        cascade="all, delete-orphan",
        order_by="SITVersion.version_number",
    )


class SITVersion(Base):
    __tablename__ = "sit_version"

    id = Column(String, primary_key=True)
    sit_id = Column(String, ForeignKey("sit.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    entity_type = Column(String)
    confidence = Column(String)
    source = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sit = relationship("SIT", back_populates="versions")
    primary_element = relationship(
        "SITPrimaryElement",
        back_populates="sit_version",
        uselist=False,
        cascade="all, delete-orphan",
    )
    supporting_logic = relationship(
        "SITSupportingLogic",
        back_populates="sit_version",
        uselist=False,
        cascade="all, delete-orphan",
    )
    supporting_groups = relationship(
        "SITSupportingGroup",
        back_populates="sit_version",
        cascade="all, delete-orphan",
        order_by="SITSupportingGroup.position",
    )


class SITPrimaryElement(Base):
    __tablename__ = "sit_primary_element"

    id = Column(String, primary_key=True)
    sit_version_id = Column(
        String, ForeignKey("sit_version.id", ondelete="CASCADE"), nullable=False
    )
    element_type = Column(String, nullable=False)  # regex | keyword
    value = Column(Text, nullable=False)

    sit_version = relationship("SITVersion", back_populates="primary_element")


class SITSupportingLogic(Base):
    __tablename__ = "sit_supporting_logic"

    id = Column(String, primary_key=True)
    sit_version_id = Column(
        String, ForeignKey("sit_version.id", ondelete="CASCADE"), nullable=False
    )
    mode = Column(
        Enum("ANY", "ALL", "MIN_N", name="supporting_logic_mode"), nullable=False
    )
    min_n = Column(Integer)
    max_n = Column(Integer)

    sit_version = relationship("SITVersion", back_populates="supporting_logic")


class SITSupportingGroup(Base):
    __tablename__ = "sit_supporting_group"

    id = Column(String, primary_key=True)
    sit_version_id = Column(
        String, ForeignKey("sit_version.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    position = Column(Integer, default=0, nullable=False)

    sit_version = relationship("SITVersion", back_populates="supporting_groups")
    items = relationship(
        "SITSupportingItem",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="SITSupportingItem.position",
    )


class SITSupportingItem(Base):
    __tablename__ = "sit_supporting_item"

    id = Column(String, primary_key=True)
    group_id = Column(
        String, ForeignKey("sit_supporting_group.id", ondelete="CASCADE"), nullable=False
    )
    item_type = Column(String, nullable=False)  # regex | keyword | keyword_list
    value = Column(Text)
    keyword_list_id = Column(String, ForeignKey("keyword_list.id"))
    position = Column(Integer, default=0, nullable=False)

    group = relationship("SITSupportingGroup", back_populates="items")
    keyword_list = relationship("KeywordList")


class KeywordList(Base):
    __tablename__ = "keyword_list"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship(
        "KeywordListItem",
        back_populates="keyword_list",
        cascade="all, delete-orphan",
    )


class KeywordListItem(Base):
    __tablename__ = "keyword_list_item"

    id = Column(String, primary_key=True)
    keyword_list_id = Column(
        String, ForeignKey("keyword_list.id", ondelete="CASCADE"), nullable=False
    )
    value = Column(String, nullable=False)

    keyword_list = relationship("KeywordList", back_populates="items")
