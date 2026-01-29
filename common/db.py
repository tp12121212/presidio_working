from sqlalchemy import create_engine
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
