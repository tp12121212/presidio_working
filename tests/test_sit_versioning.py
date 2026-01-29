import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
create_engine = sqlalchemy.create_engine
sessionmaker = sqlalchemy.orm.sessionmaker

from common.db import Base
from sit.repository import SitRepository


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_sit_versioning_increments():
    session = create_session()
    repo = SitRepository(session)
    sit = repo.create_sit("Test SIT", "desc")

    version1 = repo.create_version(
        sit.id,
        entity_type="SSN",
        confidence="medium",
        source="scan-1",
        primary_element={"type": "regex", "value": "\\d{3}-\\d{2}-\\d{4}"},
        supporting_logic={"mode": "ANY"},
        supporting_groups=[
            {"name": "context", "items": [{"type": "keyword", "value": "social"}]}
        ],
    )
    version2 = repo.create_version(
        sit.id,
        entity_type="SSN",
        confidence="high",
        source="scan-2",
        primary_element={"type": "regex", "value": "\\d{3}-\\d{2}-\\d{4}"},
        supporting_logic={"mode": "ANY"},
        supporting_groups=[
            {"name": "context", "items": [{"type": "keyword", "value": "security"}]}
        ],
    )

    assert version1.version_number == 1
    assert version2.version_number == 2
