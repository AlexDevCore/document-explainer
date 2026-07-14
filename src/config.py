"""Basic project configuration and environment helpers."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_NAME = "document-explainer"

# Claude model used for explanations (quality matters for official letters).
MODEL = "claude-sonnet-5"

# Max characters accepted from the user (guards against runaway token cost).
MAX_INPUT_CHARS = 8000

# File upload limits.
ALLOWED_FILE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
}
MAX_FILE_BYTES = 8 * 1024 * 1024  # 8 MB (after base64 decode)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def env_file_exists() -> bool:
    return ENV_FILE.exists()


def load_environment() -> bool:
    """Load key=value pairs from .env into the process environment.

    Does nothing (and returns False) if .env does not exist, so this is
    safe to call in every environment, including CI where .env is absent.
    """
    return load_dotenv(ENV_FILE)


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)
