import pytest
from app.services.rag.engine import rag_engine


@pytest.mark.asyncio
async def test_rag_answered_hostel_fee():
    """Verify answerable question achieves ANSWERED state with real citations."""
    query = "What is the standard deadline for hostel fee payment?"
    result = await rag_engine.process_query(query)

    assert result["status"] == "ANSWERED"
    assert "10 August" in result["answer"] or "10" in result["answer"]
    assert len(result["sources"]) > 0
    top_src = result["sources"][0]
    assert top_src["page"] > 0
    assert any(doc in top_src["document"] for doc in ["fee_deadlines.md", "academic_regulations.md"])


@pytest.mark.asyncio
async def test_rag_not_covered_unsupported():
    """Verify unsupported query is refused as NOT_COVERED rather than hallucinating."""
    query = "Can a student miss an examination to attend a family wedding?"
    result = await rag_engine.process_query(query)

    assert result["status"] == "NOT_COVERED"
    assert any(term in result["answer"].lower() for term in ["not mention", "not contain", "refuses", "does not"])


@pytest.mark.asyncio
async def test_rag_conflict_attendance():
    """Verify attendance contradiction surfaces CONFLICT with both provisions."""
    query = "What is the minimum attendance required to appear for final examinations?"
    result = await rag_engine.process_query(query)

    assert result["status"] == "CONFLICT"
    assert result["conflict_details"] is not None
    assert "75%" in result["conflict_details"]["provision_a"] or "75%" in result["conflict_details"]["provision_b"]
    assert "80%" in result["conflict_details"]["provision_a"] or "80%" in result["conflict_details"]["provision_b"]
    assert len(result["sources"]) >= 2


@pytest.mark.asyncio
async def test_rag_conflict_merit_scholarship():
    """Verify merit scholarship GPA contradiction surfaces CONFLICT with both provisions."""
    query = "What is the minimum cumulative GPA required for the Merit Scholarship?"
    result = await rag_engine.process_query(query)

    assert result["status"] == "CONFLICT"
    assert result["conflict_details"] is not None
    assert "8.00" in result["conflict_details"]["provision_a"] or "8.00" in result["conflict_details"]["provision_b"]
    assert "8.50" in result["conflict_details"]["provision_a"] or "8.50" in result["conflict_details"]["provision_b"]


@pytest.mark.asyncio
async def test_rag_conflict_tuition_deadline():
    """Verify semester tuition deadline surfaces CONFLICT with both provisions."""
    query = "What is the deadline for paying semester tuition?"
    result = await rag_engine.process_query(query)

    assert result["status"] == "CONFLICT"
    assert result["conflict_details"] is not None
    assert "15 August" in result["conflict_details"]["provision_a"] or "15 August" in result["conflict_details"]["provision_b"]
    assert "20 August" in result["conflict_details"]["provision_a"] or "20 August" in result["conflict_details"]["provision_b"]


@pytest.mark.asyncio
async def test_citation_provenance_invariant():
    """Verify every emitted citation contains full, resolvable provenance."""
    query = "What is the deadline to submit a written fee dispute?"
    result = await rag_engine.process_query(query)

    assert result["status"] == "ANSWERED"
    for src in result["sources"]:
        assert src["document"]
        assert src["page"] > 0
        assert src["chunk_id"].startswith("chk-")
        assert len(src["text_snippet"]) > 10

