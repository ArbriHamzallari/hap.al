"""Per-user and global LLM call limits (CLAUDE.md §9.4 / §12)."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import UTC, datetime


class LlmLimitExceeded(Exception):
    """Raised when a user or global LLM budget limit is hit."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


# Rough Haiku conversation average; used only for monthly budget estimation.
_ESTIMATED_COST_PER_CALL_USD = 0.01


class LlmRateLimiter:
    """Track LLM API calls per hashed user and estimated monthly spend (in-memory, v1)."""

    def __init__(self, *, daily_per_user: int = 50, monthly_budget_usd: float = 50.0) -> None:
        self._daily_per_user = daily_per_user
        self._monthly_budget_usd = monthly_budget_usd
        self._day_hits: dict[str, list[float]] = defaultdict(list)
        self._month_key = _current_month_key()
        self._monthly_spend_usd = 0.0

    def check_and_record(self, user_hash: str) -> None:
        """Raise LlmLimitExceeded when limits would be exceeded; otherwise record the call."""
        self._roll_month_if_needed()

        if self._monthly_spend_usd + _ESTIMATED_COST_PER_CALL_USD > self._monthly_budget_usd:
            raise LlmLimitExceeded("monthly_budget")

        now = time.monotonic()
        day = self._day_hits[user_hash]
        day[:] = [t for t in day if now - t < 86400.0]
        if len(day) >= self._daily_per_user:
            raise LlmLimitExceeded("daily_user")

        day.append(now)
        self._monthly_spend_usd += _ESTIMATED_COST_PER_CALL_USD

    def _roll_month_if_needed(self) -> None:
        key = _current_month_key()
        if key != self._month_key:
            self._month_key = key
            self._monthly_spend_usd = 0.0


def _current_month_key() -> str:
    return datetime.now(UTC).strftime("%Y-%m")
