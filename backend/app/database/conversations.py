"""Conversations table CRUD. Phase 1a replaces the in-memory history dict."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from anthropic.types import MessageParam

from app.database.client import get_supabase

_HISTORY_LIMIT = 20


async def append_message(
    user_id: str,
    role: str,
    content: str,
    *,
    language: str = "en",
    message_type: str = "general",
    prompt_version: str | None = None,
) -> None:
    """Insert a single message row."""

    def _insert() -> None:
        client = get_supabase()
        client.table("conversations").insert(
            {
                "user_id": user_id,
                "role": role,
                "content": content,
                "language": language,
                "message_type": message_type,
                "prompt_version": prompt_version,
            }
        ).execute()

    await asyncio.to_thread(_insert)


async def list_recent(user_id: str, limit: int = _HISTORY_LIMIT) -> list[MessageParam]:
    """Return the user's last `limit` messages in chronological order, ready for Anthropic."""

    def _query() -> list[dict[str, Any]]:
        client = get_supabase()
        result = (
            client.table("conversations")
            .select("role, content")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    rows = await asyncio.to_thread(_query)
    rows.reverse()  # DB query returned newest-first; LLM wants oldest-first
    return [cast(MessageParam, {"role": row["role"], "content": row["content"]}) for row in rows]
