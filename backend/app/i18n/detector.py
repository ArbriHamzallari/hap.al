"""Map Telegram language codes and first messages to `en` or `sq` (CLAUDE.md §15)."""

from __future__ import annotations

from typing import Literal

from lingua import Language, LanguageDetectorBuilder

Lang = Literal["en", "sq"]

_DETECTOR = (
    LanguageDetectorBuilder.from_languages(Language.ENGLISH, Language.ALBANIAN)
    .with_preloaded_language_models()
    .build()
)

_SQ_CODES = frozenset({"sq", "al"})


def language_from_telegram_code(code: str | None) -> Lang | None:
    """Return `sq` or `en` when the BCP-47 code is unambiguous, else None."""
    if not code:
        return None
    root = code.lower().split("-")[0]
    if root in _SQ_CODES:
        return "sq"
    if root == "en":
        return "en"
    return None


def detect_from_text(text: str) -> Lang | None:
    """Detect language from message text. Returns None if confidence is low."""
    if not text or not text.strip():
        return None
    result = _DETECTOR.detect_language_of(text)
    if result is None:
        return None
    if result == Language.ALBANIAN:
        return "sq"
    if result == Language.ENGLISH:
        return "en"
    return None


def resolve_language(
    *,
    stored: str | None,
    telegram_code: str | None,
    first_message: str | None,
    default: Lang = "en",
) -> Lang:
    """Apply precedence: explicit stored > Telegram code > text detection > default."""
    if stored in ("en", "sq"):
        return stored  # type: ignore[return-value]
    from_code = language_from_telegram_code(telegram_code)
    if from_code is not None:
        return from_code
    from_text = detect_from_text(first_message or "")
    if from_text is not None:
        return from_text
    return default
