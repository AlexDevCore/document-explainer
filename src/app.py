"""Flask web app: paste an official letter, get a plain-language explanation."""

from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src.config import ALLOWED_FILE_TYPES, MAX_FILE_BYTES, MAX_INPUT_CHARS
from src.explainer import explain_letter
from src.logger import get_logger

log = get_logger(__name__)

app = Flask(__name__)

# Protects the Anthropic budget from a single abusive client hammering /explain.
limiter = Limiter(get_remote_address, app=app, default_limits=[])


@app.route("/")
def index():
    return render_template(
        "index.html", max_chars=MAX_INPUT_CHARS, max_file_bytes=MAX_FILE_BYTES
    )


def _handle_file(data, language):
    """Validate an uploaded file and return a Flask response, or None if invalid inputs handled."""
    file_data = data.get("file_data") or ""
    file_media_type = (data.get("file_media_type") or "").strip()

    if file_media_type not in ALLOWED_FILE_TYPES:
        return jsonify(
            {"error": "Unsupported file type. Use a JPG, PNG, WebP, GIF or PDF."}
        ), 400
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
    language = (data.get("language") or "Spanish").strip()

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
