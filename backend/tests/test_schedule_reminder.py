from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest

from app.homework.followup import schedule_user_reminder

_TIRANE = ZoneInfo("Europe/Tirane")


@pytest.mark.asyncio
async def test_schedule_user_reminder_delivers_when_already_due() -> None:
    bot = AsyncMock()
    past = datetime.now(UTC) - timedelta(minutes=1)
    with (
        patch(
            "app.homework.followup.create_reminder",
            new_callable=AsyncMock,
            return_value="hw-1",
        ) as mock_create,
        patch(
            "app.homework.followup.deliver_followup",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_deliver,
        patch(
            "app.homework.followup.mark_reminder_sent",
            new_callable=AsyncMock,
        ) as mock_mark,
    ):
        await schedule_user_reminder(bot, "user-1", 12345, past, "Ping")

    mock_create.assert_awaited_once_with("user-1", past, "Ping")
    mock_deliver.assert_awaited_once_with(bot, 12345, "Ping")
    mock_mark.assert_awaited_once_with("hw-1")


@pytest.mark.asyncio
async def test_schedule_user_reminder_waits_when_future() -> None:
    bot = AsyncMock()
    future = datetime.now(_TIRANE) + timedelta(hours=2)
    with (
        patch(
            "app.homework.followup.create_reminder",
            new_callable=AsyncMock,
            return_value="hw-2",
        ),
        patch(
            "app.homework.followup.deliver_followup",
            new_callable=AsyncMock,
        ) as mock_deliver,
        patch(
            "app.homework.followup.mark_reminder_sent",
            new_callable=AsyncMock,
        ) as mock_mark,
    ):
        await schedule_user_reminder(bot, "user-1", 12345, future, "Later")

    mock_deliver.assert_not_awaited()
    mock_mark.assert_not_awaited()
