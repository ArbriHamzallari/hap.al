"""Sanity tests for the journey_events module. Doesn't exercise the DB."""

from __future__ import annotations

from app.database import journey_events


def test_module_exposes_expected_helpers() -> None:
    assert callable(journey_events.record_event)
    assert callable(journey_events.list_recent)
