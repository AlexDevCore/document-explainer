"""Flask web app: paste an official letter, get a plain-language explanation."""

from flask import Flask, Response, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.config import ALLOWED_FILE_TYPES, MAX_FILE_BYTES, MAX_INPUT_CHARS
from src.explainer import explain_letter
from src.i18n import LANGUAGE_ENGLISH_NAME, LANGUAGE_OPTIONS, RTL_CODES, UI_STRINGS
from src.logger import get_logger
from src.ui_translator import translate_ui

log = get_logger(__name__)

app = Flask(__name__)

# Protects the Anthropic budget from a single abusive client hammering /explain.
limiter = Limiter(get_remote_address, app=app, default_limits=[])


@app.route("/")
def index():
    return render_template(
        "index.html",
        max_chars=MAX_INPUT_CHARS,
        max_file_bytes=MAX_FILE_BYTES,
        ui_strings=UI_STRINGS,
        language_options=LANGUAGE_OPTIONS,
        language_english_name=LANGUAGE_ENGLISH_NAME,
        rtl_codes=list(RTL_CODES),
    )


@app.route("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\nSitemap: https://document-explainer-production.up.railway.app/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url><loc>https://document-explainer-production.up.railway.app/</loc></url>\n"
        "</urlset>\n"
    )
    return Response(body, mimetype="application/xml")


@app.route("/translate-ui", methods=["POST"])
@limiter.limit("10 per minute; 30 per day")
def translate_ui_route():
    data = request.get_json(silent=True) or {}
    language_name = (data.get("language") or "").strip()
    if not language_name:
        return jsonify({"error": "Missing language name."}), 400
    strings = translate_ui(language_name)
    return jsonify({"strings": strings})


def _handle_file(data, language):
    """Validate an uploaded file and return a Flask response, or None if invalid inputs handled."""
    file_data = data.get("file_data") or ""
    file_media_type = (data.get("file_media_type") or "").strip()

    if file_media_type not in ALLOWED_FILE_TYPES:
        return (
            jsonify(
                {"error": "Unsupported file type. Use a JPG, PNG, WebP, GIF or PDF."}
            ),
            400,
        )
    # base64 decodes to ~3/4 of its length in bytes.
    approx_bytes = len(file_data) * 3 // 4
    if approx_bytes > MAX_FILE_BYTES:
        mb = MAX_FILE_BYTES // (1024 * 1024)
        return jsonify({"error": f"File is too large (max {mb} MB)."}), 400

    result = explain_letter(
        target_language=language, file_data=file_data, file_media_type=file_media_type
    )
    if "error" in result:
        return jsonify(result), 502
    return jsonify(result)


@app.route("/explain", methods=["POST"])
@limiter.limit("10 per minute; 50 per day")
def explain():
    data = request.get_json(silent=True) or {}
    language = (data.get("language") or "English").strip()

    # File upload path takes precedence if a file is present.
    if data.get("file_data"):
        return _handle_file(data, language)

    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Please paste a letter or upload a file first."}), 400
    if len(text) > MAX_INPUT_CHARS:
        return (
            jsonify(
                {
                    "error": f"Letter is too long (max {MAX_INPUT_CHARS} characters). Please shorten it."
                }
            ),
            400,
        )

    result = explain_letter(text, language)
    if "error" in result:
        return jsonify(result), 502
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
