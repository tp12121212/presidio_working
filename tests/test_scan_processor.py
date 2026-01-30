from pathlib import Path

from common.db import SessionLocal, init_db
from ingestion.processor import FileProcessor, ProcessingStats, ScanOptions
from pii.engines import PIIEngines


def test_scan_processor_calls_presidio_analyze(tmp_path: Path, monkeypatch):
    called = {}

    def fake_analyze(self, text, entities=None, language="en", score_threshold=None):
        called["text"] = text
        called["entities"] = entities
        called["language"] = language
        called["score_threshold"] = score_threshold
        return []

    monkeypatch.setattr(PIIEngines, "analyze_text", fake_analyze)
    init_db()
    session = SessionLocal()
    try:
        sample = tmp_path / "sample.txt"
        sample.write_text("Hello SSN 123-45-6789", encoding="utf-8")
        options = ScanOptions(entities=["US_SSN"], language="en", score_threshold=0.5)
        processor = FileProcessor(session, "job-1", options)
        processor.process_path(sample, ProcessingStats(), virtual_path="sample.txt")
        assert called["entities"] == ["US_SSN"]
        assert called["score_threshold"] == 0.5
    finally:
        session.close()
