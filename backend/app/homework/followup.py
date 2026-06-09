"""Durable homework follow-up delivery (Flow 3). Used by pg_cron and optional dev poller."""

from __future__ import annotations

import logging

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden

from app.database.homework import list_due_reminders, mark_reminder_sent
from app.database.users import get_telegram_id, get_user_language
from app.i18n.loader import t
from app.utils.telegram_format import to_telegram_html

logger = logging.getLogger("hap.followup")


async def deliver_followup(bot: Bot, chat_id: int, message: str) -> bool:
    """Send a follow-up message. Returns False on transient errors (retry next cycle)."""
    html = to_telegram_html(message)
    try:
        await bot.send_message(chat_id=chat_id, text=html, parse_mode=ParseMode.HTML)
        return True
    except BadRequest:
        logger.warning("follow-up HTML parse failed, sending plain text")
        await bot.send_message(chat_id=chat_id, text=message)
        return True
    except Forbidden:
        logger.warning("follow-up send forbidden; marking as sent anyway")
        return True
    except Exception:
        logger.exception("follow-up send failed; will retry next cycle")
        return False


async def process_due_followups(bot: Bot) -> int:
    """Send all due homework reminders. Returns count delivered."""
    due = await list_due_reminders()
    sent = 0
    for row in due:
        telegram_id = await get_telegram_id(row["user_id"])
        if telegram_id is None:
            logger.warning(
                "follow-up skipped: user missing",
                extra={"homework_id": row["id"]},
            )
            await mark_reminder_sent(row["id"])
            continue

        body = row.get("task_description") or ""
        lang = await get_user_language(row["user_id"]) or "en"
        if not body.strip():
            body = t("followup.default_checkin", lang)

        if await deliver_followup(bot, telegram_id, body):
            await mark_reminder_sent(row["id"])
            sent += 1
    return sent
