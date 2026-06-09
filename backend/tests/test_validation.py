"""Tests for the validation JSON parser. The Anthropic call itself isn't exercised."""

from __future__ import annotations

from app.conversation.validation import _parse_json


def test_parse_plain_json() -> None:
    text = '{"validation_score": 65, "strengths": ["a", "b"]}'
    result = _parse_json(text)
    assert result is not None
    assert result["validation_score"] == 65
    assert result["strengths"] == ["a", "b"]


def test_parse_json_with_preamble_trimmed() -> None:
    text = 'Here is the analysis:\n{"validation_score": 50}\nDone.'
    result = _parse_json(text)
    assert result is not None
    assert result["validation_score"] == 50


def test_parse_json_in_code_fence() -> None:
    text = '```json\n{"validation_score": 72}\n```'
    result = _parse_json(text)
    assert result is not None
    assert result["validation_score"] == 72


def test_parse_json_in_bare_code_fence() -> None:
    text = '```\n{"validation_score": 30}\n```'
    result = _parse_json(text)
    assert result is not None
    assert result["validation_score"] == 30


def test_parse_no_json_returns_none() -> None:
    assert _parse_json("Sorry, I couldn't find any competitors.") is None


def test_parse_malformed_json_returns_none() -> None:
    assert _parse_json('{"validation_score": 65,}') is None  # trailing comma


def test_parse_non_object_returns_none() -> None:
    # A bare array is valid JSON but we want a dict.
    assert _parse_json("[1, 2, 3]") is None
