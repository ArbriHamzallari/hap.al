"""Conversation engine: persists messages, builds context, calls Anthropic, runs extraction."""

from __future__ import annotations

import logging

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from app.config import Settings
from app.conversation.context_builder import build_system_prompt
from app.conversation.extraction import extract_idea, extract_profile
from app.conversation.prompts.base_en import VERSION as BASE_VERSION
from app.database import journey_events
from app.database.conversations import append_message, list_recent
from app.database.homework import list_pending, mark_most_recent_sent_pending
from app.database.ideas import get_active_idea, upsert_active_idea
from app.database.models import User
from app.database.users import update_profile

logger = logging.getLogger("hap.engine")

_HISTORY_LIMIT = 20
_EXTRACTION_HISTORY_LIMIT = 40
_MAX_OUTPUT_TOKENS = 1024


def _normalize(history: list[MessageParam]) -> list[MessageParam]:
    """Collapse same-role runs so the Anthropic API accepts the request."""
    out: list[MessageParam] = []
    for msg in history:
        if out and out[-1]["role"] == msg["role"]:
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

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())
        self._model = settings.default_llm_model

    async def respond(self, user: User, user_message: str) -> str:
        await append_message(
            user.id,
            "user",
            user_message,
            language=user.language,
            prompt_version=BASE_VERSION,
        )
        history = await list_recent(user.id, limit=_HISTORY_LIMIT)
        idea = await get_active_idea(user.id)
        pending = await list_pending(user.id)
        system_prompt = build_system_prompt(user, history, idea, pending)

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_OUTPUT_TOKENS,
            system=system_prompt,
            messages=_normalize(history),
        )
        text_blocks = [block.text for block in response.content if block.type == "text"]
        assistant_message = "".join(text_blocks).strip()

        await append_message(
            user.id,
            "assistant",
            assistant_message,
            language=user.language,
            prompt_version=BASE_VERSION,
        )
        return assistant_message

    async def run_profile_extraction(self, user: User) -> None:
        """Pull profile fields from history and write them to the users row."""
        history = await list_recent(user.id, limit=_EXTRACTION_HISTORY_LIMIT)
        data = await extract_profile(self._client, history, self._model)
        if data is None:
            logger.warning("profile extraction returned nothing", extra={"user_id": user.id})
            return
        await update_profile(user.id, data, mark_onboarded=True)
        logger.info("profile extracted and stored", extra={"user_id": user.id})

    async def run_idea_extraction(self, user: User) -> None:
        """Pull idea fields from history, upsert active idea, log a pivot if the title changed."""
        history = await list_recent(user.id, limit=_EXTRACTION_HISTORY_LIMIT)
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
