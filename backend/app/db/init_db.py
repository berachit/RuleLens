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
        return True
    except Exception as e:
        logger.error(f"Error during init_db: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
