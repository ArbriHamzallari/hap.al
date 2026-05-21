"""Parse out-of-band markers from LLM output: keyboard keys, reminders, trigger flags."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

_TIRANE = ZoneInfo("Europe/Tirane")

_BTN_PATTERN = re.compile(r"\[BTN:(financial|experience|time|day_job)\]", re.IGNORECASE)
_REMIND_PATTERN = re.compile(r"\[REMIND:([^|\]]+)\|([^\]]+)\]")
_ONBOARDING_DONE_PATTERN = re.compile(r"\[ONBOARDING_DONE\]", re.IGNORECASE)
_IDEA_DETECTED_PATTERN = re.compile(r"\[IDEA_DETECTED\]", re.IGNORECASE)


@dataclass(frozen=True)
class ScheduledReminder:
    when: datetime  # always timezone-aware
    message: str


@dataclass(frozen=True)
class ParsedReply:
    text: str
    button_key: str | None = None
    reminders: tuple[ScheduledReminder, ...] = field(default_factory=tuple)
    onboarding_done: bool = False
    idea_detected: bool = False


def parse_reply(raw: str) -> ParsedReply:
    """Strip markers from a raw LLM reply. Return cleaned text + parsed payloads + flags."""
    button_key: str | None = None
    reminders: list[ScheduledReminder] = []

    btn_match = _BTN_PATTERN.search(raw)
    if btn_match:
        button_key = btn_match.group(1).lower()

    for match in _REMIND_PATTERN.finditer(raw):
        when = _parse_when(match.group(1).strip())
        message = match.group(2).strip()
        if when is not None and message:
            reminders.append(ScheduledReminder(when=when, message=message))

    onboarding_done = bool(_ONBOARDING_DONE_PATTERN.search(raw))
    idea_detected = bool(_IDEA_DETECTED_PATTERN.search(raw))

    cleaned = _BTN_PATTERN.sub("", raw)
    cleaned = _REMIND_PATTERN.sub("", cleaned)
    cleaned = _ONBOARDING_DONE_PATTERN.sub("", cleaned)
    cleaned = _IDEA_DETECTED_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    return ParsedReply(
        text=cleaned,
        button_key=button_key,
        reminders=tuple(reminders),
        onboarding_done=onboarding_done,
        idea_detected=idea_detected,
    )


def _parse_when(value: str) -> datetime | None:
    """ISO 8601 datetime. Naive timestamps assume Europe/Tirane."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_TIRANE)
    return dt
