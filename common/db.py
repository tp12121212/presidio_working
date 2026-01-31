from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from common.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


engine = create_engine(settings.database_url, echo=settings.sqlalchemy_echo)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Initialize database tables."""

    from jobs.models import Job, ProcessedFile  # noqa: F401
    from findings.models import ScanFinding  # noqa: F401
    from scans.models import ScanItem  # noqa: F401
    from purview.models import Rulepack, RulepackSelection  # noqa: F401
    from sit.models import (  # noqa: F401
        KeywordList,
        KeywordListItem,
        SIT,
        SITPrimaryElement,
        SITSupportingGroup,
        SITSupportingItem,
        SITSupportingLogic,
        SITVersion,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_scan_findings_schema()


def _ensure_scan_findings_schema() -> None:
    """Backfill missing columns for existing scan_findings tables."""
    inspector = inspect(engine)
    if "scan_findings" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("scan_findings")}
    if "entity_text" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE scan_findings ADD COLUMN entity_text TEXT"))
