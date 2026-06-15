"""In-process reminder poller (60s). Primary delivery path for due homework rows.

pg_cron → POST /internal/process-followups remains a durable backup every 5 minutes
(see app/homework/followup.py) but must not be the only path — that adds up to 5–10 min
latency for [REMIND:...] markers and short-term check-ins.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram.ext import Application

from app.homework.followup import process_due_followups

logger = logging.getLogger("hap.reminders")

_POLL_INTERVAL_SECONDS = 60

# PTB's Application is generic over 6 type params we don't specialize here.
AppType = Application[Any, Any, Any, Any, Any, Any]


async def reminder_loop(application: AppType) -> None:
    """Poll homework table every minute for due follow-ups."""
    logger.info(
        "reminder poller started",
        extra={"interval_s": _POLL_INTERVAL_SECONDS},
    )
    while True:
        try:
            await process_due_followups(application.bot)
        except asyncio.CancelledError:
            logger.info("reminder poller cancelled")
            raise
        except Exception:
            logger.exception("reminder poll cycle failed")
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
