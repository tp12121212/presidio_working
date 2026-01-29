import pytest

pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from app.main import app


def test_scan_requires_input():
    client = TestClient(app)
    response = client.post("/scan")
    assert response.status_code == 400
