"""Conversation engine: persists messages, builds context, calls Anthropic, runs extraction."""

from __future__ import annotations

import logging
from typing import cast

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from app.config import Settings
from app.security.llm_rate_limit import LlmRateLimiter
from app.utils.logger import hash_telegram_id
from app.conversation.context_builder import build_system_prompt
from app.conversation.extraction import extract_idea, extract_profile
from app.conversation.markers import parse_reply
from app.conversation.prompts.base import get_base_module
from app.conversation.validation import validate_idea
from app.database import journey_events
from app.database.conversations import append_message, list_recent
from app.database.homework import list_pending, mark_most_recent_sent_pending
from app.database.ideas import get_active_idea, update_validation, upsert_active_idea
from app.database.models import User
from app.database.users import update_profile

logger = logging.getLogger("hap.engine")

_HISTORY_LIMIT = 20
_EXTRACTION_HISTORY_LIMIT = 40
_MAX_OUTPUT_TOKENS = 1024


def _normalize(history: list[MessageParam]) -> list[MessageParam]:
    """Collapse same-role runs so the Anthropic API accepts the request.

    Consecutive messages from the same role are merged (oldest first) rather than dropped,
    so context isn't lost when e.g. a button tap and a typed message both arrive as `user`.
    """
    out: list[MessageParam] = []
    for msg in history:
        if out and out[-1]["role"] == msg["role"]:
            prev = out[-1].get("content")
            cur = msg.get("content")
            if isinstance(prev, str) and isinstance(cur, str):
                merged = {"role": msg["role"], "content": f"{prev}\n\n{cur}"}
                out[-1] = cast(MessageParam, merged)
            else:
                out[-1] = msg
        else:
            out.append(msg)
    return out


def _is_title_pivot(old: str | None, new: str | None) -> bool:
    if not old or not new:
        return False
    return old.strip().lower() != new.strip().lower()


class ConversationEngine:
    """Anthropic client + DB-backed conversation history + structured extraction."""

    def __init__(self, settings: Settings, llm_limiter: LlmRateLimiter | None = None) -> None:
        # max_retries=5 buys ~30-60s of exponential backoff before giving up. Anthropic's
        # transient `overloaded_error` (HTTP 529) usually clears in a few seconds; the SDK
        # retries it automatically. Default is 2, which is too aggressive a fail.
        self._client = AsyncAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
            max_retries=5,
        )
        self._settings = settings
        self._model = settings.default_llm_model
        self._analysis_model = settings.analysis_llm_model
        self._llm_limiter = llm_limiter or LlmRateLimiter(
            daily_per_user=settings.llm_daily_call_limit,
            monthly_budget_usd=settings.monthly_budget_cap_usd,
        )

    def _reserve_llm_call(self, user: User) -> None:
        """Raise LlmLimitExceeded when daily or monthly LLM limits are exceeded."""
        user_hash = hash_telegram_id(user.telegram_id, self._settings)
        self._llm_limiter.check_and_record(user_hash)

    async def respond(self, user: User, user_message: str) -> str:
        base_version = get_base_module(user.language).VERSION
        await append_message(
            user.id,
            "user",
            user_message,
            language=user.language,
            prompt_version=base_version,
        )
        history = await list_recent(user.id, limit=_HISTORY_LIMIT)
        idea = await get_active_idea(user.id)
        pending = await list_pending(user.id)

        validation_summary: str | None = None
        if idea is not None:
            latest_validation = await journey_events.get_latest_validation(idea.id)
            if latest_validation:
                validation_summary = latest_validation.get("description")

        system_prompt = build_system_prompt(user, history, idea, pending, validation_summary)

        self._reserve_llm_call(user)
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_OUTPUT_TOKENS,
            system=system_prompt,
            messages=_normalize(history),
        )
        text_blocks = [block.text for block in response.content if block.type == "text"]
        assistant_message = "".join(text_blocks).strip()

        # Persist the marker-free text so out-of-band markers ([VALIDATE], [BTN:...],
        # [REMIND:...], etc.) don't leak back into the model's context on later turns.
        # The raw reply is still returned so the bot can parse the markers for this turn.
        stored_message = parse_reply(assistant_message).text
        await append_message(
            user.id,
            "assistant",
            stored_message,
            language=user.language,
            prompt_version=base_version,
        )
        return assistant_message

    async def run_profile_extraction(self, user: User) -> None:
        """Pull profile fields from history and write them to the users row."""
        history = await list_recent(user.id, limit=_EXTRACTION_HISTORY_LIMIT)
        self._reserve_llm_call(user)
        data = await extract_profile(self._client, history, self._model)
        if data is None:
            logger.warning("profile extraction returned nothing", extra={"user_id": user.id})
            return
        await update_profile(user.id, data, mark_onboarded=True)
        logger.info("profile extracted and stored", extra={"user_id": user.id})

    async def run_idea_extraction(self, user: User) -> None:
        """Pull idea fields from history, upsert active idea, log a pivot if the title changed."""
        history = await list_recent(user.id, limit=_EXTRACTION_HISTORY_LIMIT)
        self._reserve_llm_call(user)
        data = await extract_idea(self._client, history, self._model)
        if data is None:
            logger.warning("idea extraction returned nothing", extra={"user_id": user.id})
            return

        existing = await get_active_idea(user.id)
        new_title = data.get("title")
        if existing is not None and _is_title_pivot(existing.title, new_title):
            await journey_events.record_event(
                user_id=user.id,
                idea_id=existing.id,
                event_type="pivot",
                description=f"{existing.title} → {new_title}",
                metadata={"from_title": existing.title, "to_title": new_title},
            )

        await upsert_active_idea(user.id, data)
        logger.info("idea extracted and stored", extra={"user_id": user.id})

    async def run_homework_update(self, user: User, *, completed: bool) -> None:
        """Flip the most recently sent pending homework. Record a milestone on completion."""
        new_status = "completed" if completed else "skipped"
        row = await mark_most_recent_sent_pending(user.id, new_status)
        if row is None:
            logger.info(
                "homework marker had no matching sent-pending row",
                extra={"user_id": user.id},
            )
            return
        if completed:
            await journey_events.record_event(
                user_id=user.id,
                idea_id=row.get("idea_id"),
                event_type="milestone",
                description=f"Completed: {row.get('task_description', '(task)')}",
            )
        logger.info(
            "homework marked",
            extra={"user_id": user.id, "homework_id": row["id"], "status": new_status},
        )

    async def run_validation(self, user: User) -> None:
        """Run a Sonnet 4.6 + web-search validation pass on the active idea."""
        idea = await get_active_idea(user.id)
        if idea is None:
            logger.info("validation requested with no active idea", extra={"user_id": user.id})
            return
        self._reserve_llm_call(user)
        result = await validate_idea(self._client, user, idea, self._analysis_model)
        if result is None:
            logger.warning("validation returned nothing", extra={"user_id": user.id})
            return

        await update_validation(idea.id, result)

        competitor_summary = (
            str(result.get("competitor_summary") or "").strip() or "Validation complete."
        )
        await journey_events.record_event(
            user_id=user.id,
            idea_id=idea.id,
            event_type="validation_feedback",
            description=competitor_summary,
            metadata={
                "validation_score": result.get("validation_score"),
                "market_saturation": result.get("market_saturation"),
                "strengths": result.get("strengths") or [],
                "weaknesses": result.get("weaknesses") or [],
            },
        )
        logger.info(
            "validation complete",
            extra={"user_id": user.id, "score": result.get("validation_score")},
        )
