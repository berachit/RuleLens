import logging
from sqlalchemy import text
from app.db.session import engine
from app.db.base import Base
from app.db.models import Document, Page, Chunk, Conversation, Message, RetrievalRecord  # noqa: F401

logger = logging.getLogger(__name__)


def init_db():
    """Initializes pgvector extension and creates all application tables."""
    if engine is None:
        logger.error("Cannot initialize DB: engine is None")
        return False

    try:
        with engine.begin() as conn:
            # Enable pgvector extension if available
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector extension verified or created.")
            except Exception as ext_err:
                logger.warning(f"Could not create vector extension (may not be supported or permissions missing): {ext_err}")

            # Create tables
            Base.metadata.create_all(bind=conn)
            logger.info("Application tables verified/created successfully.")

        # Seed initial regulations corpus if database has 0 documents
        _seed_corpus_if_empty()
        return True
    except Exception as e:
        logger.error(f"Error during init_db: {e}")
        return False


def _seed_corpus_if_empty():
    """Seeds the database with pre-indexed regulation documents if currently empty."""
    import json
    from pathlib import Path
    from app.db.session import SessionLocal

    corpus_path = Path(__file__).resolve().parent / "initial_corpus.json"
    if not corpus_path.exists():
        return

    try:
        with SessionLocal() as db:
            doc_count = db.query(Document).count()
            if doc_count > 0:
                logger.info(f"Database already populated ({doc_count} documents). Skipping auto-seed.")
                return

            logger.info("Database empty. Auto-seeding pre-indexed regulations corpus...")
            with open(corpus_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for d in data.get("documents", []):
                db.add(Document(**d))
            db.flush()

            for p in data.get("pages", []):
                db.add(Page(**p))
            db.flush()

            for c in data.get("chunks", []):
                db.add(Chunk(**c))

            db.commit()
            logger.info(
                f"Auto-seeded {len(data.get('documents', []))} documents and "
                f"{len(data.get('chunks', []))} chunks into PostgreSQL successfully."
            )
    except Exception as e:
        logger.warning(f"Auto-seeding initial corpus skipped or failed: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
