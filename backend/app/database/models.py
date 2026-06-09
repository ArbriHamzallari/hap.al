"""Pydantic models for Supabase rows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _none_to_empty_list(v: Any) -> Any:
    """Postgres TEXT[] columns without a DEFAULT come back as None; treat that as []."""
    return [] if v is None else v


class User(BaseModel):
    """Subset of the `users` table the conversation engine cares about.

    The three encrypted columns (financial_situation, personality_notes, fears) hold
    plaintext on this object after `get_or_create_user` decrypts them.
    """

    model_config = ConfigDict(extra="ignore")

    id: str  # UUID
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    language: Literal["en", "sq"] = "en"
    onboarding_complete: bool = False

    # Profile fields, populated as onboarding completes
    skills: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    financial_situation: str | None = None  # decrypted plaintext in app
    time_availability: str | None = None
    has_day_job: bool | None = None
    location: str | None = None
    motivation: str | None = None
    fears: str | None = None  # decrypted
    personality_notes: str | None = None  # decrypted

    timezone: str = "Europe/Tirane"
    created_at: datetime | None = None
    last_active: datetime | None = None

    # Not a DB column: True only on the call that just inserted the row. Used for the
    # bot_started `is_new_user` analytics property. (created_at/last_active both default
    # to NOW() in the schema, so they can't distinguish a fresh row from a returning one.)
    is_new: bool = Field(default=False, exclude=True)

    _normalize_skills = field_validator("skills", mode="before")(_none_to_empty_list)


class Idea(BaseModel):
    """Subset of the `ideas` table the conversation engine cares about."""

    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    title: str | None = None
    description: str | None = None
    target_customer: str | None = None
    problem_solved: str | None = None
    business_model: str | None = None
    unique_advantage: str | None = None
    current_stage: str = "raw_idea"
    validation_score: int = 0
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    _normalize_strengths = field_validator("strengths", mode="before")(_none_to_empty_list)
    _normalize_weaknesses = field_validator("weaknesses", mode="before")(_none_to_empty_list)
