"""Health check endpoint for monitoring and service discovery."""
import asyncio
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.database.session import get_session

logger = get_logger(__name__)


class HealthChecker:
    """Health check service for monitoring application components."""

    @staticmethod
    async def check_database(session: AsyncSession) -> dict[str, Any]:
        """
        Check database connectivity and basic query execution.

        Args:
            session: SQLAlchemy async session

        Returns:
            Dict with status and latency metrics
        """
        try:
            start_time = datetime.utcnow()

            # Execute simple query
            result = await session.execute(text("SELECT 1"))
            result.scalar()

            end_time = datetime.utcnow()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "timestamp": end_time.isoformat(),
            }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    @staticmethod
    def check_application() -> dict[str, Any]:
        """
        Check application health (basic runtime checks).

        Returns:
            Dict with application status
        """
        try:
            return {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Application health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    @staticmethod
    async def perform_health_check() -> dict[str, Any]:
        """
        Perform comprehensive health check of all components.

        Returns:
            Dict with overall health status and component details

        Example:
            >>> health = await HealthChecker.perform_health_check()
            >>> print(health["overall_status"])
            'healthy'
        """
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check application
        app_health = HealthChecker.check_application()
        health_status["components"]["application"] = app_health

        # Check database
        try:
            async with get_session() as session:
                db_health = await HealthChecker.check_database(session)
                health_status["components"]["database"] = db_health
        except Exception as e:
            logger.error("Database health check failed during session creation", error=str(e))
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Determine overall status
        for component_name, component_status in health_status["components"].items():
            if component_status["status"] != "healthy":
                health_status["overall_status"] = "unhealthy"
                logger.warning(
                    "Health check detected unhealthy component",
                    component=component_name,
                    status=component_status,
                )
                break

        return health_status


async def get_health_status() -> dict[str, Any]:
    """
    Get current health status of the application.

    This function can be used by monitoring tools, load balancers,
    or orchestration systems to determine service health.

    Returns:
        Dict containing health check results

    Example:
        >>> status = await get_health_status()
        >>> if status["overall_status"] == "healthy":
        ...     print("Service is operational")
    """
    return await HealthChecker.perform_health_check()


async def main():
    """CLI entry point for health check."""
    health = await get_health_status()

    print(f"Overall Status: {health['overall_status']}")
    print(f"Timestamp: {health['timestamp']}")
    print("\nComponent Status:")

    for component, status in health["components"].items():
        print(f"  {component}: {status['status']}")
        if "latency_ms" in status:
            print(f"    Latency: {status['latency_ms']}ms")
        if status["status"] != "healthy" and "error" in status:
            print(f"    Error: {status['error']}")


if __name__ == "__main__":
    asyncio.run(main())
