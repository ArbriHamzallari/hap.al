"""Journey events CRUD. Per CLAUDE.md §5: pivots, milestones, validation feedback, etc."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from app.database.client import get_supabase


async def record_event(
    user_id: str,
    event_type: str,
    description: str,
    *,
    idea_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert a single journey event. Fire-and-forget; nothing reads the ID."""

    def _insert() -> None:
        client = get_supabase()
        client.table("journey_events").insert(
            {
                "user_id": user_id,
                "idea_id": idea_id,
                "event_type": event_type,
                "description": description,
                "metadata": metadata or {},
            }
        ).execute()

    await asyncio.to_thread(_insert)


async def list_recent(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Most-recent events first. Used by /progress."""

    def _query() -> list[dict[str, Any]]:
        client = get_supabase()
        result = (
            client.table("journey_events")
            .select("event_type, description, metadata, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return cast(list[dict[str, Any]], result.data)

    return await asyncio.to_thread(_query)


async def get_latest_validation(idea_id: str) -> dict[str, Any] | None:
    """Most recent validation_feedback event for an idea. Used to populate CURRENT IDEA prompt."""

    def _query() -> dict[str, Any] | None:
        client = get_supabase()
        result = (
            client.table("journey_events")
            .select("description, metadata, created_at")
            .eq("idea_id", idea_id)
            .eq("event_type", "validation_feedback")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = cast(list[dict[str, Any]], result.data)
        return rows[0] if rows else None

    return await asyncio.to_thread(_query)
