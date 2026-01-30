import pytest

pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from app.main import app


def test_presidio_entities_endpoint(monkeypatch):
    class FakeEngine:
        def get_supported_entities(self, language="en"):
            return {"PERSON", "EMAIL_ADDRESS"}

    class FakeEngines:
        text_engine = FakeEngine()

    monkeypatch.setattr("app.main.PIIEngines", lambda: FakeEngines())

    client = TestClient(app)
    response = client.get("/presidio/entities")
    assert response.status_code == 200
    assert response.json() == ["EMAIL_ADDRESS", "PERSON"]
