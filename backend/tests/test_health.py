import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint provides basic app info and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "RuleLens"
    assert "tagline" in data
    assert data["health"] == "/api/health"


def test_health_endpoint_structure():
    """Verify /api/health endpoint returns correct structure and honest status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] in ["healthy", "standalone", "degraded", "unhealthy"]

    # App info
    assert "app" in data
    assert data["app"]["name"] == "RuleLens"

    # Database status
    assert "database" in data
    assert "connected" in data["database"]
    assert "latency_ms" in data["database"]

    # Corpus status
    assert "corpus" in data
    assert "loaded" in data["corpus"]
    assert "chunks_count" in data["corpus"]


def test_config_isolation():
    """Verify settings are cleanly loaded from environment/defaults."""
    assert settings.APP_NAME == "RuleLens"
    assert settings.EMBEDDING_MODEL == "BAAI/bge-small-en-v1.5"
    assert settings.EMBEDDING_DIMENSION == 384
    assert isinstance(settings.CORS_ORIGINS, list)
