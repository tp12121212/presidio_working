from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List

from presidio_analyzer import RecognizerResult

STOPWORDS = {"the", "and", "for", "with", "this", "that", "from"}


@dataclass
class FindingCandidate:
    entity_type: str
    score: float
    start: int
    end: int
    context: str
    primary_regex: str
    supporting_keywords: list[str]


def generate_findings_from_text(
    results: Iterable[RecognizerResult],
    text: str,
    window: int = 60,
) -> List[FindingCandidate]:
    candidates: List[FindingCandidate] = []
    for result in list(results):
        candidates.append(build_candidate(result, text, window=window))
    return candidates


def build_candidate(
    entity: RecognizerResult, text: str, window: int
) -> FindingCandidate:
    left = max(0, entity.start - window)
    right = min(len(text), entity.end + window)
    context_raw = text[left:right]
    entity_text = text[entity.start : entity.end]
    context = _redact_context(context_raw, entity_text)

    words = re.findall(r"[a-zA-Z]{3,}", context_raw.lower())
    filtered = [
        word
        for word in words
        if word not in STOPWORDS and word not in entity_text.lower()
    ]
    common = Counter(filtered).most_common(5)
    supporting = [word for word, _ in common]

    primary_regex = infer_regex_for_entity(entity.entity_type, entity_text)

    return FindingCandidate(
        entity_type=entity.entity_type,
        score=entity.score,
        start=entity.start,
        end=entity.end,
        context=context,
        primary_regex=primary_regex,
        supporting_keywords=supporting[:5],
    )


def _redact_context(context: str, value: str) -> str:
    if not value:
        return context
    return context.replace(value, "[REDACTED]")


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
