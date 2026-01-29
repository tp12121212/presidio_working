from __future__ import annotations

import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable

from purview.models import Rulepack
from sit.models import KeywordList, SITSupportingItem, SITSupportingLogic, SITVersion

NS = "https://schemas.microsoft.com/office/2011/mce"
ET.register_namespace("", NS)


class ExportValidationError(ValueError):
    pass


@dataclass
class ExportContext:
    rulepack: Rulepack
    versions: list[SITVersion]


def build_rule_package(rulepack: Rulepack, versions: Iterable[SITVersion]) -> bytes:
    context = ExportContext(rulepack=rulepack, versions=sorted_versions(versions))
    validate_context(context)

    rule_package = ET.Element(
        f"{{{NS}}}RulePackage",
        {
            "id": rulepack.id or str(uuid.uuid4()),
            "name": rulepack.name,
            "version": rulepack.version,
            "description": rulepack.description or "",
            "publisher": rulepack.publisher or "",
            "locale": rulepack.locale or "",
        },
    )

    rules = ET.SubElement(rule_package, f"{{{NS}}}Rules")

    for version in context.versions:
        sit_name = version.sit.name if version.sit else version.sit_id
        entity = ET.SubElement(
            rules,
            f"{{{NS}}}Entity",
            {
                "id": version.id,
                "name": sit_name,
                "description": version.sit.description if version.sit else "",
                "recommendedConfidence": version.confidence or "medium",
            },
        )

        primary_type = "Regex" if version.primary_element.element_type == "regex" else "Keyword"
        ET.SubElement(
            entity,
            f"{{{NS}}}Pattern",
            {
                "type": primary_type,
                "value": version.primary_element.value,
            },
        )

        if version.supporting_groups:
            supporting_root = ET.SubElement(
                entity,
                f"{{{NS}}}SupportingElements",
                supporting_attributes(version.supporting_logic),
            )
            for group in version.supporting_groups:
                for item in group.items:
                    item_type, value = resolve_supporting_item(item)
                    ET.SubElement(
                        supporting_root,
                        f"{{{NS}}}SupportingElement",
                        {
                            "type": item_type,
                            "value": value,
                            "group": group.name,
                        },
                    )

    return ET.tostring(rule_package, encoding="utf-8", xml_declaration=True)


def sorted_versions(versions: Iterable[SITVersion]) -> list[SITVersion]:
    return sorted(
        list(versions),
        key=lambda v: (
            v.sit.name if v.sit else "",
            v.version_number,
            v.id,
        ),
    )


def supporting_attributes(logic: SITSupportingLogic) -> dict:
    attributes = {"mode": logic.mode}
    if logic.mode == "MIN_N":
        attributes["minN"] = str(logic.min_n or 1)
    return attributes


def resolve_supporting_item(item: SITSupportingItem) -> tuple[str, str]:
    if item.item_type == "keyword_list":
        keyword_list = item.keyword_list
        values = [entry.value for entry in keyword_list.items] if keyword_list else []
        return "Keyword", ",".join(values)
    if item.item_type == "regex":
        return "Regex", item.value or ""
    return "Keyword", item.value or ""


def validate_context(context: ExportContext) -> None:
    if not context.versions:
        raise ExportValidationError("No SIT versions selected for export.")

    for version in context.versions:
        if not version.primary_element:
            raise ExportValidationError(
                f"SIT version {version.id} is missing a primary element."
            )

        _validate_primary(version)
        _validate_supporting(version)


def _validate_primary(version: SITVersion) -> None:
    primary = version.primary_element
    if primary.element_type == "regex":
        _validate_regex(primary.value, f"Primary regex invalid for {version.id}.")
    if primary.element_type == "keyword" and not primary.value:
        raise ExportValidationError(f"Primary keyword missing for {version.id}.")


def _validate_supporting(version: SITVersion) -> None:
    logic = version.supporting_logic
    groups = version.supporting_groups
    if logic and logic.mode in {"ALL", "MIN_N", "ANY"}:
        if not groups:
            raise ExportValidationError(
                f"Supporting groups required for {version.id} but none provided."
            )

    if logic and logic.mode == "MIN_N":
        if not logic.min_n or logic.min_n < 1:
            raise ExportValidationError(
                f"MIN_N requires min_n >= 1 for {version.id}."
            )

    for group in groups:
        if not group.items:
            raise ExportValidationError(f"Supporting group {group.name} is empty.")
        for item in group.items:
            if item.item_type == "regex":
                _validate_regex(item.value or "", f"Invalid supporting regex in {version.id}.")
            if item.item_type == "keyword" and not item.value:
                raise ExportValidationError(
                    f"Empty supporting keyword in {version.id}."
                )
            if item.item_type == "keyword_list":
                _validate_keyword_list(item.keyword_list, version.id)


def _validate_keyword_list(keyword_list: KeywordList | None, version_id: str) -> None:
    if not keyword_list or not keyword_list.items:
        raise ExportValidationError(
            f"Keyword list missing or empty for {version_id}."
        )


def _validate_regex(pattern: str, message: str) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ExportValidationError(message) from exc
