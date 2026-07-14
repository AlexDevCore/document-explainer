from src import explainer
from src.explainer import KEYS, _build_content, _parse, explain_letter


def test_build_content_text():
    assert _build_content("hello", None, None) == "hello"


def test_build_content_image():
    content = _build_content("", "BASE64DATA", "image/png")
    assert content[0]["type"] == "image"
    assert content[0]["source"]["media_type"] == "image/png"
    assert content[0]["source"]["data"] == "BASE64DATA"


def test_build_content_pdf():
    content = _build_content("", "BASE64DATA", "application/pdf")
    assert content[0]["type"] == "document"
    assert content[0]["source"]["media_type"] == "application/pdf"


def test_demo_response_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Make sure a real .env on disk doesn't slip a key in during the test.
    monkeypatch.setattr(explainer, "load_environment", lambda: False)

    result = explain_letter("Some official letter text.", "Russian")

    for key in KEYS:
        assert key in result
    assert result.get("demo") is True
    assert "Russian" in result["translation"]


def test_parse_extracts_json_with_fences():
    raw = '```json\n{"summary": "a", "actions": "b", "consequences": "c", "translation": "d"}\n```'
    data = _parse(raw)
    assert data == {
        "summary": "a",
        "actions": "b",
        "consequences": "c",
        "translation": "d",
    }


def test_parse_fills_missing_keys():
    data = _parse('{"summary": "only summary"}')
    assert data["summary"] == "only summary"
    for key in KEYS:
        assert key in data


def test_parse_handles_garbage():
    data = _parse("not json at all")
    for key in KEYS:
        assert key in data
