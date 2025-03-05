"""Application event handlers and health checks."""

from typing import Callable

from app.core.database import engine
from app.core.logging_config import logger
from fastapi import FastAPI, Response, status
from sqlalchemy import text
from tenacity import retry, stop_after_attempt, wait_exponential


def create_start_app_handler(app: FastAPI) -> Callable:
    """Create a handler for application startup events."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _check_db_connection() -> None:
        """Verify database connection."""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def start_app() -> None:
        """Initialize application services."""
        try:
            _check_db_connection()
            logger.info("Application startup complete")
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            raise

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """Create a handler for application shutdown events."""

    def stop_app() -> None:
        """Clean up application resources."""
        try:
            engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise

    return stop_app


def check_database_health() -> bool:
    """Check database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_api_health() -> bool:
    """Check API health."""
    return True  # Add more comprehensive checks as needed


def setup_healthcheck(app: FastAPI) -> None:
    """Configure health check endpoints."""

    @app.get("/health")
    def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy"}

    @app.get("/health/live", status_code=status.HTTP_200_OK)
    def liveness_check():
        """Kubernetes liveness probe."""
        return {"status": "alive"}

    @app.get("/health/ready", status_code=status.HTTP_200_OK)
    def readiness_check(response: Response):
        """Kubernetes readiness probe."""
        is_db_healthy = check_database_health()
        is_api_healthy = check_api_health()

        if not (is_db_healthy and is_api_healthy):
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "unavailable",
                "details": {
                    "database": "healthy" if is_db_healthy else "unhealthy",
                    "api": "healthy" if is_api_healthy else "unhealthy",
                },
            }

        return {
            "status": "ready",
            "details": {
                "database": "healthy",
                "api": "healthy",
            },
        }


def setup_events(app: FastAPI) -> None:
    """Configure application event handlers."""
    app.add_event_handler("startup", create_start_app_handler(app))
    app.add_event_handler("shutdown", create_stop_app_handler(app))
    setup_healthcheck(app)
