"""FastAPI entrypoint: health, Telegram webhook, pg_cron follow-ups (Phase 2c)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from telegram import Update

from app.config import Settings, get_settings, validate_production_settings
from app.homework.followup import process_due_followups
from app.security.middleware import RateLimitMiddleware
from app.security.telegram_auth import verify_internal_cron, verify_telegram_webhook
from app.telegram_app import build_application
from app.utils.observability import init_sentry

logger = logging.getLogger("hap.api")

_MAX_WEBHOOK_BODY = 1_048_576  # 1 MB


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    validate_production_settings(settings)

    ptb = build_application(settings)
    await ptb.initialize()
    await ptb.start()
    app.state.ptb = ptb

    if not settings.use_polling and settings.telegram_webhook_url:
        secret = (
            settings.telegram_webhook_secret.get_secret_value()
            if settings.telegram_webhook_secret
            else None
        )
        await ptb.bot.set_webhook(
            url=settings.telegram_webhook_url,
            secret_token=secret,
            allowed_updates=Update.ALL_TYPES,
        )
        logger.info("telegram webhook registered", extra={"url": settings.telegram_webhook_url})

    yield

    # Do not clear the webhook on shutdown. During rolling deploys, the old Railway
    # process can shut down after the new one registers the webhook, leaving Telegram
    # with no webhook URL.
    await ptb.stop()
    await ptb.shutdown()


def _register_routes(application: FastAPI, settings: Settings) -> None:
    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/webhook")
    async def telegram_webhook(request: Request) -> dict[str, str]:
        """Receive Telegram updates when USE_POLLING=false."""
        if settings.telegram_webhook_secret is None:
            raise HTTPException(status_code=503, detail="webhook secret not configured")

        if not verify_telegram_webhook(
            request, settings.telegram_webhook_secret.get_secret_value()
        ):
            raise HTTPException(status_code=403, detail="invalid webhook secret")

        body = await request.body()
        if len(body) > _MAX_WEBHOOK_BODY:
            raise HTTPException(status_code=413, detail="payload too large")

        data: dict[str, Any] = await request.json()
        ptb = request.app.state.ptb
        update = Update.de_json(data, ptb.bot)
        await ptb.process_update(update)
        return {"ok": "true"}

    @application.post("/internal/process-followups")
    async def process_followups_endpoint(request: Request) -> dict[str, int]:
        """Called by Supabase pg_cron every 5 minutes (Phase 2c)."""
        if settings.internal_cron_secret is None:
            raise HTTPException(status_code=503, detail="cron secret not configured")

        if not verify_internal_cron(
            request, settings.internal_cron_secret.get_secret_value()
        ):
            raise HTTPException(status_code=403, detail="invalid cron secret")

        ptb = request.app.state.ptb
        sent = await process_due_followups(ptb.bot)
        logger.info("follow-ups processed", extra={"sent": sent})
        return {"sent": sent}


def create_app() -> FastAPI:
    settings = get_settings()
    init_sentry(settings)

    docs_kwargs: dict[str, str | None] = {}
    if settings.app_env == "production":
        docs_kwargs = {"docs_url": None, "redoc_url": None, "openapi_url": None}

    application = FastAPI(
        title="Hap",
        version="0.2.0",
        lifespan=lifespan,
        **docs_kwargs,
    )
    application.state.settings = settings
    application.add_middleware(
        RateLimitMiddleware,
        per_minute=100,
    )
    _register_routes(application, settings)
    return application


app = create_app()
