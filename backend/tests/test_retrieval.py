from app.services.retrieval import retrieval_service


def test_retrieval_attendance():
    """Verify semantic retrieval returns relevant attendance chunks with provenance."""
    results = retrieval_service.search("What is the minimum attendance required for final examinations?", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "attendance" in top["text"].lower()
    assert top["document_name"] in ["academic_regulations.md", "attendance_circular.md"]
    assert top["page_number"] > 0
    assert "chunk_id" in top


def test_retrieval_merit_scholarship():
    """Verify semantic retrieval returns relevant scholarship chunks with provenance."""
    results = retrieval_service.search("What is the minimum GPA for the merit scholarship?", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert any(w in top["text"].lower() for w in ["scholarship", "gpa", "8.00", "8.50", "merit"])
    assert top["document_name"] in ["academic_regulations.md", "scholarship_notice.md"]
    assert top["page_number"] > 0


def test_retrieval_tuition_deadline():
    """Verify semantic retrieval returns relevant tuition deadline chunks with provenance."""
    results = retrieval_service.search("What is the deadline for paying semester tuition?", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert any(w in top["text"].lower() for w in ["tuition", "fee", "deadline", "august"])
    assert top["document_name"] in ["academic_regulations.md", "fee_deadlines.md"]


def test_retrieval_irrelevant_query():
    """Verify semantic retrieval filters low-similarity irrelevant queries."""
    results = retrieval_service.search("How to bake chocolate chip cookies in Mars atmosphere?", top_k=5, min_similarity=0.60)
    assert len(results) == 0
