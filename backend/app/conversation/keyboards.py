"""Inline keyboard builders for structured onboarding choices (CLAUDE.md §6)."""

from __future__ import annotations

from typing import Any, Literal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

Lang = Literal["en", "sq"]

# callback_data -> label sent to the LLM as the user's answer
CALLBACK_LABELS: dict[str, str] = {
    "fin:tight": "Tight right now",
    "fin:comfortable": "Comfortable",
    "fin:savings": "Have savings",
    "fin:investment": "Have investment money",
    "exp:none": "Never built anything",
    "exp:beginner": "Tried once or twice",
    "exp:experienced": "Built things before",
    "time:few": "Few hours per week",
    "time:part": "Part-time",
    "time:full": "Full-time",
    "job:yes": "Yes, I have a day job",
    "job:no": "No day job",
    "job:freelance": "Freelance / varied income",
}

# callback_data -> (users column, value). Used to persist structured answers when a
# button is tapped. Free-text answers don't go through here.
# `job:freelance` is intentionally absent — the schema's has_day_job is a plain boolean
# that can't express "varied", so we let the LLM read the label from conversation history.
CALLBACK_FIELD_VALUES: dict[str, tuple[str, Any]] = {
    "fin:tight": ("financial_situation", "tight"),
    "fin:comfortable": ("financial_situation", "comfortable"),
    "fin:savings": ("financial_situation", "has_savings"),
    "fin:investment": ("financial_situation", "has_investment"),
    "exp:none": ("experience_level", "none"),
    "exp:beginner": ("experience_level", "beginner"),
    "exp:experienced": ("experience_level", "experienced"),
    "time:few": ("time_availability", "few_hours_week"),
    "time:part": ("time_availability", "part_time"),
    "time:full": ("time_availability", "full_time"),
    "job:yes": ("has_day_job", True),
    "job:no": ("has_day_job", False),
}


_FINANCIAL = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Tight right now", callback_data="fin:tight")],
        [InlineKeyboardButton("Comfortable", callback_data="fin:comfortable")],
        [InlineKeyboardButton("Have savings", callback_data="fin:savings")],
        [InlineKeyboardButton("Have investment money", callback_data="fin:investment")],
    ]
)

_EXPERIENCE = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Never built anything", callback_data="exp:none")],
        [InlineKeyboardButton("Tried once or twice", callback_data="exp:beginner")],
        [InlineKeyboardButton("Built things before", callback_data="exp:experienced")],
    ]
)

_TIME = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Few hours/week", callback_data="time:few")],
        [InlineKeyboardButton("Part-time", callback_data="time:part")],
        [InlineKeyboardButton("Full-time", callback_data="time:full")],
    ]
)

_DAY_JOB = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Yes", callback_data="job:yes")],
        [InlineKeyboardButton("No", callback_data="job:no")],
        [InlineKeyboardButton("Freelance / varied", callback_data="job:freelance")],
    ]
)

_KEYBOARDS_EN: dict[str, InlineKeyboardMarkup] = {
    "financial": _FINANCIAL,
    "experience": _EXPERIENCE,
    "time": _TIME,
    "day_job": _DAY_JOB,
}

_FINANCIAL_SQ = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Situatë e ngurtë", callback_data="fin:tight")],
        [InlineKeyboardButton("Komode", callback_data="fin:comfortable")],
        [InlineKeyboardButton("Kam kursime", callback_data="fin:savings")],
        [InlineKeyboardButton("Kam para investimi", callback_data="fin:investment")],
    ]
)

_EXPERIENCE_SQ = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("S'kam ndërtuar asgjë", callback_data="exp:none")],
        [InlineKeyboardButton("Kam provuar 1-2 herë", callback_data="exp:beginner")],
        [InlineKeyboardButton("Kam ndërtuar më parë", callback_data="exp:experienced")],
    ]
)

_TIME_SQ = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Pak orë/javë", callback_data="time:few")],
        [InlineKeyboardButton("Me kohë të pjesshme", callback_data="time:part")],
        [InlineKeyboardButton("Me kohë të plotë", callback_data="time:full")],
    ]
)

_DAY_JOB_SQ = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Po", callback_data="job:yes")],
        [InlineKeyboardButton("Jo", callback_data="job:no")],
        [InlineKeyboardButton("Freelance / i ndryshueshëm", callback_data="job:freelance")],
    ]
)

_KEYBOARDS_SQ: dict[str, InlineKeyboardMarkup] = {
    "financial": _FINANCIAL_SQ,
    "experience": _EXPERIENCE_SQ,
    "time": _TIME_SQ,
    "day_job": _DAY_JOB_SQ,
}


def get_keyboard(key: str | None, lang: Lang = "en") -> InlineKeyboardMarkup | None:
    """Return the inline keyboard for a structured question, or None."""
    if key is None:
        return None
    boards = _KEYBOARDS_SQ if lang == "sq" else _KEYBOARDS_EN
    return boards.get(key)


def label_for_callback(callback_data: str) -> str | None:
    """Map callback_data to human-readable text for the conversation engine."""
    return CALLBACK_LABELS.get(callback_data)


def field_for_callback(callback_data: str) -> tuple[str, Any] | None:
    """Map callback_data to (users column name, value) for DB persistence."""
    return CALLBACK_FIELD_VALUES.get(callback_data)
