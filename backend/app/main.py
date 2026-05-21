"""FastAPI app entrypoint for webhook mode and health checks.

Phase 0 runs the bot in polling mode via `python -m app.bot`; this module is only used
for production webhooks (Phase 2+) and local health checks. Both entrypoints share
`init_sentry` from `app.utils.observability`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.utils.observability import init_sentry

settings = get_settings()
init_sentry(settings)

app = FastAPI(title="Hap", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Public health check for Railway and load balancers."""
    return {"status": "ok"}


if settings.app_env == "development":

    @app.get("/sentry-debug")
    async def trigger_error() -> None:
        """Verify Sentry error + performance reporting (development only)."""
        _ = 1 / 0
