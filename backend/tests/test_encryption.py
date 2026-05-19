"""Tests for FieldCrypto + the user-row encrypt/decrypt helpers."""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.security.encryption import (
    FieldCrypto,
    decrypt_user_row,
    encrypt_user_fields,
)


def test_roundtrip() -> None:
    crypto = FieldCrypto(Fernet.generate_key())
    ciphertext = crypto.encrypt("tight")
    assert ciphertext != "tight"
    assert crypto.decrypt(ciphertext) == "tight"


def test_decrypt_invalid_token_returns_none() -> None:
    crypto = FieldCrypto(Fernet.generate_key())
    assert crypto.decrypt("not-a-real-ciphertext") is None


def test_decrypt_with_wrong_key_returns_none() -> None:
    crypto1 = FieldCrypto(Fernet.generate_key())
    crypto2 = FieldCrypto(Fernet.generate_key())
    ciphertext = crypto1.encrypt("secret")
    assert crypto2.decrypt(ciphertext) is None


def test_user_row_helpers_roundtrip() -> None:
    plaintext = {
        "id": "x",
        "financial_situation": "tight",
        "fears": "fear of failing publicly",
        "personality_notes": "cautious but driven",
        "language": "en",
    }
    encrypted = encrypt_user_fields(plaintext)
    assert encrypted["financial_situation"] != "tight"
    assert encrypted["fears"] != plaintext["fears"]
    assert encrypted["personality_notes"] != plaintext["personality_notes"]
    # Non-sensitive fields are untouched.
    assert encrypted["language"] == "en"
    assert encrypted["id"] == "x"

    decrypted = decrypt_user_row(encrypted)
    assert decrypted["financial_situation"] == "tight"
    assert decrypted["fears"] == plaintext["fears"]
    assert decrypted["personality_notes"] == plaintext["personality_notes"]


def test_encrypt_skips_none_values() -> None:
    encrypted = encrypt_user_fields({"financial_situation": None, "fears": "x"})
    assert encrypted["financial_situation"] is None
    assert encrypted["fears"] != "x"
