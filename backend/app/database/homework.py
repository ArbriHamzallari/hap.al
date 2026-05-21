"""Homework table CRUD. Phase 1a uses it as the durable store for reminders.

Phase 2 will extend with completion tracking, follow-up status transitions,
and the pg_cron-driven process-followups endpoint. For now we just write and
read pending reminders.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.database.client import get_supabase

_BATCH_LIMIT = 50


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
