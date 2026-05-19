"""Tests for to_telegram_html: bold, italic, HTML escaping."""

from __future__ import annotations

from app.utils.telegram_format import to_telegram_html


def test_empty() -> None:
    assert to_telegram_html("") == ""


def test_plain_text_passes_through() -> None:
    assert to_telegram_html("hello world") == "hello world"


def test_bold() -> None:
    assert to_telegram_html("**bold**") == "<b>bold</b>"


def test_italic_asterisk() -> None:
    assert to_telegram_html("*italic*") == "<i>italic</i>"


def test_italic_underscore() -> None:
    assert to_telegram_html("_italic_") == "<i>italic</i>"


def test_bold_inside_sentence() -> None:
    assert to_telegram_html("Hello **world** today.") == "Hello <b>world</b> today."


def test_mixed_bold_and_italic() -> None:
    result = to_telegram_html("**bold** and *italic* and _under_")
    assert result == "<b>bold</b> and <i>italic</i> and <i>under</i>"


def test_html_chars_escaped() -> None:
    assert to_telegram_html("<script>") == "&lt;script&gt;"


def test_html_chars_inside_bold_escaped() -> None:
    assert to_telegram_html("**a<b**") == "<b>a&lt;b</b>"


def test_single_asterisk_in_word_not_italic() -> None:
    assert to_telegram_html("x*y") == "x*y"


def test_underscore_in_identifier_not_italic() -> None:
    assert to_telegram_html("snake_case_var") == "snake_case_var"


def test_amp_escaped() -> None:
    assert to_telegram_html("a & b") == "a &amp; b"


def test_bold_with_em_dash_inside() -> None:
    assert to_telegram_html("**Layer 1 — The person.**") == "<b>Layer 1 — The person.</b>"


def test_escapes_html_outside_bold() -> None:
    assert to_telegram_html("Use <script> & **bold**") == "Use &lt;script&gt; &amp; <b>bold</b>"
