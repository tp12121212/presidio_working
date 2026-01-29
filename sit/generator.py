from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List

from presidio_analyzer import RecognizerResult

STOPWORDS = {"the", "and", "for", "with", "this", "that", "from"}


@dataclass
class SitDefinition:
    id: str
    name: str
    description: str | None
    primary_type: str
    primary_value: str
    supporting_type: str | None
    supporting_value: str | None
    proximity: int | None
    confidence: str
    entity_type: str
    source: str | None


def generate_sits_from_text(
    results: Iterable[RecognizerResult],
    text: str,
    source: str | None = None,
    window: int = 60,
) -> List[SitDefinition]:
    generated: List[SitDefinition] = []
    results_list = list(results)
    for result in results_list:
        generated.append(build_sit_for_entity(result, text, source=source, window=window))
    return generated


def build_sit_for_entity(
    entity: RecognizerResult, text: str, source: str | None, window: int
) -> SitDefinition:
    left = max(0, entity.start - window)
    right = min(len(text), entity.end + window)
    context = text[left:right].lower()
    entity_text = text[entity.start : entity.end]

    words = re.findall(r"[a-zA-Z]{3,}", context)
    filtered = [
        word
        for word in words
        if word not in STOPWORDS and word not in entity_text.lower()
    ]
    common = Counter(filtered).most_common(5)
    supporting = [word for word, _ in common]

    primary_regex = infer_regex_for_entity(entity.entity_type, entity_text)
    supporting_value = ",".join(supporting[:3]) if supporting else None

    return SitDefinition(
        id=str(uuid.uuid4()),
        name=f"{entity.entity_type}_custom",
        description=None,
        primary_type="regex",
        primary_value=primary_regex,
        supporting_type="keyword" if supporting_value else None,
        supporting_value=supporting_value,
        proximity=window if supporting_value else None,
        confidence=score_confidence(entity.score),
        entity_type=entity.entity_type,
        source=source,
    )


def infer_regex_for_entity(entity_type: str, value: str) -> str:
    patterns = {
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,19}\b",
        "PHONE_NUMBER": r"\b\+?\d[\d\s().-]{7,}\b",
        "EMAIL_ADDRESS": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }
    if entity_type in patterns:
        return patterns[entity_type]
    return _generalize_value_to_regex(value)


def _generalize_value_to_regex(value: str) -> str:
    tokens = []
    for char in value:
        if char.isdigit():
            tokens.append("\\d")
        elif char.isalpha():
            tokens.append("[A-Za-z]")
        elif char.isspace():
            tokens.append("\\s")
        else:
            tokens.append(re.escape(char))
    return "".join(tokens)


def score_confidence(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"
