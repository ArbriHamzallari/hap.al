"""Shared date formatting for bot command replies."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.i18n.loader import Lang, t


def describe_due(iso_value: Any, lang: Lang = "en") -> str:
    """Human relative due-date in the user's language (e.g. 'due in 3h')."""
    if not iso_value:
        return t("dates.no_due", lang)
    try:
        when = datetime.fromisoformat(str(iso_value))
    except ValueError:
        return t("dates.no_due", lang)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    delta = when - datetime.now(UTC)
    minutes = int(delta.total_seconds() // 60)
    if minutes < -60 * 24:
        return t("dates.due_ago", lang, n=str(-minutes // (60 * 24)))
    if minutes < 0:
        return t("dates.due_now", lang)
    if minutes < 60:
        return t("dates.due_in_min", lang, n=str(minutes))
    if minutes < 60 * 24:
        return t("dates.due_in_hr", lang, n=str(minutes // 60))
    return t("dates.due_in_day", lang, n=str(minutes // (60 * 24)))


def format_event_when(iso_value: Any) -> str:
    """Compact, language-neutral timestamp for journey timelines (e.g. '26/05 14:30')."""
    if not iso_value:
        return "—"
    try:
        when = datetime.fromisoformat(str(iso_value))
    except ValueError:
        return "—"
    return when.strftime("%d/%m %H:%M")
