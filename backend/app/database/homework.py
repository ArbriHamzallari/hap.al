"""Homework table CRUD. Durable store for reminders + Phase 2 lifecycle tracking."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.database.client import get_supabase

_BATCH_LIMIT = 50
_PENDING_LIST_LIMIT = 20


async def create_reminder(user_id: str, when: datetime, message: str) -> str:
    """Insert a pending homework row with the reminder body. Returns its UUID."""

    def _insert() -> dict[str, Any]:
        client = get_supabase()
        result = (
            client.table("homework")
            .insert(
                {
                    "user_id": user_id,
                    "task_description": message,
                    "due_date": when.astimezone(UTC).isoformat(),
                    "status": "pending",
                    "follow_up_sent": False,
                }
            )
            .execute()
        )
        return result.data[0]

    row = await asyncio.to_thread(_insert)
    return str(row["id"])


async def list_due_reminders() -> list[dict[str, Any]]:
    """Pending homework rows whose due_date has passed and which haven't been sent."""

    def _query() -> list[dict[str, Any]]:
        client = get_supabase()
        now_iso = datetime.now(UTC).isoformat()
        result = (
            client.table("homework")
            .select("id, user_id, task_description")
            .lte("due_date", now_iso)
            .eq("follow_up_sent", False)
            .eq("status", "pending")
            .limit(_BATCH_LIMIT)
            .execute()
        )
        return result.data

    return await asyncio.to_thread(_query)


async def mark_reminder_sent(homework_id: str) -> None:
    """Set follow_up_sent=true so the poller doesn't fire this reminder again."""

    def _update() -> None:
        client = get_supabase()
        client.table("homework").update({"follow_up_sent": True}).eq("id", homework_id).execute()

    await asyncio.to_thread(_update)


async def list_pending(user_id: str, limit: int = _PENDING_LIST_LIMIT) -> list[dict[str, Any]]:
    """All pending homework for a user, soonest-due first. Used by /homework + system prompt."""

    def _query() -> list[dict[str, Any]]:
        client = get_supabase()
        result = (
            client.table("homework")
            .select("id, task_description, due_date, follow_up_sent")
            .eq("user_id", user_id)
            .eq("status", "pending")
            .order("due_date", desc=False)
            .limit(limit)
            .execute()
        )
        return result.data

    return await asyncio.to_thread(_query)


async def mark_most_recent_sent_pending(user_id: str, new_status: str) -> dict[str, Any] | None:
    """Update the most-recently-due pending homework that was already reminded.

    Returns the row that was updated, or None if no candidate row existed (in which case the
    LLM's HOMEWORK_DONE/SKIPPED marker is a no-op — probably emitted in error).
    """
    if new_status not in {"completed", "skipped"}:
        raise ValueError(f"invalid status transition: {new_status}")

    def _query() -> dict[str, Any] | None:
        client = get_supabase()
        candidate = (
            client.table("homework")
            .select("id, task_description, due_date, idea_id")
            .eq("user_id", user_id)
            .eq("follow_up_sent", True)
            .eq("status", "pending")
            .order("due_date", desc=True)
            .limit(1)
            .execute()
        )
        if not candidate.data:
            return None
        row = candidate.data[0]
        client.table("homework").update({"status": new_status}).eq("id", row["id"]).execute()
        return row

    return await asyncio.to_thread(_query)
