"""Admin API routes for document management.

All endpoints require the X-Admin-Key header matching settings.ADMIN_API_KEY.
"""

import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db, engine
from app.db.models import Document, Chunk, Page

logger = logging.getLogger("rulelens.admin")

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Auth dependency ─────────────────────────────────────────────────────────

def require_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key.")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/documents", dependencies=[Depends(require_admin_key)])
def list_admin_documents(db: Session = Depends(get_db)):
    """Returns all documents with chunk counts and metadata."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    results = []
    for doc in docs:
        chunk_count = (
            db.query(Chunk)
            .join(Page, Chunk.page_id == Page.id)
            .filter(Page.document_id == doc.id)
            .count()
        )
        page_count = db.query(Page).filter(Page.document_id == doc.id).count()
        results.append({
            "id": doc.id,
            "name": doc.name,
            "title": doc.title,
            "file_type": doc.file_type,
            "file_size_bytes": doc.file_size_bytes,
            "upload_status": doc.upload_status,
            "chunk_count": chunk_count,
            "page_count": page_count,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })
    return {"documents": results, "total": len(results)}


@router.post("/documents", dependencies=[Depends(require_admin_key)])
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Uploads a regulation file, parses in memory and stores chunks + embeddings directly in PostgreSQL."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable. Cannot ingest files without PostgreSQL.")

    allowed_suffixes = {".md", ".pdf", ".txt"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(allowed_suffixes)}",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    doc_id = f"doc-{Path(file.filename).stem.lower().replace(' ', '-')}"
    doc_title = Path(file.filename).stem.replace("_", " ").replace("-", " ").title()

    # Ingest directly into PostgreSQL
    try:
        from app.ingest.pipeline import ingest_file
        result = ingest_file(
            doc_id=doc_id,
            doc_name=file.filename,
            doc_title=doc_title,
            file_bytes=content,
            file_size_bytes=len(content),
        )
        from app.services.retrieval import retrieval_service
        retrieval_service.reload()

        return {
            "message": f"'{file.filename}' uploaded and indexed into database successfully.",
            "doc_id": doc_id,
            "doc_name": file.filename,
            "chunk_count": result["chunk_count"],
            "page_count": result["page_count"],
            "upload_status": "indexed",
        }
    except Exception as e:
        logger.error(f"Ingestion failed for '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.delete("/documents/{doc_id}", dependencies=[Depends(require_admin_key)])
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """Deletes a document and all its pages and chunks from PostgreSQL."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    doc_name = doc.name
    db.delete(doc)
    db.commit()
    logger.info(f"Deleted document '{doc_id}' and all chunks from database.")

    from app.services.retrieval import retrieval_service
    retrieval_service.reload()

    return {"message": f"'{doc_name}' deleted successfully.", "doc_id": doc_id}


@router.get("/stats", dependencies=[Depends(require_admin_key)])
def admin_stats(db: Session = Depends(get_db)):
    """Returns overall corpus stats for the admin dashboard."""
    from app.services.retrieval import retrieval_service

    doc_count = db.query(Document).count()
    page_count = db.query(Page).count()
    chunk_count = db.query(Chunk).count()
    indexed_count = db.query(Document).filter(Document.upload_status == "indexed").count()
    failed_count = db.query(Document).filter(Document.upload_status == "failed").count()

    return {
        "total_documents": doc_count,
        "indexed_documents": indexed_count,
        "failed_documents": failed_count,
        "total_pages": page_count,
        "total_chunks_in_db": chunk_count,
        "in_memory_chunks": len(retrieval_service._corpus),
        "vector_dimension": 384,
        "storage": "PostgreSQL Vector Database",
    }
