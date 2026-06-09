"""Tests for parse_reply: button keys, reminders, trigger flags, cleanup."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.conversation.markers import parse_reply

_TIRANE = ZoneInfo("Europe/Tirane")


def test_no_markers() -> None:
    result = parse_reply("Just a regular message.")
    assert result.text == "Just a regular message."
    assert result.button_key is None
    assert result.reminders == ()
    assert result.onboarding_done is False
    assert result.idea_detected is False
    assert result.homework_done is False
    assert result.homework_skipped is False
    assert result.validate is False


def test_button_marker_stripped() -> None:
    result = parse_reply("How's your money situation?\n[BTN:financial]")
    assert result.text == "How's your money situation?"
    assert result.button_key == "financial"


def test_button_marker_case_insensitive() -> None:
    result = parse_reply("Question?\n[btn:experience]")
    assert result.button_key == "experience"


def test_unknown_button_marker_ignored() -> None:
    result = parse_reply("Q?\n[BTN:not_a_known_key]")
    assert result.button_key is None
    assert "[BTN:not_a_known_key]" in result.text


def test_reminder_naive_assumes_tirane() -> None:
    raw = "Cool.\n[REMIND:2026-05-21T15:00:00|Talk to anyone yet?]"
    result = parse_reply(raw)
    assert result.text == "Cool."
    assert len(result.reminders) == 1
    r = result.reminders[0]
    assert r.message == "Talk to anyone yet?"
    assert r.when == datetime(2026, 5, 21, 15, 0, tzinfo=_TIRANE)


def test_reminder_with_explicit_tz_preserved() -> None:
    raw = "[REMIND:2026-05-21T15:00:00+00:00|Check in]"
    result = parse_reply(raw)
    r = result.reminders[0]
    assert r.when.tzinfo is not None
    assert r.when.utcoffset() == timedelta(0)


def test_reminder_invalid_datetime_dropped() -> None:
    raw = "Sure.\n[REMIND:not-a-date|message]"
    result = parse_reply(raw)
    assert result.reminders == ()
    assert "[REMIND" not in result.text


def test_both_button_and_reminder() -> None:
    raw = "Cool.\n[BTN:time]\n[REMIND:2026-12-31T09:00:00|Year-end check]"
    result = parse_reply(raw)
    assert result.button_key == "time"
    assert len(result.reminders) == 1
    assert result.reminders[0].message == "Year-end check"


def test_excess_newlines_collapsed() -> None:
    raw = "Hello\n\n\n\n[BTN:financial]\n\n\nWorld"
    result = parse_reply(raw)
    assert "\n\n\n" not in result.text


def test_utc_datetime_in_future() -> None:
    future = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
    raw = f"[REMIND:{future.isoformat()}|Hello future]"
    result = parse_reply(raw)
    assert result.reminders[0].when == future


def test_onboarding_done_marker() -> None:
    result = parse_reply("Great, I've got everything I need.\n[ONBOARDING_DONE]")
    assert result.onboarding_done is True
    assert "[ONBOARDING_DONE]" not in result.text


def test_idea_detected_marker() -> None:
    result = parse_reply("That's a real idea!\n[IDEA_DETECTED]")
    assert result.idea_detected is True
    assert "[IDEA_DETECTED]" not in result.text


def test_homework_done_marker() -> None:
    result = parse_reply("Nice work, that's huge.\n[HOMEWORK_DONE]")
    assert result.homework_done is True
    assert result.homework_skipped is False
    assert "[HOMEWORK_DONE]" not in result.text


def test_homework_skipped_marker() -> None:
    result = parse_reply("No worries, life happens.\n[HOMEWORK_SKIPPED]")
    assert result.homework_skipped is True
    assert result.homework_done is False
    assert "[HOMEWORK_SKIPPED]" not in result.text


def test_validate_marker() -> None:
    result = parse_reply("Alright, let me dig into this.\n[VALIDATE]")
    assert result.validate is True
    assert "[VALIDATE]" not in result.text


def test_all_triggers_together() -> None:
    raw = (
        "Great, here's where we are.\n"
        "[ONBOARDING_DONE]\n"
        "[IDEA_DETECTED]\n"
        "[VALIDATE]\n"
        "[REMIND:2026-06-01T10:00:00|Did you talk to anyone?]"
    )
    result = parse_reply(raw)
    assert result.onboarding_done is True
    assert result.idea_detected is True
    assert result.validate is True
    assert len(result.reminders) == 1
