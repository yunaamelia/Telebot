"""Integration tests for scheduler with time mocking.

Following TDD: Tests written FIRST to ensure scheduler triggers at correct WITA time.
Tests 24:00 WITA trigger with real scheduler instance.
"""
import asyncio
from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from freezegun import freeze_time

from src.scheduler.daily_report import configure_daily_report_scheduler


class TestSchedulerIntegration:
    """Integration tests for daily report scheduler."""

    @pytest.mark.asyncio
    async def test_scheduler_triggers_at_midnight_wita(self):
        """Should trigger daily report at 00:00 WITA per US4."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        target_time = wita.localize(datetime(2025, 12, 22, 0, 0, 0))

        scheduler = AsyncIOScheduler(timezone=wita)
        mock_job = AsyncMock()

        configure_daily_report_scheduler(scheduler, mock_job)
        scheduler.start()

        # Act - Fast-forward to midnight WITA
        with freeze_time(target_time):
            # Wait for job execution (in real test, this would be actual time passage)
            await asyncio.sleep(1)

        # Assert
        scheduler.shutdown()
        mock_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_scheduler_does_not_trigger_before_midnight(self):
        """Should not trigger before 00:00 WITA."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        before_midnight = wita.localize(datetime(2025, 12, 21, 23, 59, 0))

        scheduler = AsyncIOScheduler(timezone=wita)
        mock_job = AsyncMock()

        configure_daily_report_scheduler(scheduler, mock_job)
        scheduler.start()

        # Act
        with freeze_time(before_midnight):
            await asyncio.sleep(1)

        # Assert
        scheduler.shutdown()
        mock_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_scheduler_handles_dst_transitions(self):
        """Should handle daylight saving transitions (WITA has no DST but test anyway)."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        # WITA doesn't observe DST, but verify timezone remains stable

        scheduler = AsyncIOScheduler(timezone=wita)
        mock_job = AsyncMock()

        # Act
        configure_daily_report_scheduler(scheduler, mock_job)

        # Assert
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        # Timezone should remain Asia/Makassar regardless of date
        assert scheduler.timezone == wita

    @pytest.mark.asyncio
    async def test_scheduler_triggers_daily(self):
        """Should trigger once per day consistently."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        day1 = wita.localize(datetime(2025, 12, 22, 0, 0, 0))
        day2 = day1 + timedelta(days=1)

        scheduler = AsyncIOScheduler(timezone=wita)
        call_count = 0

        async def count_calls():
            nonlocal call_count
            call_count += 1

        configure_daily_report_scheduler(scheduler, count_calls)
        scheduler.start()

        # Act - Simulate two midnight triggers
        with freeze_time(day1):
            await asyncio.sleep(0.1)

        with freeze_time(day2):
            await asyncio.sleep(0.1)

        # Assert
        scheduler.shutdown()
        assert call_count == 2  # One call per day

    @pytest.mark.asyncio
    async def test_scheduler_recovers_from_missed_trigger(self):
        """Should handle missed triggers if system was down per FR-024."""
        # Arrange
        wita = pytz.timezone("Asia/Makassar")
        scheduler = AsyncIOScheduler(timezone=wita)
        mock_job = AsyncMock()

        configure_daily_report_scheduler(scheduler, mock_job)

        # Act - Scheduler starts after midnight (missed trigger)
        late_start = wita.localize(datetime(2025, 12, 22, 1, 0, 0))
        with freeze_time(late_start):
            scheduler.start()
            await asyncio.sleep(0.1)

        # Assert - Should not execute missed job immediately
        # (manual recovery via /report command per FR-024)
        scheduler.shutdown()
        mock_job.assert_not_called()
