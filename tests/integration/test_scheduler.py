"""Integration tests for scheduler configuration.

Following TDD: Tests written FIRST to ensure scheduler configures correctly for WITA time.
Tests scheduler configuration, job registration, and timezone handling.
Note: Actual time-based triggering requires freezegun which is incompatible with Python 3.13.
"""
import asyncio
from unittest.mock import AsyncMock

import pytest
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scheduler.daily_report import configure_daily_report_scheduler


class TestSchedulerIntegration:
    """Integration tests for daily report scheduler configuration."""

    @pytest.mark.asyncio
    async def test_scheduler_configuration_with_wita_timezone(self):
        """Should configure scheduler with WITA timezone per US4."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        scheduler = AsyncIOScheduler()
        mock_job = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job)

        # Assert
        assert scheduler.timezone == wita
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "daily_report_midnight_wita"

    @pytest.mark.asyncio
    async def test_scheduler_job_trigger_configuration(self):
        """Should configure CronTrigger for midnight (00:00) WITA."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_job = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job)

        # Assert
        jobs = scheduler.get_jobs()
        job = jobs[0]
        assert isinstance(job.trigger, CronTrigger)
        # Verify trigger is set for midnight
        trigger_str = str(job.trigger)
        assert "0 0 " in trigger_str or "hour='0'" in trigger_str

    @pytest.mark.asyncio
    async def test_scheduler_job_replacement(self):
        """Should replace existing job when reconfigured."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_job_1 = AsyncMock()
        mock_job_2 = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job_1)
        configure_daily_report_scheduler(scheduler, mock_job_2)

        # Assert
        jobs = scheduler.get_jobs()
        # Should have daily_report_midnight_wita job with mock_job_2
        job = [j for j in jobs if j.id == "daily_report_midnight_wita"][-1]
        assert job.func == mock_job_2

    @pytest.mark.asyncio
    async def test_scheduler_timezone_stability(self):
        """Should maintain WITA timezone regardless of system timezone."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        scheduler = AsyncIOScheduler()
        mock_job = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job)

        # Assert
        assert scheduler.timezone == wita
        # WITA is UTC+8 fixed (no current DST)

    @pytest.mark.asyncio
    async def test_scheduler_misfire_grace_time(self):
        """Should have grace period for missed triggers."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_job = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job)

        # Assert
        jobs = scheduler.get_jobs()
        job = jobs[0]
        # APScheduler uses misfire_grace_time
        assert hasattr(job, "misfire_grace_time")
        # Should have 5 minute grace period (300 seconds)
        assert job.misfire_grace_time == 300

    @pytest.mark.asyncio
    async def test_scheduler_start_and_shutdown(self):
        """Should start and shutdown cleanly."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        scheduler = AsyncIOScheduler(timezone=wita)
        mock_job = AsyncMock()

        configure_daily_report_scheduler(scheduler, mock_job)

        # Act & Assert - Should not raise exceptions
        try:
            scheduler.start()
            await asyncio.sleep(0.1)  # Brief wait
            scheduler.shutdown(wait=False)
        except Exception as e:
            pytest.fail(f"Scheduler lifecycle failed: {e}")

    @pytest.mark.asyncio
    async def test_scheduler_job_metadata(self):
        """Should set descriptive job name and ID."""
        # Arrange
        scheduler = AsyncIOScheduler()
        mock_job = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job)

        # Assert
        jobs = scheduler.get_jobs()
        job = jobs[0]
        assert job.id == "daily_report_midnight_wita"
        assert job.name == "Daily Financial Report Generation"
