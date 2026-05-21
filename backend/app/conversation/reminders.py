"""In-process reminder poller. Phase 1a only.

Polls the homework table every minute for due reminders, sends them via Telegram, marks
them sent. Reminders fire as push notifications on the user's phone — Telegram routes
through APNs / FCM whether or not the app is open.

Phase 2 swaps this for pg_cron + an /internal/process-followups endpoint so reminders
survive bot downtime (currently a reminder due during a restart fires whenever the bot
comes back, not exactly on time).
"""

from __future__ import annotations

import asyncio
import logging

from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import Application

from app.database.homework import list_due_reminders, mark_reminder_sent
from app.database.users import get_telegram_id
from app.utils.telegram_format import to_telegram_html

logger = logging.getLogger("hap.reminders")

_POLL_INTERVAL_SECONDS = 60


async def reminder_loop(application: Application) -> None:
    """Run forever: poll → send → sleep."""
    logger.info("reminder poller started", extra={"interval_s": _POLL_INTERVAL_SECONDS})
    while True:
        try:
            await _process_due(application)
        except asyncio.CancelledError:
            logger.info("reminder poller cancelled")
            raise
        except Exception:
            logger.exception("reminder poll cycle failed")
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)


async def _process_due(application: Application) -> None:
    due = await list_due_reminders()
    for row in due:
        telegram_id = await get_telegram_id(row["user_id"])
        if telegram_id is None:
            # Orphaned reminder (user deleted?). Mark sent so we don't keep retrying.
            logger.warning("reminder skipped: user missing", extra={"homework_id": row["id"]})
            await mark_reminder_sent(row["id"])
            continue
        delivered = await _deliver(application, telegram_id, row["task_description"])
        if delivered:
            await mark_reminder_sent(row["id"])


async def _deliver(application: Application, chat_id: int, message: str) -> bool:
    """Send the reminder. Returns False if the user blocked the bot (don't retry forever)."""
    html = to_telegram_html(message)
    try:
        await application.bot.send_message(chat_id=chat_id, text=html, parse_mode=ParseMode.HTML)
        return True
    except BadRequest:
        logger.warning("reminder HTML parse failed, sending plain text")
        await application.bot.send_message(chat_id=chat_id, text=message)
        return True
    except Forbidden:
        # User blocked the bot. Mark sent so we don't keep trying.
        logger.warning("reminder send forbidden; marking as sent anyway")
        return True
    except Exception:
        logger.exception("reminder send failed; will retry next cycle")
        return False
