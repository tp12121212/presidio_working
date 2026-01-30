import io
import pytest

pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from app.main import app


def test_scan_file_passes_options(monkeypatch, tmp_path):
    captured = {}

    def fake_delay(job_id, path, options=None, virtual_root=None, root_dir=None):
        captured["options"] = options
        return None

    monkeypatch.setattr("app.main.scan_file_job.delay", fake_delay)

    client = TestClient(app)
    payload = {
        "file": ("sample.txt", io.BytesIO(b"hello"), "text/plain"),
        "entity_types": (None, "PERSON,EMAIL"),
        "threshold": (None, "0.4"),
        "language": (None, "en"),
        "ocr_mode": (None, "auto"),
        "include_headers": (None, "true"),
        "parse_html": (None, "false"),
        "include_attachments": (None, "true"),
        "include_inline_images": (None, "false"),
    }

    response = client.post("/scan/file", files=payload)
    assert response.status_code == 200
    assert captured["options"]["entities"] == ["PERSON", "EMAIL"]
    assert captured["options"]["score_threshold"] == 0.4
    assert captured["options"]["include_headers"] is True
    assert captured["options"]["parse_html"] is False
    assert captured["options"]["include_attachments"] is True
    assert captured["options"]["include_inline_images"] is False
