"""Core logic: turn an official letter into a plain-language explanation.

Falls back to a demo response when ANTHROPIC_API_KEY is not set, so the whole
app stays runnable (and the UI testable) before a key is available.
"""

import json
import re
from pathlib import Path

from anthropic import Anthropic

from src.config import MODEL, get_env, load_environment
from src.logger import get_logger

log = get_logger(__name__)

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "explainer_system.txt"
)

# Shape every response follows, so the frontend can rely on these four keys.
KEYS = ("summary", "actions", "consequences", "translation")


def _load_system_prompt(language: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace("{LANGUAGE}", language)


def _demo_response(language: str) -> dict:
    """Returned when no API key is set — lets us test the UI without spending anything."""
    return {
        "summary": "[DEMO — no API key yet] This is a notice from the DMV about renewing "
        "your vehicle registration.",
        "actions": "[DEMO] Renew your registration by March 15, 2026. You can do it online "
        "at dmv.ca.gov or by mail using the enclosed form.",
        "consequences": "[DEMO] If you miss the deadline, you may have to pay a late fee and "
        "driving with expired registration can lead to a ticket.",
        "translation": f"[DEMO] (This is where the summary and actions appear in {language}.)",
        "demo": True,
    }


def _parse(raw: str) -> dict:
    """Extract the JSON object from the model reply, tolerant of stray text/fences."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        log.warning("No JSON found in model reply")
        return {k: "" for k in KEYS} | {
            "summary": "Could not read the response. Please try again."
        }
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        log.warning("Model reply was not valid JSON")
        return {k: "" for k in KEYS} | {
            "summary": "Could not read the response. Please try again."
        }
    # Guarantee all keys exist so the frontend never breaks.
    return {k: data.get(k, "") for k in KEYS}


def explain_letter(letter_text: str, target_language: str) -> dict:
    """Explain one official letter. Returns a dict with KEYS (+ optional 'demo')."""
    load_environment()
    api_key = get_env("ANTHROPIC_API_KEY")
    if not api_key:
        log.info("ANTHROPIC_API_KEY not set - returning demo response")
        return _demo_response(target_language)

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=_load_system_prompt(target_language),
        messages=[{"role": "user", "content": letter_text}],
    )
    return _parse(message.content[0].text)
