"""Users table CRUD with field-level encryption for sensitive columns."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.database.client import get_supabase
from app.database.models import User
from app.security.encryption import (
    ENCRYPTED_USER_FIELDS,
    decrypt_user_row,
    encrypt_user_fields,
)


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:
    """Return the user row, creating it if absent. Bumps last_active on every call."""

    def _query() -> dict[str, Any]:
        client = get_supabase()
        existing = (
            client.table("users")
            .select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            row = existing.data[0]
            client.table("users").update(
                {"last_active": datetime.now(UTC).isoformat()}
            ).eq("id", row["id"]).execute()
            return row
        inserted = (
            client.table("users")
            .insert(
                {
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name,
                }
            )
            .execute()
        )
        return inserted.data[0]

    row = await asyncio.to_thread(_query)
    row = decrypt_user_row(row)
    return User.model_validate(row)


async def get_telegram_id(user_id: str) -> int | None:
    """Look up a user's Telegram ID by their internal UUID. Used by the reminder poller."""

    def _query() -> int | None:
        client = get_supabase()
        result = (
            client.table("users")
            .select("telegram_id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return int(result.data[0]["telegram_id"])

    return await asyncio.to_thread(_query)


async def update_field(user_id: str, field: str, value: Any) -> None:
    """Update a single column. Encrypts automatically if `field` is sensitive."""
    payload: dict[str, Any] = {field: value}
    if field in ENCRYPTED_USER_FIELDS and value is not None:
        payload = encrypt_user_fields(payload)

    def _query() -> None:
        client = get_supabase()
        client.table("users").update(payload).eq("id", user_id).execute()

    await asyncio.to_thread(_query)


async def update_profile(
    user_id: str,
    profile: dict[str, Any],
    *,
    mark_onboarded: bool,
) -> None:
    """Bulk-update profile fields. Encrypts the sensitive ones, optionally flips onboarding."""
    cleaned = {k: v for k, v in profile.items() if v is not None and v != ""}
    payload = encrypt_user_fields(cleaned)
    if mark_onboarded:
        payload["onboarding_complete"] = True
    if not payload:
        return

    def _query() -> None:
        client = get_supabase()
        client.table("users").update(payload).eq("id", user_id).execute()

    await asyncio.to_thread(_query)
