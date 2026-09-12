import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from app.ingest.parser import parse_markdown, parse_pdf
from app.ingest.chunker import chunk_document, ChunkData
from app.services.embedding_service import embedding_service
from app.db.session import SessionLocal, engine
from app.db.models import Document, Page, Chunk
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rulelens.ingest")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def run_ingestion() -> List[Dict[str, Any]]:
    """Runs end-to-end ingestion pipeline: dynamically discovers all files in data/raw, chunks, and indexes."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Dynamically scan data/raw
    raw_files = list(RAW_DIR.glob("*.*"))
    supported_files = [f for f in raw_files if f.suffix.lower() in [".md", ".pdf", ".txt"]]

    if not supported_files:
        logger.warning(f"No documents found in {RAW_DIR}. Nothing to ingest.")
        # Save empty index
        with open(PROCESSED_DIR / "corpus_index.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    all_chunks: List[ChunkData] = []
    parsed_docs = []

    for doc_path in supported_files:
        file_ext = doc_path.suffix.lower()
        file_type = "pdf" if file_ext == ".pdf" else "markdown"
        doc_id = f"doc-{doc_path.stem.lower()}"
        doc_title = doc_path.stem.replace("_", " ").replace("-", " ").title()

        logger.info(f"Parsing: {doc_path.name} ({file_type})...")
        if file_type == "pdf":
            parsed_doc = parse_pdf(doc_path, doc_id, doc_title, f"Uploaded document: {doc_path.name}")
        else:
            parsed_doc = parse_markdown(doc_path, doc_id, doc_title, f"Uploaded document: {doc_path.name}")

        parsed_docs.append(parsed_doc)
        chunks = chunk_document(parsed_doc)
        logger.info(f"  -> Generated {len(chunks)} chunks across {len(parsed_doc.pages)} pages")
        all_chunks.extend(chunks)

    logger.info(f"Total chunks extracted: {len(all_chunks)}. Computing embeddings via BAAI/bge-small-en-v1.5...")
    texts = [c.text for c in all_chunks]
    embeddings = embedding_service.embed_texts(texts)

    # Prepare export dataset with full provenance
    export_records = []
    for chunk, emb in zip(all_chunks, embeddings):
        record = {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_name": chunk.document_name,
            "document_title": chunk.document_title,
            "page_number": chunk.page_number,
            "section": chunk.section,
            "text": chunk.text,
            "chunk_index": chunk.chunk_index,
            "metadata": chunk.metadata,
            "embedding": emb,
        }
        export_records.append(record)

    # Save to local processed index
    index_file = PROCESSED_DIR / "corpus_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(export_records, f, indent=2)
    logger.info(f"Corpus index saved with embeddings at: {index_file}")

    # Attempt to persist in PostgreSQL if available
    try:
        if engine is not None:
            init_db()
            with SessionLocal() as db:
                for p_doc in parsed_docs:
                    existing_doc = db.query(Document).filter(Document.id == p_doc.id).first()
                    if not existing_doc:
                        db_doc = Document(
                            id=p_doc.id,
                            name=p_doc.name,
                            file_type=p_doc.file_type,
                            title=p_doc.title,
                            description=p_doc.description,
                        )
                        db.add(db_doc)
                        db.flush()

                        for p_page in p_doc.pages:
                            db_page = Page(
                                id=f"page-{p_doc.id}-{p_page.page_number}",
                                document_id=p_doc.id,
                                page_number=p_page.page_number,
                                raw_text=p_page.raw_text,
                            )
                            db.add(db_page)
                            db.flush()

                for record in export_records:
                    existing_chunk = db.query(Chunk).filter(Chunk.id == record["chunk_id"]).first()
                    if not existing_chunk:
                        page_id = f"page-{record['document_id']}-{record['page_number']}"
                        db_chunk = Chunk(
                            id=record["chunk_id"],
                            page_id=page_id,
                            section=record["section"],
                            text=record["text"],
                            embedding=record["embedding"],
                            chunk_index=record["chunk_index"],
                            metadata_json=record["metadata"],
                        )
                        db.add(db_chunk)
                db.commit()
                logger.info("Successfully populated PostgreSQL database with corpus records.")
    except Exception as db_err:
        logger.warning(f"Could not persist to PostgreSQL (fallback to corpus_index.json): {db_err}")

    return export_records


if __name__ == "__main__":
    run_ingestion()
