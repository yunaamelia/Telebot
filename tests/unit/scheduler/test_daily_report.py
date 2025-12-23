"""Unit tests for daily report scheduler configuration.

Following TDD: These tests are written FIRST and should FAIL until implementation.
Tests scheduler timezone configuration, job scheduling, and WITA compliance.
"""
from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scheduler.daily_report import configure_daily_report_scheduler


class TestDailyReportSchedulerConfiguration:
    """Test daily report scheduler setup and configuration."""

    @pytest.mark.asyncio
    async def test_scheduler_uses_wita_timezone(self):
        """Should configure scheduler with WITA timezone per FR-009."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_report_job = Mock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_report_job)

        # Assert
        assert scheduler.timezone == pytz.timezone("Asia/Makassar")

    @pytest.mark.asyncio
    async def test_daily_report_scheduled_at_midnight_wita(self):
        """Should schedule daily report at 24:00 (00:00) WITA per US4."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_report_job = Mock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_report_job)

        # Assert
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        job = jobs[0]

        # Verify it's a CronTrigger
        assert isinstance(job.trigger, CronTrigger)

        # Verify trigger parameters via string representation or public attributes
        # cron[hour='0', minute='0', timezone='Asia/Makassar']
        trigger_str = str(job.trigger)
        assert "hour='0'" in trigger_str
        assert "minute='0'" in trigger_str
        # Timezone check might vary in string rep, checking attribute directly is safer for objects
        assert job.trigger.timezone == pytz.timezone("Asia/Makassar")

    @pytest.mark.asyncio
    async def test_scheduler_calls_correct_job_function(self):
        """Should register the provided report job function."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_report_job = Mock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_report_job)

        # Assert
        jobs = scheduler.get_jobs()
        assert jobs[0].func == mock_report_job

    @pytest.mark.asyncio
    async def test_scheduler_job_id_is_descriptive(self):
        """Should use descriptive job ID for monitoring."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_report_job = Mock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_report_job)

        # Assert
        jobs = scheduler.get_jobs()
        assert jobs[0].id == "daily_report_midnight_wita"

    @pytest.mark.asyncio
    async def test_scheduler_replaces_existing_job(self):
        """Should replace existing job if scheduler is reconfigured."""
        # Arrange
        scheduler = Mock()
        mock_report_job_1 = Mock()
        mock_report_job_2 = Mock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_report_job_1)
        configure_daily_report_scheduler(scheduler, mock_report_job_2)

        # Assert
        # Verify add_job was called with replace_existing=True
        # We can check the last call
        scheduler.add_job.assert_called_with(
            mock_report_job_2,
            trigger=ANY,  # verifying arguments strictly might be verbose
            id="daily_report_midnight_wita",
            name="Daily Financial Report Generation",
            replace_existing=True,
            misfire_grace_time=300,
        )
        # Or simpler:
        call_args = scheduler.add_job.call_args
        assert call_args.kwargs["replace_existing"] is True
        assert call_args.kwargs["id"] == "daily_report_midnight_wita"
        assert call_args.args[0] == mock_report_job_2

    @pytest.mark.asyncio
    async def test_scheduler_handles_timezone_edge_case_23_59_59(self):
        """Should correctly handle transactions at 23:59:59 WITA per edge cases."""
        # Arrange - Simulate time just before midnight
        scheduler = AsyncIOScheduler()
        mock_report_job = Mock()

        # Use a real datetime class for mocking to avoid MagicMock tzinfo issues
        from datetime import datetime

        with patch("src.scheduler.daily_report.datetime") as mock_datetime:
            # Configure side_effect or return_value securely
            # We want datetime.now(wita) to return a specific time
            wita = pytz.timezone("Asia/Makassar")
            mock_now = wita.localize(datetime(2025, 12, 22, 23, 59, 59))
            mock_datetime.now.return_value = mock_now
            # Ensure side effects don't break other datetime usage if any

            # Act
            configure_daily_report_scheduler(scheduler, mock_report_job)

            # Assert
            jobs = scheduler.get_jobs()
            assert len(jobs) == 1
