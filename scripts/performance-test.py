#!/usr/bin/env python3
"""
Performance test script for Cash Flow Bot.

Simulates 500 transactions/day load per plan.md performance requirements.
Tests transaction confirmation (<2s), summary generation (<5s), and report delivery (<60s).
"""
import asyncio
import random
import time
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.repositories.category_repository import CategoryRepository
from src.bot.repositories.transaction_repository import TransactionRepository
from src.bot.repositories.user_repository import UserRepository
from src.bot.services.report_service import ReportService
from src.bot.services.transaction_service import TransactionService
from src.config.logging import get_logger
from src.database.session import get_session
from src.database.session import init_db

logger = get_logger(__name__)


class PerformanceTest:
    """Performance testing suite for Cash Flow Bot."""

    def __init__(self):
        """Initialize performance test suite."""
        self.user_repo = UserRepository()
        self.category_repo = CategoryRepository()
        self.transaction_repo = TransactionRepository()
        self.transaction_service = TransactionService()
        self.report_service = ReportService()
        self.metrics: dict[str, list[float]] = {
            "transaction_creation": [],
            "transaction_retrieval": [],
            "summary_generation": [],
            "report_generation": [],
        }

    async def setup(self, session: AsyncSession) -> int:
        """Create test user for performance testing."""
        logger.info("Setting up performance test user")

        # Create test user
        user = await self.user_repo.create(
            session=session,
            telegram_id=999999999,
            username="perf_test_user",
            full_name="Performance Test User",
            role="staff",
            is_active=True,
        )

        logger.info("Performance test user created", user_id=user.user_id)
        return user.user_id

    async def cleanup(self, session: AsyncSession, user_id: int):
        """Clean up test data."""
        logger.info("Cleaning up performance test data")

        # Delete test transactions
        await session.execute(
            text("DELETE FROM transactions WHERE user_id = :user_id"),
            {"user_id": user_id},
        )

        # Delete test user
        await session.execute(
            text("DELETE FROM users WHERE user_id = :user_id"), {"user_id": user_id}
        )

        await session.commit()
        logger.info("Performance test cleanup completed")

    async def test_transaction_creation(
        self, session: AsyncSession, user_id: int, num_transactions: int = 500
    ) -> float:
        """
        Test transaction creation performance.
        Target: <2s per transaction (p95)
        """
        logger.info(f"Testing transaction creation ({num_transactions} transactions)")

        # Get available categories
        categories = await self.category_repo.list_all(session)
        category_ids = [cat.category_id for cat in categories if cat.category_type == "expense"]

        transactions_created = 0
        start_time = time.time()

        for i in range(num_transactions):
            tx_start = time.time()

            # Alternate between income and expense
            is_income = i % 2 == 0
            amount = Decimal(random.randint(10000, 1000000))  # nosec  # 10k to 1M Rupiah
            description = f"Performance test transaction {i + 1}"

            try:
                if is_income:
                    await self.transaction_service.record_income(
                        session=session,
                        user_id=user_id,
                        amount=amount,
                        description=description,
                    )
                else:
                    category_id = random.choice(category_ids)  # nosec
                    await self.transaction_service.record_expense(
                        session=session,
                        user_id=user_id,
                        amount=amount,
                        description=description,
                        category_id=category_id,
                    )

                tx_duration = time.time() - tx_start
                self.metrics["transaction_creation"].append(tx_duration)
                transactions_created += 1

                # Log every 100 transactions
                if (i + 1) % 100 == 0:
                    logger.info(f"Created {i + 1}/{num_transactions} transactions")

            except Exception as e:
                logger.error(f"Failed to create transaction {i + 1}", error=str(e))

        total_duration = time.time() - start_time
        avg_duration = total_duration / num_transactions if num_transactions > 0 else 0

        logger.info(
            "Transaction creation test completed",
            transactions=transactions_created,
            total_duration=f"{total_duration:.2f}s",
            avg_duration=f"{avg_duration:.4f}s",
        )

        return avg_duration

    async def test_transaction_retrieval(
        self, session: AsyncSession, user_id: int, num_queries: int = 100
    ) -> float:
        """Test transaction retrieval performance."""
        logger.info(f"Testing transaction retrieval ({num_queries} queries)")

        start_time = time.time()

        for i in range(num_queries):
            query_start = time.time()

            # Test different query patterns
            if i % 3 == 0:
                # Get recent transactions
                await self.transaction_repo.get_history(
                    session=session, user_id=user_id, limit=10, offset=0
                )
            elif i % 3 == 1:
                # Get transactions by date
                today = datetime.now().date()
                await self.transaction_repo.get_by_date_range(
                    session=session, user_id=user_id, start_date=today, end_date=today
                )
            else:
                # Get transactions with pagination
                await self.transaction_repo.get_history(
                    session=session, user_id=user_id, limit=20, offset=i * 20
                )

            query_duration = time.time() - query_start
            self.metrics["transaction_retrieval"].append(query_duration)

        total_duration = time.time() - start_time
        avg_duration = total_duration / num_queries if num_queries > 0 else 0

        logger.info(
            "Transaction retrieval test completed",
            queries=num_queries,
            total_duration=f"{total_duration:.2f}s",
            avg_duration=f"{avg_duration:.4f}s",
        )

        return avg_duration

    async def test_summary_generation(
        self, session: AsyncSession, user_id: int, num_summaries: int = 50
    ) -> float:
        """
        Test daily summary generation performance.
        Target: <5s for 500 transactions
        """
        logger.info(f"Testing summary generation ({num_summaries} summaries)")

        start_time = time.time()

        for i in range(num_summaries):
            summary_start = time.time()

            # Generate summary for today
            today = datetime.now().date()
            await self.report_service.generate_daily_summary(
                session=session, user_id=user_id, date=today
            )

            summary_duration = time.time() - summary_start
            self.metrics["summary_generation"].append(summary_duration)

            if (i + 1) % 10 == 0:
                logger.info(f"Generated {i + 1}/{num_summaries} summaries")

        total_duration = time.time() - start_time
        avg_duration = total_duration / num_summaries if num_summaries > 0 else 0

        logger.info(
            "Summary generation test completed",
            summaries=num_summaries,
            total_duration=f"{total_duration:.2f}s",
            avg_duration=f"{avg_duration:.4f}s",
        )

        return avg_duration

    async def test_report_generation(
        self, session: AsyncSession, user_id: int, num_reports: int = 20
    ) -> float:
        """
        Test report generation and formatting performance.
        Target: <60s for full report
        """
        logger.info(f"Testing report generation ({num_reports} reports)")

        start_time = time.time()

        for _ in range(num_reports):
            report_start = time.time()

            # Generate comprehensive report
            today = datetime.now().date()
            await self.report_service.generate_daily_report(session=session, date=today)

            report_duration = time.time() - report_start
            self.metrics["report_generation"].append(report_duration)

        total_duration = time.time() - start_time
        avg_duration = total_duration / num_reports if num_reports > 0 else 0

        logger.info(
            "Report generation test completed",
            reports=num_reports,
            total_duration=f"{total_duration:.2f}s",
            avg_duration=f"{avg_duration:.4f}s",
        )

        return avg_duration

    def calculate_percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile value from data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def print_results(self):
        """Print performance test results."""
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST RESULTS")
        print("=" * 80)

        for metric_name, values in self.metrics.items():
            if not values:
                continue

            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            p50 = self.calculate_percentile(values, 50)
            p95 = self.calculate_percentile(values, 95)
            p99 = self.calculate_percentile(values, 99)

            print("\n{metric_name.upper().replace('_', ' ')}")
            print("  Samples: {len(values)}")
            print("  Average: {avg* 1000:.2f}ms")
            print("  Min: {min_val* 1000:.2f}ms")
            print("  Max: {max_val* 1000:.2f}ms")
            print("  P50: {p50 * 1000:.2f}ms")
            print("  P95: {p95 * 1000:.2f}ms")
            print("  P99: {p99 * 1000:.2f}ms")

            # Check against targets
            if metric_name == "transaction_creation" and p95 > 2.0:
                print("  ⚠️  WARNING: P95 ({p95:.2f}s) exceeds target (<2s)")
            elif metric_name == "summary_generation" and p95 > 5.0:
                print("  ⚠️  WARNING: P95 ({p95:.2f}s) exceeds target (<5s)")
            elif metric_name == "report_generation" and p95 > 60.0:
                print("  ⚠️  WARNING: P95 ({p95:.2f}s) exceeds target (<60s)")
            else:
                print("  ✅ PASS: Within performance target")

        print("\n" + "=" * 80)


