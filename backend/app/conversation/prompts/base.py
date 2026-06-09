"""Language-specific base prompt selection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, Protocol, cast

from app.conversation.prompts import base_en, base_sq

Lang = Literal["en", "sq"]


class BasePromptModule(Protocol):
    """Structural type for the base prompt modules (base_en / base_sq)."""

    VERSION: str
    ANTI_INJECTION: str
    build_base_prompt: Callable[[], str]


def get_base_module(lang: Lang) -> BasePromptModule:
    """Return the prompt module for the user's language."""
    if lang == "sq":
        return cast("BasePromptModule", base_sq)
    return cast("BasePromptModule", base_en)
