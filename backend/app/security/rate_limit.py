"""Per-user message rate limits for the Telegram bot (CLAUDE.md §9.4)."""

from __future__ import annotations

import time
from collections import defaultdict


class UserRateLimiter:
    """Track message counts per hashed telegram id (in-memory, v1)."""

    def __init__(self, *, per_minute: int = 20, per_day: int = 200) -> None:
        self._per_minute = per_minute
        self._per_day = per_day
        self._minute_hits: dict[str, list[float]] = defaultdict(list)
        self._day_hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_hash: str) -> bool:
        """Return False when the user exceeds minute or daily limits."""
        now = time.monotonic()
        minute = self._minute_hits[user_hash]
        minute[:] = [t for t in minute if now - t < 60.0]
        if len(minute) >= self._per_minute:
            return False

        day = self._day_hits[user_hash]
        day[:] = [t for t in day if now - t < 86400.0]
        if len(day) >= self._per_day:
            return False

        minute.append(now)
        day.append(now)
        return True
