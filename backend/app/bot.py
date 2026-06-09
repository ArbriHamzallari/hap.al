"""Telegram bot entrypoint. Polling locally; webhook via `app.main` in production."""

from __future__ import annotations

import logging

from app.config import get_settings
from app.telegram_app import build_application
from app.utils.observability import init_sentry

logger = logging.getLogger("hap.bot")


def main() -> None:
    settings = get_settings()
    init_sentry(settings)

    if not settings.use_polling:
        raise SystemExit(
            "USE_POLLING=false: run the FastAPI app instead:\n"
            "  uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"
        )

    application = build_application(settings)
    logger.info("starting bot in polling mode", extra={"env": settings.app_env})
    application.run_polling()


if __name__ == "__main__":
    main()
