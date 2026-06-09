"""Production startup validation and API surface hardening."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from app.config import Settings, validate_production_settings
from app.main import create_app


def _prod_settings(**overrides: object) -> Settings:
    base = {
        "telegram_bot_token": "test-token",
        "anthropic_api_key": "test-key",
        "supabase_url": "http://test.local",
        "supabase_service_key": "service-key",
        "telegram_id_hash_salt": "salt",
        "encryption_key": Fernet.generate_key().decode(),
        "app_env": "production",
        "use_polling": False,
        "telegram_webhook_secret": "webhook-secret",
        "telegram_webhook_url": "https://example.com/webhook",
        "internal_cron_secret": "cron-secret",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_validate_production_settings_ok() -> None:
    validate_production_settings(_prod_settings())


def test_validate_production_rejects_polling() -> None:
    with pytest.raises(RuntimeError, match="USE_POLLING"):
        validate_production_settings(_prod_settings(use_polling=True))


def test_validate_production_requires_webhook_secret() -> None:
    with pytest.raises(RuntimeError, match="TELEGRAM_WEBHOOK_SECRET"):
        validate_production_settings(_prod_settings(telegram_webhook_secret=None))


def test_production_app_hides_openapi_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("USE_POLLING", "false")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "webhook-secret")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setenv("INTERNAL_CRON_SECRET", "cron-secret")

    application = create_app()
    assert application.docs_url is None
    assert application.openapi_url is None
