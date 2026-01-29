import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
create_engine = sqlalchemy.create_engine
sessionmaker = sqlalchemy.orm.sessionmaker

from common.db import Base
from purview.repository import RulepackRepository
from sit.repository import SitRepository


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_rulepack_selection_persists():
    session = create_session()
    sit_repo = SitRepository(session)
    rulepack_repo = RulepackRepository(session)

    sit = sit_repo.create_sit("Selection SIT", None)
    version = sit_repo.create_version(
        sit.id,
        entity_type="SSN",
        confidence="medium",
        source="scan",
        primary_element={"type": "regex", "value": "\\d{3}-\\d{2}-\\d{4}"},
        supporting_logic={"mode": "ANY"},
        supporting_groups=[
            {"name": "context", "items": [{"type": "keyword", "value": "social"}]}
        ],
    )

    rulepack = rulepack_repo.create_rulepack(
        "Selections", "1", None, None, None
    )
    rulepack_repo.set_selections(rulepack.id, [version.id])
    loaded = rulepack_repo.get_rulepack(rulepack.id)

    assert loaded is not None
    assert [selection.sit_version_id for selection in loaded.selections] == [version.id]
