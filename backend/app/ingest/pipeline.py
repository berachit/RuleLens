import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.ingest.parser import parse_markdown, parse_pdf
from app.ingest.chunker import chunk_document, ChunkData
from app.services.embedding_service import embedding_service
from app.db.session import SessionLocal, engine
from app.db.models import Document, Page, Chunk
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rulelens.ingest")


from app.ingest.parser import parse_pdf_bytes, parse_markdown_text, parse_pdf, parse_markdown


def ingest_file(
    doc_id: str,
    doc_name: str,
    doc_title: str,
    file_bytes: Optional[bytes] = None,
    file_path: Optional[Path] = None,
    file_size_bytes: Optional[int] = None,
) -> Dict[str, Any]:
    """Parses, chunks and embeds a document directly into PostgreSQL without disk persistence.

    Args:
        doc_id: Stable document ID (e.g. 'doc-academic-regulations').
        doc_name: Original filename (e.g. 'academic_regulations.md').
        doc_title: Human-readable title.
        file_bytes: File contents in memory.
        file_path: Optional path for backward compatibility.
        file_size_bytes: File size for metadata.

    Returns:
        dict with chunk_count, page_count, and doc_id.
    """
    if engine is None:
        raise RuntimeError("Database engine is not available. Ensure PostgreSQL is running.")

    file_ext = Path(doc_name).suffix.lower()
    file_type = "pdf" if file_ext == ".pdf" else "markdown"

    logger.info(f"Parsing in-memory: {doc_name} ({file_type})...")
    if file_bytes is not None:
        size = len(file_bytes)
        if file_type == "pdf":
            parsed_doc = parse_pdf_bytes(file_bytes, doc_name, doc_id, doc_title, f"Uploaded document: {doc_name}")
        else:
            text_content = file_bytes.decode("utf-8", errors="replace")
            parsed_doc = parse_markdown_text(text_content, doc_name, doc_id, doc_title, f"Uploaded document: {doc_name}")
    elif file_path is not None:
        size = file_path.stat().st_size
        if file_type == "pdf":
            parsed_doc = parse_pdf(file_path, doc_id, doc_title, f"Uploaded document: {doc_name}")
        else:
            parsed_doc = parse_markdown(file_path, doc_id, doc_title, f"Uploaded document: {doc_name}")
    else:
        raise ValueError("Either file_bytes or file_path must be provided.")

    chunks: List[ChunkData] = chunk_document(parsed_doc)
    logger.info(f"  -> Generated {len(chunks)} chunks across {len(parsed_doc.pages)} pages")

    # Compute embeddings
    texts = [c.text for c in chunks]
    embeddings = embedding_service.embed_texts(texts)
    logger.info(f"  -> Computed {len(embeddings)} embeddings.")

    init_db()

    with SessionLocal() as db:
        # Upsert document row by id or name
        existing_doc = db.query(Document).filter(
            (Document.id == doc_id) | (Document.name == doc_name)
        ).first()
        if existing_doc:
            db.delete(existing_doc)
            db.flush()

        db_doc = Document(
            id=doc_id,
            name=doc_name,
            file_type=file_type,
            title=doc_title,
            description=f"Uploaded document: {doc_name}",
            file_path=None,
            file_size_bytes=file_size_bytes or size,
            upload_status="indexed",
        )
        db.add(db_doc)
        db.flush()

        for p_page in parsed_doc.pages:
            page_id = f"page-{doc_id}-{p_page.page_number}"
            db_page = Page(
                id=page_id,
                document_id=doc_id,
                page_number=p_page.page_number,
                raw_text=p_page.raw_text,
            )
            db.add(db_page)
            db.flush()

        for chunk, emb in zip(chunks, embeddings):
            page_id = f"page-{doc_id}-{chunk.page_number}"
            db_chunk = Chunk(
                id=chunk.id,
                page_id=page_id,
                section=chunk.section,
                text=chunk.text,
                embedding=emb,
                chunk_index=chunk.chunk_index,
                metadata_json=chunk.metadata,
            )
            db.add(db_chunk)

        db.commit()
        logger.info(f"Committed {len(chunks)} chunks for '{doc_name}' to PostgreSQL.")

    return {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "chunk_count": len(chunks),
        "page_count": len(parsed_doc.pages),
    }


def delete_document_from_db(doc_id: str) -> bool:
    """Deletes a document and all its pages and chunks from the database."""
    if engine is None:
        raise RuntimeError("Database engine is not available.")
    with SessionLocal() as db:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        logger.info(f"Deleted document '{doc_id}' and all associated chunks from PostgreSQL.")
    return True
