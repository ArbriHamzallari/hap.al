"""FastAPI middleware: per-user rate limiting (CLAUDE.md §9.4)."""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory per-IP rate limit for webhook and internal endpoints (v1)."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        per_minute: int = 100,
    ) -> None:
        super().__init__(app)
        self._per_minute = per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self._hits[client]
        window[:] = [t for t in window if now - t < 60.0]
        if len(window) >= self._per_minute:
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        window.append(now)
        return await call_next(request)
