import pytest

from src import explainer
from src.app import app
from src.config import MAX_INPUT_CHARS


@pytest.fixture
def client(monkeypatch):
    # Force demo mode so tests never make a real API call.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(explainer, "load_environment", lambda: False)
    app.config.update(TESTING=True)
    return app.test_client()


def test_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Letter Explainer" in r.data


def test_explain_rejects_empty(client):
    r = client.post("/explain", json={"text": "  ", "language": "Spanish"})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_explain_rejects_too_long(client):
    r = client.post(
        "/explain",
        json={"text": "x" * (MAX_INPUT_CHARS + 1), "language": "Spanish"},
    )
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_explain_returns_demo(client):
    r = client.post("/explain", json={"text": "A DMV notice.", "language": "Russian"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["demo"] is True
    assert "Russian" in data["translation"]


def test_explain_file_demo(client):
    r = client.post(
        "/explain",
        json={
            "file_data": "QUJD",
            "file_media_type": "image/png",
            "language": "Spanish",
        },
    )
    assert r.status_code == 200
    assert r.get_json()["demo"] is True


def test_explain_file_rejects_bad_type(client):
    r = client.post(
        "/explain",
        json={
            "file_data": "QUJD",
            "file_media_type": "application/zip",
            "language": "Spanish",
        },
    )
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_explain_file_rejects_too_large(client):
    from src.config import MAX_FILE_BYTES

    big = "A" * (MAX_FILE_BYTES * 2)  # base64 decodes to ~1.5x MAX
    r = client.post(
        "/explain",
        json={"file_data": big, "file_media_type": "image/jpeg", "language": "Spanish"},
    )
    assert r.status_code == 400
    assert "error" in r.get_json()
