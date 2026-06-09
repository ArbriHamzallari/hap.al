"""Telegram webhook request verification (CLAUDE.md §9.2)."""

from __future__ import annotations

import secrets

from fastapi import Request


def _safe_compare(provided: str | None, expected: str) -> bool:
    if provided is None:
        return False
    return secrets.compare_digest(provided, expected)


def verify_telegram_webhook(request: Request, expected_secret: str) -> bool:
    """Return True when the X-Telegram-Bot-Api-Secret-Token header matches."""
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    return _safe_compare(token, expected_secret)


def verify_internal_cron(request: Request, expected_secret: str) -> bool:
    """Return True when the internal cron bearer token matches."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return _safe_compare(auth.removeprefix("Bearer ").strip(), expected_secret)
    return _safe_compare(request.headers.get("X-Internal-Cron-Secret"), expected_secret)