async def main():
    """Run performance test suite."""
    print("Starting Cash Flow Bot Performance Test")
    print("=" * 80)
    print("Configuration:")
    print("  - Transactions: 500 (simulating daily load)")
    print("  - Queries: 100 (retrieval tests)")
    print("  - Summaries: 50 (generation tests)")
    print("  - Reports: 20 (full report tests)")
    print("=" * 80)

    # Initialize database
    await init_db()

    # Create test instance
    perf_test = PerformanceTest()

    try:
        async with get_session() as session:
            # Setup
            user_id = await perf_test.setup(session)

            # Run tests
            print("\n[1/4] Testing transaction creation...")
            await perf_test.test_transaction_creation(session, user_id, num_transactions=500)

            print("\n[2/4] Testing transaction retrieval...")
            await perf_test.test_transaction_retrieval(session, user_id, num_queries=100)

            print("\n[3/4] Testing summary generation...")
            await perf_test.test_summary_generation(session, user_id, num_summaries=50)

            print("\n[4/4] Testing report generation...")
            await perf_test.test_report_generation(session, user_id, num_reports=20)

            # Cleanup
            await perf_test.cleanup(session, user_id)

        # Print results
        perf_test.print_results()

        print("\n✅ Performance test completed successfully")

    except Exception as e:
        print("\n❌ Performance test failed: {e}")
        logger.exception("Performance test failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
