"""Tests for LLM daily and monthly budget limits."""

from __future__ import annotations

import pytest

from app.security.llm_rate_limit import LlmLimitExceeded, LlmRateLimiter


def test_daily_per_user_limit() -> None:
    limiter = LlmRateLimiter(daily_per_user=2, monthly_budget_usd=100.0)
    limiter.check_and_record("user-a")
    limiter.check_and_record("user-a")
    with pytest.raises(LlmLimitExceeded) as exc:
        limiter.check_and_record("user-a")
    assert exc.value.reason == "daily_user"


def test_daily_limit_is_per_user() -> None:
    limiter = LlmRateLimiter(daily_per_user=1, monthly_budget_usd=100.0)
    limiter.check_and_record("user-a")
    limiter.check_and_record("user-b")  # different user, still allowed


def test_monthly_budget_limit() -> None:
    limiter = LlmRateLimiter(daily_per_user=1000, monthly_budget_usd=0.01)
    limiter.check_and_record("user-a")
    with pytest.raises(LlmLimitExceeded) as exc:
        limiter.check_and_record("user-a")
    assert exc.value.reason == "monthly_budget"
