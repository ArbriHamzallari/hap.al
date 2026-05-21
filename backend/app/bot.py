"""Telegram bot entrypoint. Phase 2a: follow-up flow, /homework, /progress."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from telegram import Chat, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import Settings, get_settings
from app.conversation.engine import ConversationEngine
from app.conversation.keyboards import field_for_callback, get_keyboard, label_for_callback
from app.conversation.markers import parse_reply
from app.conversation.reminders import reminder_loop
from app.database import journey_events
from app.database.homework import create_reminder, list_pending
from app.database.ideas import deactivate_active_idea, get_active_idea
from app.database.users import get_or_create_user, update_field
from app.utils.logger import configure_logging, hash_telegram_id
from app.utils.observability import init_sentry
from app.utils.telegram_format import to_telegram_html

logger = logging.getLogger("hap.bot")

_NON_TEXT_FALLBACK = (
    "Right now I can only read text messages. Tell me what you'd like to talk about in writing?"
)
_ERROR_FALLBACK = "Something went wrong on my end. Give me a moment and try again."
_NO_IDEA_TEXT = "You haven't shared an idea with me yet. Tell me about it — what are you thinking?"
_NO_HOMEWORK_TEXT = "No active homework right now. What's the next move?"
_NO_PROGRESS_TEXT = (
    "No journey milestones yet. Once we work on tasks together, I'll track them here."
)

_HELP_TEXT = (
    "Here's what I can do:\n"
    "/start — restart our conversation\n"
    "/myidea — show your current idea\n"
    "/newidea — archive the current idea and explore a new one\n"
    "/homework — list your pending tasks\n"
    "/progress — show your journey timeline\n"
    "/help — show this message\n\n"
    "Otherwise just text me normally. I remember everything across sessions and I'll "
    "ping you when we agree on a task."
)


async def _send_reply(
    chat: Chat,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Send the reply via Telegram HTML, with a plain-text fallback on parse failure."""
    html = to_telegram_html(text)
    try:
        await chat.send_message(html, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except BadRequest:
        logger.warning("telegram HTML parse failed, sending plain text")
        await chat.send_message(text, reply_markup=reply_markup)


async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Common path: user lookup → engine → marker parse → side effects → reply."""
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    engine: ConversationEngine = context.application.bot_data["engine"]
    user_hash = hash_telegram_id(tg_user.id, settings)

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    logger.info("turn", extra={"user_hash": user_hash})

    await chat.send_action("typing")
    raw_reply = await engine.respond(user, text)
    parsed = parse_reply(raw_reply)

    for reminder in parsed.reminders:
        await create_reminder(user.id, reminder.when, reminder.message)
        logger.info(
            "reminder scheduled",
            extra={"user_hash": user_hash, "fires_at": reminder.when.isoformat()},
        )

    if parsed.onboarding_done and not user.onboarding_complete:
        logger.info("onboarding done, extracting profile", extra={"user_hash": user_hash})
        await engine.run_profile_extraction(user)

    if parsed.idea_detected:
        logger.info("idea detected, extracting", extra={"user_hash": user_hash})
        await engine.run_idea_extraction(user)

    if parsed.homework_done:
        logger.info("homework reported done", extra={"user_hash": user_hash})
        await engine.run_homework_update(user, completed=True)
    elif parsed.homework_skipped:
        logger.info("homework reported skipped", extra={"user_hash": user_hash})
        await engine.run_homework_update(user, completed=False)

    markup = get_keyboard(parsed.button_key)
    await _send_reply(chat, parsed.text, reply_markup=markup)


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    text = message.text if message and message.text else "/start"
    await _handle(update, context, text)


async def _on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or message.text is None:
        return
    await _handle(update, context, message.text)


async def _on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    callback = query.data
    label = label_for_callback(callback)
    await query.answer()
    if label is None:
        return

    tg_user = update.effective_user
    field_value = field_for_callback(callback)
    if field_value is not None and tg_user is not None:
        user = await get_or_create_user(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        field_name, value = field_value
        await update_field(user.id, field_name, value)

    await _handle(update, context, label)


async def _on_non_text(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await chat.send_message(_NON_TEXT_FALLBACK)


async def _help(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    await chat.send_message(_HELP_TEXT)


async def _myidea(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    idea = await get_active_idea(user.id)
    if idea is None:
        await chat.send_message(_NO_IDEA_TEXT)
        return

    lines: list[str] = []
    if idea.title:
        lines.append(f"**{idea.title}**")
    if idea.description:
        if lines:
            lines.append("")
        lines.append(idea.description)
    if idea.target_customer:
        lines.append(f"\n*Target customer:* {idea.target_customer}")
    if idea.problem_solved:
        lines.append(f"*Problem:* {idea.problem_solved}")
    if idea.business_model:
        lines.append(f"*Business model:* {idea.business_model}")
    if idea.unique_advantage:
        lines.append(f"*Your edge:* {idea.unique_advantage}")
    lines.append(f"*Stage:* {idea.current_stage}")
    if idea.validation_score:
        lines.append(f"*Validation score:* {idea.validation_score}/100")
    await _send_reply(chat, "\n".join(lines))


async def _newidea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    if tg_user is None:
        return
    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    await deactivate_active_idea(user.id)
    await _handle(update, context, "/newidea")


async def _homework(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    pending = await list_pending(user.id)
    if not pending:
        await chat.send_message(_NO_HOMEWORK_TEXT)
        return

    lines = ["**Your homework:**", ""]
    for row in pending:
        desc = row.get("task_description") or "(no description)"
        due_str = _describe_due(row.get("due_date"))
        sent_status = "awaiting your update" if row.get("follow_up_sent") else due_str
        lines.append(f"- {desc}")
        lines.append(f"   _{sent_status}_")
    await _send_reply(chat, "\n".join(lines))


async def _progress(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    events = await journey_events.list_recent(user.id)
    if not events:
        await chat.send_message(_NO_PROGRESS_TEXT)
        return

    lines = ["**Your journey:**", ""]
    for ev in events:
        when_str = _format_event_when(ev.get("created_at"))
        kind = str(ev.get("event_type", "")).replace("_", " ")
        desc = ev.get("description") or ""
        lines.append(f"*{when_str}* — {kind}")
        if desc:
            lines.append(f"  {desc}")
        lines.append("")
    await _send_reply(chat, "\n".join(lines).rstrip())


def _describe_due(iso_value: Any) -> str:
    if not iso_value:
        return "no due date"
    try:
        when = datetime.fromisoformat(str(iso_value))
    except ValueError:
        return "no due date"
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    delta = when - datetime.now(UTC)
    minutes = int(delta.total_seconds() // 60)
    if minutes < -60 * 24:
        return f"due {-minutes // (60 * 24)}d ago"
    if minutes < 0:
        return "due now"
    if minutes < 60:
        return f"due in {minutes}m"
    if minutes < 60 * 24:
        return f"due in {minutes // 60}h"
    return f"due in {minutes // (60 * 24)}d"


def _format_event_when(iso_value: Any) -> str:
    if not iso_value:
        return "unknown"
    try:
        when = datetime.fromisoformat(str(iso_value))
    except ValueError:
        return "unknown"
    return when.strftime("%b %d, %H:%M")


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("handler error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat is not None:
        await update.effective_chat.send_message(_ERROR_FALLBACK)


async def _post_init(application: Application) -> None:
    """Start the reminder poller as a tracked background task once the loop is running."""
    application.create_task(reminder_loop(application))


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    init_sentry(settings)
    engine = ConversationEngine(settings)

    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .post_init(_post_init)
        .build()
    )
    application.bot_data["engine"] = engine
    application.bot_data["settings"] = settings

    application.add_handler(CommandHandler("start", _start))
    application.add_handler(CommandHandler("help", _help))
    application.add_handler(CommandHandler("myidea", _myidea))
    application.add_handler(CommandHandler("newidea", _newidea))
    application.add_handler(CommandHandler("homework", _homework))
    application.add_handler(CommandHandler("progress", _progress))
    application.add_handler(CallbackQueryHandler(_on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_text))
    application.add_handler(MessageHandler(~filters.TEXT, _on_non_text))
    application.add_error_handler(_on_error)

    logger.info("starting bot in polling mode", extra={"env": settings.app_env})
    application.run_polling()


if __name__ == "__main__":
    main()
