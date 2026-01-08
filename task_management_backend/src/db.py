import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _get_database_url() -> Optional[str]:
    """
    Internal helper to fetch database connection string from environment.

    We intentionally support both DATABASE_URL and DB_URL to reduce friction
    across different deployment setups.
    """
    return os.getenv("DATABASE_URL") or os.getenv("DB_URL")


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Create and return a SQLAlchemy Engine for the configured PostgreSQL database.

    Environment variables:
      - DATABASE_URL (preferred) or DB_URL: e.g. postgresql+psycopg2://user:pass@host:port/db

    Returns:
        sqlalchemy.engine.Engine: Engine configured for connection pooling.

    Raises:
        RuntimeError: If no database URL is configured.
    """
    db_url = _get_database_url()
    if not db_url:
        raise RuntimeError(
            "Database URL not configured. Please set DATABASE_URL (preferred) or DB_URL."
        )

    # Normalize common postgres URL scheme if provided without driver.
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Pool sizing kept conservative for a template app; can be overridden later.
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    )
