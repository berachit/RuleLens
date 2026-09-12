from fastapi import APIRouter
from app.config import settings
from app.db.session import check_db_connection
from app.services.redis_client import redis_manager
from app.services.retrieval import retrieval_service

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """Health check endpoint evaluating application, database, cache, and corpus index states."""
    db_connected, db_latency, db_error = check_db_connection()
    redis_connected, redis_latency, redis_error = redis_manager.ping()
    corpus_chunks_count = len(retrieval_service._corpus)

    # Overall system health:
    # If DB and Redis are connected: healthy
    # If DB connected but Redis offline: degraded
    # If DB offline but local corpus index is loaded: standalone (active)
    # If neither: unhealthy
    if db_connected:
        overall_status = "healthy" if (redis_connected or not settings.REDIS_ENABLED) else "degraded"
    elif corpus_chunks_count > 0:
        overall_status = "standalone"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "app": {
            "name": settings.APP_NAME,
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "corpus": {
            "loaded": corpus_chunks_count > 0,
            "chunks_count": corpus_chunks_count,
        },
        "database": {
            "connected": db_connected,
            "latency_ms": db_latency,
            "error": db_error,
        },
        "redis": {
            "enabled": settings.REDIS_ENABLED,
            "connected": redis_connected,
            "latency_ms": redis_latency,
            "error": redis_error,
        },
    }
