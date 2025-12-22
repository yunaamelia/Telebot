"""E2E tests for daily report workflow.

Following TDD: Tests complete workflow from trigger to delivery.
Tests report generation, formatting, delivery, and error handling.
"""
from datetime import date
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import pytz

from src.bot.models.transaction import Transaction
from src.bot.services.report_service import ReportService
from src.scheduler.daily_report import execute_daily_report_job


class TestDailyReportE2E:
    """E2E tests for daily report generation and delivery."""

    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions for testing."""
        return [
            Transaction(
                transaction_id="TX20251222001",
                user_id=1,
                type="income",
                amount=Decimal("5000000"),
                description="Client payment",
                timestamp=datetime(2025, 12, 22, 10, 0, 0),
                category_id=None,
            ),
            Transaction(
                transaction_id="TX20251222002",
                user_id=1,
                type="expense",
                amount=Decimal("2000000"),
                description="Office rent",
                timestamp=datetime(2025, 12, 22, 14, 0, 0),
                category_id=1,
            ),
            Transaction(
                transaction_id="TX20251222003",
                user_id=1,
                type="expense",
                amount=Decimal("1500000"),
                description="Salaries",
                timestamp=datetime(2025, 12, 22, 16, 0, 0),
                category_id=2,
            ),
        ]

    @pytest.mark.asyncio
    async def test_complete_daily_report_workflow(self, sample_transactions):
        """Should generate and deliver daily report successfully per US4."""
        # Arrange
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        mock_report_service = Mock(spec=ReportService)
        mock_report_service.generate_daily_report = AsyncMock(
            return_value={
                "date": "22 Dec 2025",
                "total_income": "Rp 5,000,000",
                "total_expenses": "Rp 3,500,000",
                "net_cash_flow": "Rp 1,500,000",
                "net_cash_flow_indicator": "📈",
                "category_breakdown": "🏢 Operational: Rp 2,000,000\n👔 Salaries: Rp 1,500,000",
                "transaction_count": 3,
                "income_count": 1,
                "expense_count": 2,
            }
        )

        management_chat_id = 123456789

        # Act
        with patch("src.scheduler.daily_report.ReportService", return_value=mock_report_service):
            with patch("src.scheduler.daily_report.Bot", return_value=mock_bot):
                await execute_daily_report_job(management_chat_id)

        # Assert
        mock_report_service.generate_daily_report.assert_called_once()
        mock_bot.send_message.assert_called_once()

        # Verify message contains key elements
        call_args = mock_bot.send_message.call_args
        message_text = call_args.kwargs["text"]
        assert "Daily Financial Report" in message_text
        assert "Rp 5,000,000" in message_text
        assert "Rp 3,500,000" in message_text

    @pytest.mark.asyncio
    async def test_daily_report_handles_zero_transactions(self):
        """Should handle days with no transactions per US4 AS2."""
        # Arrange
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        mock_report_service = Mock(spec=ReportService)
        mock_report_service.generate_daily_report = AsyncMock(
            return_value={
                "date": "22 Dec 2025",
                "total_income": "Rp 0",
                "total_expenses": "Rp 0",
                "net_cash_flow": "Rp 0",
                "net_cash_flow_indicator": "ℹ️",
                "category_breakdown": "ℹ️ No expenses today",
                "transaction_count": 0,
                "income_count": 0,
                "expense_count": 0,
            }
        )

        # Act
        with patch("src.scheduler.daily_report.ReportService", return_value=mock_report_service):
            with patch("src.scheduler.daily_report.Bot", return_value=mock_bot):
                await execute_daily_report_job(123456789)

        # Assert
        mock_bot.send_message.assert_called_once()
        message_text = mock_bot.send_message.call_args.kwargs["text"]
        assert "Rp 0" in message_text or "No transactions" in message_text

    @pytest.mark.asyncio
    async def test_daily_report_retries_on_failure(self):
        """Should retry delivery on failure per FR-018."""
        # Arrange
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock(
            side_effect=[
                Exception("Network error"),
                None,  # Success on retry
            ]
        )

        # Act
        with patch("src.scheduler.daily_report.Bot", return_value=mock_bot):
            with patch("asyncio.sleep"):  # Speed up retry delays
                await execute_daily_report_job(123456789)

        # Assert
        assert mock_bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_daily_report_sends_critical_alert_on_persistent_failure(self):
        """Should alert on persistent delivery failure per FR-030."""
        # Arrange
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Persistent failure"))

        mock_alert_service = Mock()
        mock_alert_service.send_critical_alert = AsyncMock()

        # Act
        with patch("src.scheduler.daily_report.Bot", return_value=mock_bot):
            with patch("asyncio.sleep"):
                with patch(
                    "src.scheduler.daily_report.send_critical_alert",
                    mock_alert_service.send_critical_alert,
                ):
                    with pytest.raises(Exception, match="Persistent failure"):
                        await execute_daily_report_job(123456789)

        # Assert
        mock_alert_service.send_critical_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_daily_report_uses_wita_timezone(self):
        """Should generate report for correct WITA date per FR-009."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        wita_midnight = wita.localize(datetime(2025, 12, 22, 0, 0, 0))

        mock_report_service = Mock(spec=ReportService)
        mock_report_service.generate_daily_report = AsyncMock()

        # Act
        with patch("src.scheduler.daily_report.datetime") as mock_datetime:
            mock_datetime.now.return_value = wita_midnight
            with patch(
                "src.scheduler.daily_report.ReportService",
                return_value=mock_report_service,
            ):
                await execute_daily_report_job(123456789)

        # Assert
        # Should request report for 2025-12-21 (previous day)
        call_args = mock_report_service.generate_daily_report.call_args
        report_date = call_args[0][0] if call_args[0] else call_args.kwargs.get("report_date")
        assert report_date == date(2025, 12, 21)
