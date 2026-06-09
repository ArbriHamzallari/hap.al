"""Dev-only in-process reminder poller when USE_POLLING=true.

Production uses pg_cron → POST /internal/process-followups (see app/homework/followup.py).
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
    """Poll homework table every minute — only for local polling mode."""
    logger.info(
        "dev reminder poller started",
        extra={"interval_s": _POLL_INTERVAL_SECONDS},
    )
    while True:
        try:
            await process_due_followups(application.bot)
        except asyncio.CancelledError:
            logger.info("dev reminder poller cancelled")
            raise
        except Exception:
            logger.exception("dev reminder poll cycle failed")
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
