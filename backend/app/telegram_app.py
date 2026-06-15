"""Shared python-telegram-bot Application factory for polling and webhook modes."""

from __future__ import annotations

import logging
from typing import Any

import anthropic
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Update
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

from app.config import Settings
from app.conversation.engine import ConversationEngine
from app.conversation.keyboards import field_for_callback, get_keyboard, label_for_callback
from app.conversation.markers import parse_reply
from app.conversation.reminders import reminder_loop
from app.database import analytics as analytics_db
from app.database import journey_events
from app.database.homework import list_pending
from app.homework.followup import schedule_user_reminder
from app.database.ideas import deactivate_active_idea, get_active_idea
from app.database.users import delete_user_data, get_or_create_user, update_field
from app.i18n.loader import Lang, t
from app.security.llm_rate_limit import LlmLimitExceeded, LlmRateLimiter
from app.security.rate_limit import UserRateLimiter
from app.security.sanitizer import sanitize_input
from app.utils.logger import configure_logging, hash_telegram_id
from app.utils.telegram_format import to_telegram_html

logger = logging.getLogger("hap.bot")

# PTB's Application is generic over 6 type params we don't specialize here.
AppType = Application[Any, Any, Any, Any, Any, Any]

# telegram user id -> awaiting YES for /deletedata
_pending_delete: set[int] = set()


def _lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Lang:
    """Best-effort language for bot-initiated strings on this turn."""
    data = context.user_data
    stored = data.get("language") if data is not None else None
    return "sq" if stored == "sq" else "en"


