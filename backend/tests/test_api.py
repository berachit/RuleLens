from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_documents_endpoint():
    """Verify GET /api/documents returns active corpus documents."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) >= 4
    doc_names = [d["name"] for d in data["documents"]]
    assert "academic_regulations.md" in doc_names
    assert "scholarship_notice.md" in doc_names
    assert "fee_deadlines.md" in doc_names
    assert "attendance_circular.md" in doc_names


def test_search_regulations_endpoint():
    """Verify GET /api/search returns semantic vector search results with provenance."""
    response = client.get("/api/search?q=attendance%20requirement")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    first = data["results"][0]
    assert "page_number" in first
    assert "chunk_id" in first
    assert "document_name" in first
    assert "similarity" in first


def test_get_source_endpoint():
    """Verify GET /api/sources/{source_id} resolves an existing chunk."""
    # First find a chunk ID from search
    search_res = client.get("/api/search?q=attendance")
    chunk_id = search_res.json()["results"][0]["chunk_id"]

    source_res = client.get(f"/api/sources/{chunk_id}")
    assert source_res.status_code == 200
    source_data = source_res.json()
    assert source_data["chunk_id"] == chunk_id
    assert source_data["page_number"] > 0
