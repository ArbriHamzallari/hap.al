"""Product analytics events (CLAUDE.md §17). No PII — hashed telegram id only."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.database.client import get_supabase

logger = logging.getLogger("hap.analytics")


async def track_event(
    user_hash: str,
    event_name: str,
    properties: dict[str, Any] | None = None,
) -> None:
    """Insert a row into analytics_events. Failures are logged, never raised to users."""

    def _insert() -> None:
        client = get_supabase()
        client.table("analytics_events").insert(
            {
                "user_hash": user_hash,
                "event_name": event_name,
                "properties": properties or {},
            }
        ).execute()

    try:
        await asyncio.to_thread(_insert)
    except Exception:
        logger.exception("analytics track failed", extra={"event": event_name})
