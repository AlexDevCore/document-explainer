"""Flask web app: paste an official letter, get a plain-language explanation."""

from flask import Flask, jsonify, render_template, request

from src.config import MAX_INPUT_CHARS
from src.explainer import explain_letter
from src.logger import get_logger

log = get_logger(__name__)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", max_chars=MAX_INPUT_CHARS)


@app.route("/explain", methods=["POST"])
def explain():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    language = (data.get("language") or "Spanish").strip()

    if not text:
        return jsonify({"error": "Please paste the text of a letter first."}), 400
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
