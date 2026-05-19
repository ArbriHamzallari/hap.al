"""Pydantic models for Supabase rows."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
