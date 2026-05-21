"""Conversation engine: persists messages, builds context, calls Anthropic, runs extraction.

Phase 1b: history lives in Supabase. After every reply, the bot inspects markers and may ask
the engine to run profile or idea extraction — separate LLM calls that read the same history.
"""

from __future__ import annotations

import logging

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from app.config import Settings
from app.conversation.context_builder import build_system_prompt
from app.conversation.extraction import extract_idea, extract_profile
from app.conversation.prompts.base_en import VERSION as BASE_VERSION
from app.database.conversations import append_message, list_recent
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
        system_prompt = build_system_prompt(user, history, idea)

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
        """Pull idea fields from history and upsert the active idea."""
        history = await list_recent(user.id, limit=_EXTRACTION_HISTORY_LIMIT)
        data = await extract_idea(self._client, history, self._model)
        if data is None:
            logger.warning("idea extraction returned nothing", extra={"user_id": user.id})
            return
        await upsert_active_idea(user.id, data)
        logger.info("idea extracted and stored", extra={"user_id": user.id})
