"""Convert LLM markdown-style emphasis to Telegram HTML parse mode.

Telegram HTML supports a small tag set (<b>, <i>, <u>, <s>, <a>, <code>, <pre>). LLMs
emit markdown — we convert and escape everything else. The italic regexes are deliberately
strict about boundaries so they don't consume single asterisks used as bullets or
underscores used inside identifiers like `snake_case`.
"""

from __future__ import annotations

import re
from html import escape

# Null-byte sentinels so the italic pass doesn't see asterisks placed by the bold pass.
_B_OPEN = "\x00B\x00"
_B_CLOSE = "\x00/B\x00"
_I_OPEN = "\x00I\x00"
_I_CLOSE = "\x00/I\x00"

_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC_STAR = re.compile(r"(?<![*\w])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![*\w])")
_ITALIC_UNDER = re.compile(r"(?<![_\w])_(?!\s)([^_\n]+?)(?<!\s)_(?![_\w])")


def to_telegram_html(text: str) -> str:
    """Turn ``**bold**``, ``*italic*``, and ``_italic_`` into Telegram HTML tags."""
    if not text:
        return ""

    work = _BOLD.sub(lambda m: f"{_B_OPEN}{m.group(1)}{_B_CLOSE}", text)
    work = _ITALIC_STAR.sub(lambda m: f"{_I_OPEN}{m.group(1)}{_I_CLOSE}", work)
    work = _ITALIC_UNDER.sub(lambda m: f"{_I_OPEN}{m.group(1)}{_I_CLOSE}", work)

    work = escape(work)
    work = work.replace(_B_OPEN, "<b>").replace(_B_CLOSE, "</b>")
    work = work.replace(_I_OPEN, "<i>").replace(_I_CLOSE, "</i>")
    return work
