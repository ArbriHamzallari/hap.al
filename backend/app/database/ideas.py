"""Ideas table CRUD."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, cast

from app.database.client import get_supabase
from app.database.models import Idea


async def get_active_idea(user_id: str) -> Idea | None:
    """Return the user's currently active idea, or None."""

    def _query() -> dict[str, Any] | None:
        client = get_supabase()
        result = (
            client.table("ideas")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        rows = cast(list[dict[str, Any]], result.data)
        return rows[0] if rows else None

    row = await asyncio.to_thread(_query)
    return Idea.model_validate(row) if row else None


async def upsert_active_idea(user_id: str, fields: dict[str, Any]) -> Idea:
    """Update the user's active idea if one exists, else insert a new one as active."""

    def _query() -> dict[str, Any]:
        client = get_supabase()
        cleaned = {k: v for k, v in fields.items() if v is not None and v != ""}
        existing = (
            client.table("ideas")
            .select("id")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        existing_rows = cast(list[dict[str, Any]], existing.data)
        if existing_rows:
            idea_id = existing_rows[0]["id"]
            cleaned["updated_at"] = datetime.now(UTC).isoformat()
            updated = client.table("ideas").update(cleaned).eq("id", idea_id).execute()
            return cast(list[dict[str, Any]], updated.data)[0]
        cleaned["user_id"] = user_id
        cleaned["is_active"] = True
        inserted = client.table("ideas").insert(cleaned).execute()
        return cast(list[dict[str, Any]], inserted.data)[0]

    row = await asyncio.to_thread(_query)
    return Idea.model_validate(row)


async def deactivate_active_idea(user_id: str) -> bool:
    """Mark the active idea as is_active=false. Returns True if anything was updated."""

    def _query() -> bool:
        client = get_supabase()
        result = (
            client.table("ideas")
            .update({"is_active": False, "updated_at": datetime.now(UTC).isoformat()})
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        return bool(result.data)

    return await asyncio.to_thread(_query)


async def update_validation(idea_id: str, validation: dict[str, Any]) -> None:
    """Write validation_score / strengths / weaknesses from a Sonnet validation pass.

    Other fields in `validation` (competitor_summary, market_saturation) belong on the journey
    event, not the ideas row — they don't have schema columns.
    """
    cleaned: dict[str, Any] = {}
    score = validation.get("validation_score")
    if isinstance(score, int):
        cleaned["validation_score"] = max(0, min(100, score))
    strengths = validation.get("strengths")
    if isinstance(strengths, list) and strengths:
        cleaned["strengths"] = [str(s) for s in strengths]
    weaknesses = validation.get("weaknesses")
    if isinstance(weaknesses, list) and weaknesses:
        cleaned["weaknesses"] = [str(w) for w in weaknesses]
    if not cleaned:
        return
    cleaned["updated_at"] = datetime.now(UTC).isoformat()

    def _update() -> None:
        client = get_supabase()
        client.table("ideas").update(cleaned).eq("id", idea_id).execute()

    await asyncio.to_thread(_update)
