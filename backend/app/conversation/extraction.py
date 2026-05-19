"""Structured field extraction via a separate LLM call.

Triggered when the LLM emits `[ONBOARDING_DONE]` or `[IDEA_DETECTED]` in a normal reply.
The bot then calls one of these functions with the conversation history; the function asks
Haiku to return a single JSON object with the fields we want, parses it, and returns a dict.
The bot is responsible for writing the dict into Supabase.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

logger = logging.getLogger("hap.extraction")

_PROFILE_PROMPT = """You are a data extraction assistant.

The user just completed onboarding with the Hap co-founder bot. From the conversation history \
that follows, extract these fields about the user. Return ONLY a single JSON object — no \
explanation, no markdown code fences, no surrounding text.

{
  "skills": ["array of self-reported skills"],
  "location": "city or country if mentioned, else null",
  "motivation": "1-2 sentences capturing why they want to start a business",
  "fears": "1-2 sentences on what holds them back, if shared. null if not mentioned.",
  "personality_notes": "2-3 sentences summarizing their personality and mindset"
}

Use null for missing string fields, [] for missing skills. Do not invent details that aren't \
in the conversation."""

_IDEA_PROMPT = """You are a data extraction assistant.

The user just shared (or updated) a business idea with the Hap co-founder bot. From the \
conversation history that follows, extract these fields. Return ONLY a single JSON object — no \
explanation, no markdown code fences, no surrounding text.

{
  "title": "short title (3-6 words)",
  "description": "1-2 sentence description of the idea",
  "target_customer": "who would use this",
  "problem_solved": "what pain point this addresses",
  "business_model": "how it makes money, if discussed",
  "current_stage": "one of: raw_idea, exploring, validating, building"
}

Use null for fields not yet discussed. Do not invent details. If the user has only just \
mentioned an idea casually, current_stage is 'raw_idea'."""


async def extract_profile(
    client: AsyncAnthropic,
    history: list[MessageParam],
    model: str,
) -> dict[str, Any] | None:
    """One-shot profile extraction from onboarding history."""
    return await _extract(client, history, model, _PROFILE_PROMPT)


async def extract_idea(
    client: AsyncAnthropic,
    history: list[MessageParam],
    model: str,
) -> dict[str, Any] | None:
    """One-shot idea extraction from recent conversation."""
    return await _extract(client, history, model, _IDEA_PROMPT)


async def _extract(
    client: AsyncAnthropic,
    history: list[MessageParam],
    model: str,
    system_prompt: str,
) -> dict[str, Any] | None:
    if not history:
        return None
    try:
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=_ensure_user_last(history),
        )
        text = "".join(b.text for b in response.content if b.type == "text")
    except Exception:
        logger.exception("extraction LLM call failed")
        return None
    return _parse_json(text)


def _ensure_user_last(history: list[MessageParam]) -> list[MessageParam]:
    """Anthropic requires the last message to be from the user. Append a stub if needed."""
    if history and history[-1]["role"] == "assistant":
        return [*history, {"role": "user", "content": "(Extract the fields now.)"}]
    return list(history)


def _parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    # Strip markdown code fences if the model added them despite instructions.
    if text.startswith("```"):
        match = re.match(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end < start:
        logger.warning("extraction returned no JSON-like braces")
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        logger.warning("extraction returned non-JSON output", extra={"head": text[:200]})
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed
