from unittest.mock import AsyncMock, patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _settings(**overrides: object) -> Settings:
    base = {
        "telegram_bot_token": "1:test",
        "anthropic_api_key": "sk-test",
        "supabase_url": "https://example.supabase.co",
        "supabase_service_key": "service-key",
        "telegram_id_hash_salt": "salt",
        "encryption_key": Fernet.generate_key().decode(),
        "app_env": "development",
        "use_polling": True,
        "internal_cron_secret": "cron-secret",
        "telegram_webhook_secret": "webhook-secret",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _mock_ptb() -> AsyncMock:
    mock_ptb = AsyncMock()
    mock_ptb.initialize = AsyncMock()
    mock_ptb.start = AsyncMock()
    mock_ptb.stop = AsyncMock()
    mock_ptb.shutdown = AsyncMock()
    mock_ptb.bot = object()
    return mock_ptb


def test_process_followups_requires_auth() -> None:
    with (
        patch("app.main.get_settings", return_value=_settings()),
        patch("app.main.build_application", return_value=_mock_ptb()),
    ):
        with TestClient(create_app()) as client:
            r = client.post("/internal/process-followups")
        assert r.status_code == 403


def test_process_followups_ok() -> None:
    with (
        patch("app.main.get_settings", return_value=_settings()),
        patch("app.main.build_application", return_value=_mock_ptb()),
        patch("app.main.process_due_followups", new_callable=AsyncMock) as mock_proc,
    ):
        mock_proc.return_value = 2
        with TestClient(create_app()) as client:
            r = client.post(
                "/internal/process-followups",
                headers={"Authorization": "Bearer cron-secret"},
            )
        assert r.status_code == 200
        assert r.json() == {"sent": 2}
