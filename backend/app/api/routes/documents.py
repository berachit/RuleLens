from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.retrieval import retrieval_service

router = APIRouter(tags=["Documents & Search"])


@router.get("/documents")
def list_documents():
    """Lists all verified academic regulation documents currently active in the corpus."""
    from pathlib import Path
    from app.config import BACKEND_DIR

    raw_dir = BACKEND_DIR.parent / "data" / "raw"
    files = sorted(list(raw_dir.glob("*.*"))) if raw_dir.exists() else []

    doc_list = []
    for f in files:
        if f.suffix.lower() in [".md", ".pdf", ".txt"]:
            title = f.stem.replace("_", " ").replace("-", " ").title()
            doc_type = "pdf" if f.suffix.lower() == ".pdf" else "markdown"
            doc_list.append({
                "id": f"doc-{f.stem.lower()}",
                "name": f.name,
                "title": f"Demo University {title} 2026",
                "file_type": doc_type,
                "version": "2026",
                "description": f"Authoritative institutional document: {f.name}",
            })

    return {
        "corpus": "Demo University — Academic & Student Regulations 2026",
        "authority": "Academic Senate & Office of the Registrar",
        "effective_period": "2026 - 2027",
        "documents": doc_list,
    }


@router.get("/search")
def search_regulations(
    q: str = Query(..., description="Natural language search query"),
    top_k: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.35, ge=0.0, le=1.0),
):
    """Executes semantic vector search over the verified regulation corpus."""
    results = retrieval_service.search(q, top_k=top_k, min_similarity=min_similarity)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/documents/{doc_name}/content")
def get_document_content(doc_name: str):
    """Retrieves the full raw content of a document in the corpus."""
    from pathlib import Path
    from app.config import BACKEND_DIR

    raw_dir = BACKEND_DIR.parent / "data" / "raw"
    target_file = raw_dir / doc_name

    if not target_file.exists():
        raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found.")

    if doc_name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(str(target_file))
        pages = []
        for idx, page in enumerate(reader.pages):
            pages.append({
                "page": idx + 1,
                "text": page.extract_text() or "",
            })
        full_text = "\n\n--- Page Break ---\n\n".join(p["text"] for p in pages)
        return {
            "document_name": doc_name,
            "file_type": "pdf",
            "content": full_text,
            "pages": pages,
        }
    else:
        content = target_file.read_text(encoding="utf-8")
        return {
            "document_name": doc_name,
            "file_type": "markdown",
            "content": content,
        }


@router.get("/sources/{source_id}")
def get_source(source_id: str):
    """Retrieves document, section, and page provenance for a given chunk ID, reconstructs clean table/prose."""
    for chunk in retrieval_service._corpus:
        if chunk["chunk_id"] == source_id:
            return {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "document_title": chunk["document_title"],
                "page_number": chunk["page_number"],
                "section": chunk["section"],
                "text": chunk["text"],
            }
    raise HTTPException(status_code=404, detail="Source chunk not found in corpus.")
