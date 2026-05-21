"""Ideas table CRUD."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

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
        return result.data[0] if result.data else None

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
        if existing.data:
            idea_id = existing.data[0]["id"]
            cleaned["updated_at"] = datetime.now(UTC).isoformat()
            updated = client.table("ideas").update(cleaned).eq("id", idea_id).execute()
            return updated.data[0]
        cleaned["user_id"] = user_id
        cleaned["is_active"] = True
        inserted = client.table("ideas").insert(cleaned).execute()
        return inserted.data[0]

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
