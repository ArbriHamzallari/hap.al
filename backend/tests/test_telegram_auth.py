from app.security.telegram_auth import verify_internal_cron, verify_telegram_webhook


class _FakeRequest:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def test_verify_telegram_webhook() -> None:
    req = _FakeRequest({"X-Telegram-Bot-Api-Secret-Token": "secret"})
    assert verify_telegram_webhook(req, "secret") is True  # type: ignore[arg-type]
    assert verify_telegram_webhook(req, "wrong") is False  # type: ignore[arg-type]


def test_verify_internal_cron_bearer() -> None:
    req = _FakeRequest({"Authorization": "Bearer cron-secret"})
    assert verify_internal_cron(req, "cron-secret") is True  # type: ignore[arg-type]
