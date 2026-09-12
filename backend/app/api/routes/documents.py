from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from app.services.retrieval import retrieval_service
from app.db.session import get_db, engine

router = APIRouter(tags=["Documents & Search"])


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    """Lists all verified academic regulation documents currently active in the corpus."""
    # 1. Query from PostgreSQL if available
    if engine is not None:
        try:
            from app.db.models import Document
            docs = db.query(Document).order_by(Document.name).all()
            if docs:
                doc_list = [
                    {
                        "id": doc.id,
                        "name": doc.name,
                        "title": doc.title,
                        "file_type": doc.file_type,
                        "version": doc.version,
                        "description": doc.description or "",
                        "upload_status": doc.upload_status,
                    }
                    for doc in docs
                ]
                return {
                    "corpus": "Academic & Student Regulations",
                    "authority": "Academic Senate & Office of the Registrar",
                    "documents": doc_list,
                }
        except Exception:
            pass

    # 2. Derive active documents from loaded retrieval corpus
    seen = {}
    for chunk in retrieval_service._corpus:
        name = chunk.get("document_name")
        if name and name not in seen:
            seen[name] = {
                "id": chunk.get("document_id", f"doc-{name.lower()}"),
                "name": name,
                "title": chunk.get("document_title", name.replace("_", " ").title()),
                "file_type": "pdf" if name.endswith(".pdf") else "markdown",
                "version": "2026",
                "description": f"Regulation document: {name}",
                "upload_status": "indexed",
            }

    return {
        "corpus": "Academic & Student Regulations",
        "authority": "Academic Senate & Office of the Registrar",
        "documents": list(seen.values()),
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
def get_document_content(doc_name: str, db: Session = Depends(get_db)):
    """Retrieves the full raw content of a document, served directly from the database."""
    # 1. Primary: Retrieve pages directly from the database
    if engine is not None:
        try:
            from app.db.models import Document, Page
            doc = db.query(Document).filter((Document.name == doc_name) | (Document.id == doc_name)).first()
            if doc:
                pages = db.query(Page).filter(Page.document_id == doc.id).order_by(Page.page_number).all()
                if pages:
                    pages_data = [{"page": p.page_number, "text": p.raw_text} for p in pages]
                    if doc.file_type == "pdf":
                        full_text = "\n\n--- Page Break ---\n\n".join(p.raw_text for p in pages)
                    else:
                        full_text = "\n\n".join(p.raw_text for p in pages)
                    return {
                        "document_name": doc.name,
                        "file_type": doc.file_type,
                        "content": full_text,
                        "pages": pages_data,
                    }
        except Exception:
            pass

    # 2. Fallback: Reconstruct content from loaded in-memory corpus chunks
    doc_chunks = [c for c in retrieval_service._corpus if c.get("document_name") == doc_name or c.get("document_id") == doc_name]
    if doc_chunks:
        doc_chunks_sorted = sorted(doc_chunks, key=lambda c: (c.get("page_number", 1), c.get("chunk_index", 0)))
        pages_dict = {}
        for c in doc_chunks_sorted:
            p_num = c.get("page_number", 1)
            pages_dict.setdefault(p_num, []).append(c["text"])
        pages_data = [{"page": p, "text": "\n\n".join(texts)} for p, texts in sorted(pages_dict.items())]
        file_type = "pdf" if doc_name.lower().endswith(".pdf") else "markdown"
        separator = "\n\n--- Page Break ---\n\n" if file_type == "pdf" else "\n\n"
        full_text = separator.join(p["text"] for p in pages_data)
        return {
            "document_name": doc_name,
            "file_type": file_type,
            "content": full_text,
            "pages": pages_data,
        }

    raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found.")


@router.get("/sources/{source_id}")
def get_source(source_id: str):
    """Retrieves document, section and page provenance for a given chunk ID."""
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
