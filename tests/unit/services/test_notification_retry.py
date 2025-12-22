"""Unit tests for notification service retry logic.

Following TDD: Tests written FIRST to ensure retry mechanism works per FR-018.
Tests retry with 5-minute intervals, 30-minute maximum retry window.
"""
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from telegram.error import NetworkError
from telegram.error import TimedOut

from src.bot.services.notification_service import NotificationService


class TestNotificationServiceRetry:
    """Test notification retry logic for daily reports."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock Telegram Bot."""
        bot = Mock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def notification_service(self, mock_bot):
        """Create NotificationService with mock bot."""
        return NotificationService(mock_bot)

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, notification_service, mock_bot):
        """Should retry message delivery on network error per FR-018."""
        # Arrange
        mock_bot.send_message.side_effect = [
            NetworkError("Network failure"),
            None,  # Success on second attempt
        ]

        # Act
        await notification_service.send_daily_report_with_retry(
            chat_id=123, report_text="Test report"
        )

        # Assert
        assert mock_bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_interval_5_minutes(self, notification_service, mock_bot):
        """Should wait 5 minutes between retry attempts per FR-018."""
        # Arrange
        mock_bot.send_message.side_effect = [
            TimedOut("Timeout"),
            None,
        ]

        with patch("asyncio.sleep") as mock_sleep:
            # Act
            await notification_service.send_daily_report_with_retry(chat_id=123, report_text="Test")

            # Assert
            mock_sleep.assert_called_once_with(300)  # 5 minutes = 300 seconds

    @pytest.mark.asyncio
    async def test_max_retry_window_30_minutes(self, notification_service, mock_bot):
        """Should stop retrying after 30 minutes per FR-018."""
        # Arrange
        mock_bot.send_message.side_effect = NetworkError("Persistent failure")

        with patch("asyncio.sleep"):
            # Act & Assert
            with pytest.raises(NetworkError):
                await notification_service.send_daily_report_with_retry(
                    chat_id=123, report_text="Test"
                )

        # Should try: initial + 5 retries (0, 5, 10, 15, 20, 25 minutes = 6 attempts)
        assert mock_bot.send_message.call_count == 6

    @pytest.mark.asyncio
    async def test_no_retry_on_success(self, notification_service, mock_bot):
        """Should not retry if first attempt succeeds."""
        # Arrange
        mock_bot.send_message.return_value = None

        # Act
        await notification_service.send_daily_report_with_retry(chat_id=123, report_text="Test")

        # Assert
        assert mock_bot.send_message.call_count == 1
