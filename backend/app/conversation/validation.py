"""Deep validation pass via Sonnet 4.6 + Anthropic's server-side web search tool.

Triggered when the LLM emits [VALIDATE] (typically once the user's idea is substantially
formed). The bot calls `validate_idea`, which:

1. Asks Sonnet 4.6 to use the web_search tool to find real competitors
2. Returns structured JSON: validation_score, strengths, weaknesses, competitor_summary,
   market_saturation
3. The engine writes the fields back to the ideas row and logs a journey event so the
   competitor landscape is available in future system prompts (see context_builder).

Web search runs server-side at Anthropic; no extra API key on our end. Cost is Sonnet
pricing plus per-search billing. Use sparingly — see the prompt rules in base_en.py.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import AsyncAnthropic

from app.database.models import Idea, User

logger = logging.getLogger("hap.validation")

_MAX_WEB_SEARCHES = 5
_MAX_OUTPUT_TOKENS = 4096

# Typed Any: the server-side web_search tool has no typed param in the Anthropic SDK,
# so a plain dict is passed straight through to messages.create(tools=...).
_WEB_SEARCH_TOOL: Any = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": _MAX_WEB_SEARCHES,
}

_VALIDATION_PROMPT = """You are a startup validation analyst working with Hap, the AI \
co-founder bot.

The user has shared a business idea. Your job is a deep, HONEST validation pass that uses real \
web data — not generic advice.

Process:

1. Use the web_search tool 2-5 times to find direct AND adjacent competitors. Make searches \
specific to the user's market and region (often Albania / Western Balkans — check ABOUT THIS \
USER below). Look for:
   - Direct competitors offering similar core value
   - Adjacent solutions or substitutes
   - Recent press, reviews, or complaints about that market

2. From the search results, form a view on:
   - Saturation: crowded, partially served, or open?
   - What 2-3 competitors are doing RIGHT — specific patterns worth learning from
   - What 2-3 competitors are doing WRONG — gaps the user could exploit
   - Whether the user's specific profile (skills, finances, time, location) is a fit

3. Score the idea 0-100. Be honest:
   - 0-30: fundamentally weak (no clear customer, no business model, saturated with no edge)
   - 31-60: has potential but missing key pieces
   - 61-80: solid with execution risk
   - 81-100: rare — exceptional fit plus market

Return ONLY a single JSON object — no markdown fences, no preamble, no commentary. Use empty \
arrays or null for missing fields. NEVER fabricate competitors; if your searches turned up \
nothing real, say so honestly in competitor_summary and adjust the score.

{
  "validation_score": 0-100 integer,
  "strengths": ["3-5 short strings"],
  "weaknesses": ["3-5 short strings"],
  "competitor_summary": "3-6 sentences naming actual competitors, what they do right and \
wrong, where the gap is — or saying clearly that you couldn't find competitors in this niche \
and what that signals",
  "market_saturation": "saturated" | "partial" | "open"
}"""


async def validate_idea(
    client: AsyncAnthropic,
    user: User,
    idea: Idea,
    model: str,
) -> dict[str, Any] | None:
    """Run a Sonnet 4.6 web-search validation pass. Returns the parsed JSON or None on failure."""
    context_message = (
        f"## ABOUT THIS USER\n{_format_user(user)}\n\n"
        f"## THEIR IDEA\n{_format_idea(idea)}\n\n"
        "Run the validation now and return only the JSON."
    )

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=_MAX_OUTPUT_TOKENS,
            system=_VALIDATION_PROMPT,
            messages=[{"role": "user", "content": context_message}],
            # The server-side web_search tool has no typed param in the SDK; pass the dict.
            tools=[_WEB_SEARCH_TOOL],
        )
    except Exception:
        logger.exception("validation LLM call failed")
        return None

    text = "".join(
        getattr(b, "text", "")
        for b in response.content
        if getattr(b, "type", "") == "text"
    )
    return _parse_json(text)


def _format_user(user: User) -> str:
    parts = []
    if user.first_name:
        parts.append(f"First name: {user.first_name}")
    if user.location:
        parts.append(f"Location: {user.location}")
    if user.skills:
        parts.append(f"Skills: {', '.join(user.skills)}")
    if user.experience_level:
        parts.append(f"Building experience: {user.experience_level}")
    if user.financial_situation:
        parts.append(f"Financial situation: {user.financial_situation}")
    if user.time_availability:
        parts.append(f"Time available: {user.time_availability}")
    if user.has_day_job is True:
        parts.append("Has a day job: yes")
    elif user.has_day_job is False:
        parts.append("Has a day job: no")
    if user.motivation:
        parts.append(f"Motivation: {user.motivation}")
    if user.fears:
        parts.append(f"Fears: {user.fears}")
    return "\n".join(parts) if parts else "(profile incomplete)"


def _format_idea(idea: Idea) -> str:
    parts = []
    if idea.title:
        parts.append(f"Title: {idea.title}")
    if idea.description:
        parts.append(f"Description: {idea.description}")
    if idea.target_customer:
        parts.append(f"Target customer: {idea.target_customer}")
    if idea.problem_solved:
        parts.append(f"Problem solved: {idea.problem_solved}")
    if idea.business_model:
        parts.append(f"Business model: {idea.business_model}")
    if idea.unique_advantage:
        parts.append(f"Unique advantage: {idea.unique_advantage}")
    parts.append(f"Stage: {idea.current_stage}")
    return "\n".join(parts)


def _parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        match = re.match(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end < start:
        logger.warning("validation returned no JSON-like braces")
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        logger.warning("validation returned non-JSON", extra={"head": text[:200]})
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed
