"""Load bilingual bot strings from JSON files."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

Lang = Literal["en", "sq"]

_STRINGS_DIR = Path(__file__).parent / "strings"


@lru_cache(maxsize=2)
def _load(lang: Lang) -> dict[str, Any]:
    path = _STRINGS_DIR / f"{lang}.json"
    with path.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def t(key: str, lang: Lang = "en", **kwargs: str) -> str:
    """Resolve a dotted key like `errors.generic` with optional format placeholders."""
    parts = key.split(".")
    node: Any = _load(lang)
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"missing i18n key {key!r} for lang {lang}")
        node = node[part]
    if not isinstance(node, str):
        raise KeyError(f"i18n key {key!r} is not a string")
    return node.format(**kwargs) if kwargs else node
