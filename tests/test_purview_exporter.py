import xml.etree.ElementTree as ET

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
create_engine = sqlalchemy.create_engine
sessionmaker = sqlalchemy.orm.sessionmaker

from common.db import Base
from purview.exporter import NS, build_rule_package
from purview.models import Rulepack
from sit.repository import SitRepository


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_build_rule_package_structure_and_determinism():
    session = create_session()
    repo = SitRepository(session)

    sit_a = repo.create_sit("Alpha SIT", "first")
    repo.create_version(
        sit_a.id,
        entity_type="SSN",
        confidence="medium",
        source="scan",
        primary_element={"type": "regex", "value": "\\d{3}-\\d{2}-\\d{4}"},
        supporting_logic={"mode": "ANY"},
        supporting_groups=[
            {"name": "context", "items": [{"type": "keyword", "value": "social"}]}
        ],
    )

    keyword_list = repo.create_keyword_list("Cards", None, ["visa", "mastercard"])
    sit_b = repo.create_sit("Beta SIT", "second")
    repo.create_version(
        sit_b.id,
        entity_type="CREDIT_CARD",
        confidence="high",
        source="scan",
        primary_element={"type": "regex", "value": "\\d{4}-\\d{4}-\\d{4}-\\d{4}"},
        supporting_logic={"mode": "MIN_N", "min_n": 2},
        supporting_groups=[
            {
                "name": "brands",
                "items": [
                    {"type": "keyword_list", "keyword_list_id": keyword_list.id}
                ],
            }
        ],
    )

    versions = repo.get_versions_by_ids(
        [sit_a.versions[0].id, sit_b.versions[0].id]
    )
    rulepack = Rulepack(
        id="rulepack-1",
        name="Custom Pack",
        version="1",
        description="desc",
        publisher="publisher",
        locale="en-US",
    )
    xml_data = build_rule_package(rulepack, versions)
    root = ET.fromstring(xml_data)

    assert root.tag == f"{{{NS}}}RulePackage"
    rules = root.find(f"{{{NS}}}Rules")
    entities = list(rules.findall(f"{{{NS}}}Entity"))
    assert entities[0].attrib["name"] == "Alpha SIT"
    assert entities[1].attrib["name"] == "Beta SIT"

    supporting = entities[1].find(f"{{{NS}}}SupportingElements")
    assert supporting is not None
    assert supporting.attrib["mode"] == "MIN_N"
    assert supporting.attrib["minN"] == "2"