def _remember_lang(context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    """Cache the user's language on this chat's user_data (PTB types it as Optional)."""
    if context.user_data is not None:
        context.user_data["language"] = lang


async def _send_reply(
    chat: Chat,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    html = to_telegram_html(text)
    try:
        await chat.send_message(html, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except BadRequest:
        logger.warning("telegram HTML parse failed, sending plain text")
        await chat.send_message(text, reply_markup=reply_markup)


async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    engine: ConversationEngine = context.application.bot_data["engine"]
    limiter: UserRateLimiter = context.application.bot_data["rate_limiter"]
    user_hash = hash_telegram_id(tg_user.id, settings)

    if tg_user.id in _pending_delete:
        await _handle_deletedata_confirm(update, context, text.strip())
        return

    if not limiter.is_allowed(user_hash):
        lang = _lang(update, context)
        await chat.send_message(t("errors.rate_limit", lang))
        return

    safe_text = sanitize_input(text)
    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
        telegram_language_code=tg_user.language_code,
        message_text=safe_text,
    )
    _remember_lang(context, user.language)
    logger.info("turn", extra={"user_hash": user_hash})

    lang = _lang(update, context)
    await chat.send_action("typing")
    try:
        raw_reply = await engine.respond(user, safe_text)
    except LlmLimitExceeded as exc:
        key = (
            "errors.llm_monthly_budget"
            if exc.reason == "monthly_budget"
            else "errors.llm_daily_limit"
        )
        await chat.send_message(t(key, lang))
        return

    parsed = parse_reply(raw_reply)

    markup = get_keyboard(parsed.button_key, user.language)
    await _send_reply(chat, parsed.text, reply_markup=markup)

    for reminder in parsed.reminders:
        await schedule_user_reminder(
            context.application.bot,
            user.id,
            tg_user.id,
            reminder.when,
            reminder.message,
        )
        logger.info(
            "reminder scheduled",
            extra={"user_hash": user_hash, "fires_at": reminder.when.isoformat()},
        )

    if parsed.onboarding_done and not user.onboarding_complete:
        logger.info("onboarding done, extracting profile", extra={"user_hash": user_hash})
        try:
            await engine.run_profile_extraction(user)
        except LlmLimitExceeded:
            logger.warning("profile extraction skipped: LLM limit", extra={"user_hash": user_hash})
        await analytics_db.track_event(
            user_hash,
            "onboarding_completed",
            {"language": user.language},
        )

    if parsed.idea_detected:
        logger.info("idea detected, extracting", extra={"user_hash": user_hash})
        had_idea = await get_active_idea(user.id) is not None
        try:
            await engine.run_idea_extraction(user)
        except LlmLimitExceeded:
            logger.warning("idea extraction skipped: LLM limit", extra={"user_hash": user_hash})
            had_idea = True  # suppress false idea_created analytics
        if not had_idea:
            idea = await get_active_idea(user.id)
            await analytics_db.track_event(
                user_hash,
                "idea_created",
                {
                    "language": user.language,
                    "initial_validation_score": idea.validation_score if idea else 0,
                },
            )

    if parsed.validate:
        logger.info("validation requested", extra={"user_hash": user_hash})
        await chat.send_action("typing")
        try:
            await engine.run_validation(user)
        except LlmLimitExceeded:
            await chat.send_message(t("errors.llm_daily_limit", lang))

    if parsed.homework_done:
        logger.info("homework reported done", extra={"user_hash": user_hash})
        await engine.run_homework_update(user, completed=True)
        await analytics_db.track_event(user_hash, "homework_completed", {"language": user.language})
    elif parsed.homework_skipped:
        logger.info("homework reported skipped", extra={"user_hash": user_hash})
        await engine.run_homework_update(user, completed=False)
        await analytics_db.track_event(user_hash, "homework_skipped", {"language": user.language})


async def _handle_deletedata_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return
    lang = _lang(update, context)
    _pending_delete.discard(tg_user.id)
    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    settings: Settings = context.application.bot_data["settings"]
    user_hash = hash_telegram_id(tg_user.id, settings)
    yes_words = {"yes", "po", "PO", "YES"}
    if text in yes_words:
        await delete_user_data(user.id)
        await analytics_db.track_event(user_hash, "user_deleted_data", {})
        await chat.send_message(t("commands.deletedata_done", lang))
    else:
        await chat.send_message(t("commands.deletedata_cancel", lang))


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    text = message.text if message and message.text else "/start"
    tg_user = update.effective_user
    settings: Settings = context.application.bot_data["settings"]
    if tg_user is not None:
        user_hash = hash_telegram_id(tg_user.id, settings)
        user = await get_or_create_user(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            telegram_language_code=tg_user.language_code,
            message_text=text,
        )
        _remember_lang(context, user.language)
        await analytics_db.track_event(
            user_hash,
            "bot_started",
            {"language": user.language, "is_new_user": user.is_new},
        )
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

    if callback.startswith("lang:"):
        await query.answer()
        lang_code = callback.removeprefix("lang:")
        if lang_code not in ("en", "sq"):
            return
        lang: Lang = "sq" if lang_code == "sq" else "en"
        tg_user = update.effective_user
        if tg_user is None:
            return
        user = await get_or_create_user(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        await update_field(user.id, "language", lang)
        _remember_lang(context, lang)
        name = t(f"language_names.{lang}", lang)
        chat = update.effective_chat
        if chat is not None:
            await chat.send_message(t("commands.language_set", lang, language=name))
        return

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
        _remember_lang(context, user.language)
        field_name, value = field_value
        await update_field(user.id, field_name, value)

    await _handle(update, context, label)


async def _on_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    lang = _lang(update, context)
    await chat.send_message(t("non_text", lang))


async def _help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    lang = _lang(update, context)
    await chat.send_message(t("commands.help", lang))


async def _language(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("English", callback_data="lang:en")],
            [InlineKeyboardButton("Shqip", callback_data="lang:sq")],
        ]
    )
    await chat.send_message("Pick your language / Zgjidh gjuhën:", reply_markup=markup)


async def _deletedata(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return
    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    _remember_lang(context, user.language)
    _pending_delete.add(tg_user.id)
    await chat.send_message(t("commands.deletedata_confirm", user.language))


async def _myidea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    _remember_lang(context, user.language)
    lang = user.language
    idea = await get_active_idea(user.id)
    if idea is None:
        await chat.send_message(t("commands.no_idea", lang))
        return

    lines: list[str] = []
    if idea.title:
        lines.append(f"**{idea.title}**")
    if idea.description:
        if lines:
            lines.append("")
        lines.append(idea.description)
    if idea.target_customer:
        lines.append(f"\n*{t('commands.idea_target', lang)}* {idea.target_customer}")
    if idea.problem_solved:
        lines.append(f"*{t('commands.idea_problem', lang)}* {idea.problem_solved}")
    if idea.business_model:
        lines.append(f"*{t('commands.idea_model', lang)}* {idea.business_model}")
    if idea.unique_advantage:
        lines.append(f"*{t('commands.idea_edge', lang)}* {idea.unique_advantage}")
    lines.append(f"*{t('commands.idea_stage', lang)}* {idea.current_stage}")
    if idea.validation_score:
        lines.append(f"*{t('commands.idea_score', lang)}* {idea.validation_score}/100")
    if idea.strengths:
        lines.append("")
        lines.append(f"*{t('commands.idea_strengths', lang)}*")
        for s in idea.strengths:
            lines.append(f"  • {s}")
    if idea.weaknesses:
        lines.append("")
        lines.append(f"*{t('commands.idea_weaknesses', lang)}*")
        for w in idea.weaknesses:
            lines.append(f"  • {w}")

    latest_validation = await journey_events.get_latest_validation(idea.id)
    if latest_validation and latest_validation.get("description"):
        lines.append("")
        lines.append(f"*{t('commands.idea_competitors', lang)}*")
        lines.append(str(latest_validation["description"]))

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
    _remember_lang(context, user.language)
    await deactivate_active_idea(user.id)
    await _handle(update, context, "/newidea")


async def _homework(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.utils.dates import describe_due

    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    _remember_lang(context, user.language)
    lang = user.language
    pending = await list_pending(user.id)
    if not pending:
        await chat.send_message(t("commands.no_homework", lang))
        return

    lines = [f"**{t('commands.homework_header', lang)}**", ""]
    for row in pending:
        desc = row.get("task_description") or "(no description)"
        due_str = describe_due(row.get("due_date"), lang)
        if row.get("follow_up_sent"):
            sent_status = t("commands.homework_awaiting", lang)
        else:
            sent_status = due_str
        lines.append(f"- {desc}")
        lines.append(f"   _{sent_status}_")
    await _send_reply(chat, "\n".join(lines))


async def _progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.utils.dates import format_event_when

    chat = update.effective_chat
    tg_user = update.effective_user
    if chat is None or tg_user is None:
        return

    user = await get_or_create_user(
        telegram_id=tg_user.id,
        username=tg_user.username,
        first_name=tg_user.first_name,
    )
    _remember_lang(context, user.language)
    lang = user.language
    events = await journey_events.list_recent(user.id)
    if not events:
        await chat.send_message(t("commands.no_progress", lang))
        return

    lines = [f"**{t('commands.progress_header', lang)}**", ""]
    for ev in events:
        when_str = format_event_when(ev.get("created_at"))
        kind = str(ev.get("event_type", "")).replace("_", " ")
        desc = ev.get("description") or ""
        lines.append(f"*{when_str}* — {kind}")
        if desc:
            lines.append(f"  {desc}")
        lines.append("")
    await _send_reply(chat, "\n".join(lines).rstrip())


def _is_overloaded(err: BaseException | None) -> bool:
    if err is None:
        return False
    if isinstance(err, anthropic.APIStatusError) and err.status_code in (429, 529):
        return True
    return "overloaded" in str(err).lower()


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("handler error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat is not None:
        lang: Lang = "en"
        if context.user_data is not None and context.user_data.get("language") == "sq":
            lang = "sq"
        key = "errors.overloaded" if _is_overloaded(context.error) else "errors.generic"
        await update.effective_chat.send_message(t(key, lang))


async def _post_init(application: AppType) -> None:
    application.create_task(reminder_loop(application))


def build_application(settings: Settings) -> AppType:
    """Create a configured PTB Application (handlers registered, not yet running)."""
    configure_logging(settings)
    llm_limiter = LlmRateLimiter(
        daily_per_user=settings.llm_daily_call_limit,
        monthly_budget_usd=settings.monthly_budget_cap_usd,
    )
    engine = ConversationEngine(settings, llm_limiter=llm_limiter)
    limiter = UserRateLimiter(
        per_minute=settings.rate_limit_per_minute,
        per_day=settings.rate_limit_per_day,
    )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token.get_secret_value())
        .post_init(_post_init)
        .build()
    )
    application.bot_data["engine"] = engine
    application.bot_data["settings"] = settings
    application.bot_data["rate_limiter"] = limiter

    application.add_handler(CommandHandler("start", _start))
    application.add_handler(CommandHandler("help", _help))
    application.add_handler(CommandHandler("language", _language))
    application.add_handler(CommandHandler("deletedata", _deletedata))
    application.add_handler(CommandHandler("myidea", _myidea))
    application.add_handler(CommandHandler("newidea", _newidea))
    application.add_handler(CommandHandler("homework", _homework))
    application.add_handler(CommandHandler("progress", _progress))
    application.add_handler(CallbackQueryHandler(_on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_text))
    application.add_handler(MessageHandler(~filters.TEXT, _on_non_text))
    application.add_error_handler(_on_error)
    return application
