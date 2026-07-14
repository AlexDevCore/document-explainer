"""Translate the UI strings into a language the user typed themselves.

Popular languages are pre-translated in i18n.py (free, instant). This module
handles the "Other…" case: one Claude call per new language, cached in memory
so the same language is never translated twice.
"""

import json
import re

from anthropic import Anthropic, APIError

from src.i18n import UI_STRINGS
from src.config import MODEL, get_env, load_environment
from src.logger import get_logger

log = get_logger(__name__)

# In-memory cache: {language_name_lowercased: translated_dict}. Fine for a single
# gunicorn worker (see Procfile); resets on redeploy, which is an acceptable cost.
_cache: dict[str, dict] = {}

_ENGLISH_KEYS = UI_STRINGS["en"]


def _extract_text(message) -> str:
    return "".join(
        block.text
        for block in message.content
        if getattr(block, "type", None) == "text"
    )


def translate_ui(language_name: str) -> dict:
    """Return a dict with the same keys as UI_STRINGS['en'], translated into
    `language_name`. Falls back to English strings if no API key or on error.
    """
    key = language_name.strip().lower()
    if not key:
        return _ENGLISH_KEYS
    if key in _cache:
        return _cache[key]

    load_environment()
    api_key = get_env("ANTHROPIC_API_KEY")
    if not api_key:
        log.info(
            "ANTHROPIC_API_KEY not set - returning English UI strings for %s",
            language_name,
        )
        return _ENGLISH_KEYS

    prompt = (
        "Translate the values of this JSON object into "
        + language_name
        + ". Keep the keys exactly the same. Keep placeholders like {max} and {mb} "
        "unchanged. Do not translate proper nouns like DMV, IRS, JPG, PNG, WebP, GIF, PDF. "
        "Respond with ONLY the translated JSON object, no markdown, no commentary.\n\n"
        + json.dumps(_ENGLISH_KEYS, ensure_ascii=False)
    )

    client = Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
    except APIError as exc:
        log.error("Claude API error translating UI: %s", exc)
        return _ENGLISH_KEYS

    raw = _extract_text(message)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        log.warning("No JSON found translating UI into %s", language_name)
        return _ENGLISH_KEYS
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        log.warning("Invalid JSON translating UI into %s", language_name)
        return _ENGLISH_KEYS

    # Guarantee every key exists, falling back to English per-key if one is missing.
    result = {k: data.get(k, _ENGLISH_KEYS[k]) for k in _ENGLISH_KEYS}
    _cache[key] = result
    return result
