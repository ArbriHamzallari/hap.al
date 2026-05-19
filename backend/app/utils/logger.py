"""Structured JSON logging and the PII-safe telegram_id hasher.

CLAUDE.md §9.7 / §10:
- NEVER log message content, API keys, decrypted user data, or raw telegram_id.
- ALWAYS log timestamps, hashed telegram_id, endpoint, response status, error IDs, latency.
"""

from __future__ import annotations

import hashlib
import logging

from pythonjsonlogger.json import JsonFormatter

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    """Install a JSON formatter on the root logger. Call once at process start."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "ts"},
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())


def hash_telegram_id(telegram_id: int, settings: Settings) -> str:
    """Stable, non-reversible 16-char hash for log lines and analytics."""
    salt = settings.telegram_id_hash_salt.get_secret_value()
    return hashlib.sha256(f"{salt}:{telegram_id}".encode()).hexdigest()[:16]
