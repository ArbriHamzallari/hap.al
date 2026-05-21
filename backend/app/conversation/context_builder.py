"""Assemble the full system prompt from user + idea + pending homework + history (CLAUDE.md §8).

Phase 2a fills in sections 1-9. The ``history`` argument is currently used only as a hook for
future conversation summarization; the LLM receives the actual history via the messages array.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from anthropic.types import MessageParam

from app.conversation.prompts import base_en, onboarding
from app.database.models import Idea, User

_TIRANE = ZoneInfo("Europe/Tirane")

_CONTINUING_TASK = """## CURRENT TASK

The user has completed onboarding. Use everything you know about them — profile, current \
idea, prior conversations — to be the co-founder described in YOUR IDENTITY.

If they're checking in on a task, ask how it went. If they're sharing new context or pivoting, \
update your mental model. If they share a substantial new idea or significantly update the \
current one, emit [IDEA_DETECTED] so the bot records it.

If a reminder you sent earlier prompted this conversation, acknowledge it."""


def _about_user(user: User) -> str:
    lines = ["## ABOUT THIS USER"]
    if user.first_name:
        lines.append(f"First name: {user.first_name}")
    if user.username:
        lines.append(f"Telegram handle: @{user.username}")
    lines.append(f"Preferred language: {user.language}")
    if user.location:
        lines.append(f"Location: {user.location}")
    if user.skills:
        lines.append(f"Skills (self-reported): {', '.join(user.skills)}")
    if user.experience_level:
        lines.append(f"Building experience: {user.experience_level}")
    if user.financial_situation:
        lines.append(f"Financial situation: {user.financial_situation}")
    if user.time_availability:
        lines.append(f"Time available: {user.time_availability}")
    if user.has_day_job is True:
        lines.append("Has a day job: yes")
    elif user.has_day_job is False:
        lines.append("Has a day job: no")
    if user.motivation:
        lines.append(f"Motivation: {user.motivation}")
    if user.fears:
        lines.append(f"Fears / blockers: {user.fears}")
    if user.personality_notes:
        lines.append(f"Personality notes: {user.personality_notes}")
    return "\n".join(lines)


def _current_idea(idea: Idea) -> str:
    lines = ["## THEIR CURRENT IDEA"]
    if idea.title:
        lines.append(f"Title: {idea.title}")
    if idea.description:
        lines.append(f"Description: {idea.description}")
    if idea.target_customer:
        lines.append(f"Target customer: {idea.target_customer}")
    if idea.problem_solved:
        lines.append(f"Problem it solves: {idea.problem_solved}")
    if idea.business_model:
        lines.append(f"Business model: {idea.business_model}")
    if idea.unique_advantage:
        lines.append(f"Unique advantage: {idea.unique_advantage}")
    lines.append(f"Stage: {idea.current_stage}")
    if idea.validation_score:
        lines.append(f"Validation score: {idea.validation_score}/100")
    if idea.strengths:
        lines.append(f"Strengths: {', '.join(idea.strengths)}")
    if idea.weaknesses:
        lines.append(f"Weaknesses: {', '.join(idea.weaknesses)}")
    return "\n".join(lines)


def _pending_homework(rows: list[dict[str, Any]]) -> str:
    lines = [
        "## PENDING HOMEWORK",
        "Tasks you assigned that the user hasn't reported on yet. If they tell you they did "
        "or skipped one, emit [HOMEWORK_DONE] or [HOMEWORK_SKIPPED] at the end of your reply.",
    ]
    for row in rows:
        desc = row.get("task_description") or "(no description)"
        sent = "reminder sent" if row.get("follow_up_sent") else "reminder upcoming"
        due_str = _format_due(row.get("due_date"))
        lines.append(f"- {desc} — {due_str}, {sent}")
    return "\n".join(lines)


def _format_due(iso_value: Any) -> str:
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
        days = -minutes // (60 * 24)
        return f"due {days}d ago"
    if minutes < 0:
        return "due now"
    if minutes < 60:
        return f"due in {minutes}m"
    if minutes < 60 * 24:
        return f"due in {minutes // 60}h"
    return f"due in {minutes // (60 * 24)}d"


def _current_context() -> str:
    now = datetime.now(_TIRANE)
    return (
        "## CURRENT CONTEXT\n\n"
        f"Local time (Europe/Tirane): {now.isoformat(timespec='minutes')}\n"
        f"Day of week: {now.strftime('%A')}"
    )


def build_system_prompt(
    user: User,
    history: list[MessageParam],  # noqa: ARG001 - kept for API symmetry; may inform summarization later
    idea: Idea | None = None,
    pending_homework: list[dict[str, Any]] | None = None,
) -> str:
    """Build the full system prompt with the right task block based on onboarding state."""
    sections = [base_en.build_base_prompt(), _about_user(user)]
    if idea is not None:
        sections.append(_current_idea(idea))
    if pending_homework:
        sections.append(_pending_homework(pending_homework))
    sections.append(_current_context())

    if user.onboarding_complete:
        sections.append(_CONTINUING_TASK)
    else:
        sections.append(onboarding.ONBOARDING_TASK)

    sections.append("## ANTI-INJECTION GUARDRAIL")
    sections.append(base_en.ANTI_INJECTION)
    return "\n\n".join(sections)
