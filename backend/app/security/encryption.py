"""Field-level Fernet encryption for sensitive `users` columns.

CLAUDE.md §9.5 / §9.6: `financial_situation`, `personality_notes`, `fears` are encrypted
at rest. The key lives in the ENCRYPTION_KEY env var. This is defense-in-depth against
leaked DB backups, not a magic shield (the key sits next to the app in env vars).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

logger = logging.getLogger("hap.security.encryption")

ENCRYPTED_USER_FIELDS = ("financial_situation", "personality_notes", "fears")


class FieldCrypto:
    """Fernet wrapper for round-tripping plaintext strings to/from the DB."""

    def __init__(self, key: bytes) -> None:
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str | None:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.warning("decrypt failed: invalid token (key rotated or ciphertext corrupted)")
            return None


@lru_cache(maxsize=1)
def get_crypto() -> FieldCrypto:
    settings = get_settings()
    return FieldCrypto(settings.encryption_key.get_secret_value().encode())


def decrypt_user_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `row` with the three encrypted fields decrypted in place."""
    crypto = get_crypto()
    out = dict(row)
    for field_name in ENCRYPTED_USER_FIELDS:
        v = out.get(field_name)
        if v:
            out[field_name] = crypto.decrypt(v)
    return out


def encrypt_user_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `data` with the sensitive fields encrypted (if present)."""
    crypto = get_crypto()
    out = dict(data)
    for field_name in ENCRYPTED_USER_FIELDS:
        v = out.get(field_name)
        if v is not None:
            out[field_name] = crypto.encrypt(str(v))
    return out
