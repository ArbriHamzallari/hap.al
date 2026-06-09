"""Input sanitization before LLM and DB persistence (CLAUDE.md §9.3)."""

from __future__ import annotations

import re
import unicodedata

_MAX_LENGTH = 2000
_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_input(text: str) -> str:
    """Strip HTML, limit length, remove null bytes, normalize unicode (NFKC)."""
    cleaned = unicodedata.normalize("NFKC", text)
    cleaned = cleaned.replace("\x00", "")
    cleaned = _TAG_RE.sub("", cleaned)
    return cleaned[:_MAX_LENGTH]
