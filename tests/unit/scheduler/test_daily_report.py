"""Unit tests for daily report scheduler configuration.

Following TDD: These tests are written FIRST and should FAIL until implementation.
Tests scheduler timezone configuration, job scheduling, and WITA compliance.
"""
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

        # Verify scheduled for midnight
        assert job.trigger.fields[0].expressions[0].step == 0  # hour=0
        assert job.trigger.fields[1].expressions[0].step == 0  # minute=0

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
        scheduler = AsyncIOScheduler()
        mock_report_job_1 = Mock()
        mock_report_job_2 = Mock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_report_job_1)
        configure_daily_report_scheduler(scheduler, mock_report_job_2)

        # Assert
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1  # Should only have one job
        assert jobs[0].func == mock_report_job_2

    @pytest.mark.asyncio
    async def test_scheduler_handles_timezone_edge_case_23_59_59(self):
        """Should correctly handle transactions at 23:59:59 WITA per edge cases."""
        # Arrange - Simulate time just before midnight
        scheduler = AsyncIOScheduler()
        mock_report_job = Mock()

        with patch("src.scheduler.daily_report.datetime") as mock_datetime:
            # Mock current time as 23:59:59 WITA
            wita = pytz.timezone("Asia/Makassar")
            mock_datetime.now.return_value = wita.localize(mock_datetime(2025, 12, 22, 23, 59, 59))

            # Act
            configure_daily_report_scheduler(scheduler, mock_report_job)

            # Assert
            jobs = scheduler.get_jobs()
            # Should be scheduled for next midnight, not immediately
            assert len(jobs) == 1
