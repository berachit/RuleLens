import time
import logging
from typing import Generator, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

logger = logging.getLogger(__name__)

# Engine configuration with pooling
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    if SessionLocal is None:
        raise RuntimeError("Database engine is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Tuple[bool, float, Optional[str]]:
    """Checks database connectivity and latency."""
    if engine is None:
        return False, 0.0, "Database engine not initialized"

    start_time = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return True, latency_ms, None
    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return False, latency_ms, str(exc)
