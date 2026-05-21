"""Sentry initialization shared by the bot (polling) and the FastAPI app (webhook).

CLAUDE.md §9.7: PII must not flow into error reports. `send_default_pii=False` strips
request bodies, headers, and `request.user` from events. Add explicit context only via
`sentry_sdk.set_context()` and only after running it through our log redactor.
"""

from __future__ import annotations

import sentry_sdk

from app.config import Settings


def init_sentry(settings: Settings) -> None:
    """No-op when SENTRY_DSN is unset."""
    if not settings.sentry_dsn:
        return
    traces_sample_rate = 1.0 if settings.app_env == "development" else 0.2
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        send_default_pii=False,
        traces_sample_rate=traces_sample_rate,
    )
