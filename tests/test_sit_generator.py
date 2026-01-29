import pytest

presidio_analyzer = pytest.importorskip("presidio_analyzer")
RecognizerResult = presidio_analyzer.RecognizerResult

from findings.generator import build_candidate


def test_build_candidate_redacts_context_and_extracts_keywords():
    text = "Employee SSN is 123-45-6789 and social security number should be masked."
    entity = RecognizerResult(
        entity_type="SSN",
        start=16,
        end=27,
        score=0.7,
    )
    candidate = build_candidate(entity, text, window=40)
    assert "[REDACTED]" in candidate.context
    assert "social" in candidate.supporting_keywords
    assert "\\d{3}-\\d{2}-\\d{4}" in candidate.primary_regex
