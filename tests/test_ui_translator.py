from src import ui_translator
from src.i18n import UI_STRINGS
from src.ui_translator import translate_ui


def test_falls_back_to_english_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(ui_translator, "load_environment", lambda: False)
    ui_translator._cache.clear()

    result = translate_ui("Klingon")

    assert result == UI_STRINGS["en"]


def test_empty_language_returns_english(monkeypatch):
    monkeypatch.setattr(ui_translator, "load_environment", lambda: False)
    assert translate_ui("") == UI_STRINGS["en"]
    assert translate_ui("   ") == UI_STRINGS["en"]


def test_no_key_fallback_is_not_cached(monkeypatch):
    # Without a key we return the English fallback but deliberately don't cache it,
    # so a real translation still happens once a key becomes available.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(ui_translator, "load_environment", lambda: False)
    ui_translator._cache.clear()

    translate_ui("Klingon")
    assert "klingon" not in ui_translator._cache


def test_successful_translation_is_cached(monkeypatch):
    class FakeBlock:
        type = "text"
        text = '{"explain_btn": "Explique"}'

    class FakeMessage:
        content = [FakeBlock()]

    class FakeMessages:
        def create(self, **kwargs):
            return FakeMessage()

    class FakeClient:
        def __init__(self, api_key=None):
            self.messages = FakeMessages()

    monkeypatch.setattr(ui_translator, "load_environment", lambda: True)
    monkeypatch.setattr(ui_translator, "get_env", lambda key: "fake-key")
    monkeypatch.setattr(ui_translator, "Anthropic", FakeClient)
    ui_translator._cache.clear()

    result = translate_ui("Klingon")

    assert result["explain_btn"] == "Explique"
    # Untranslated keys fall back to English per-key.
    assert result["copy_btn"] == UI_STRINGS["en"]["copy_btn"]
    assert "klingon" in ui_translator._cache
