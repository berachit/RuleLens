import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.embedding_service import embedding_service

logger = logging.getLogger("rulelens.retrieval")

# Fallback JSON index path (used when DB is unavailable)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_FALLBACK_INDEX = REPO_ROOT / "data" / "processed" / "corpus_index.json"


class RetrievalService:
    """Performs semantic vector search over the verified regulation corpus.

    Primary source: PostgreSQL chunks table (via SQLAlchemy).
    Fallback: corpus_index.json (for offline / no-DB development).
    """

    def __init__(self):
        self._corpus: List[Dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None
        self._load_index()

    def clear(self):
        """Clears in-memory corpus index and vectors."""
        self._corpus = []
        self._embeddings = None

    def reload(self):
        """Reloads the in-memory index from the database. Call after every upload."""
        self._load_index()

    def _load_index(self):
        """Try PostgreSQL first, then fall back to JSON."""
        loaded = self._load_from_db()
        if not loaded:
            self._load_from_json()

    def _load_from_db(self) -> bool:
        """Load chunks + embeddings from PostgreSQL. Returns True on success."""
        try:
            from app.db.session import SessionLocal, engine
            from app.db.models import Chunk, Page, Document

            if engine is None:
                return False

            with SessionLocal() as db:
                rows = (
                    db.query(Chunk, Page, Document)
                    .join(Page, Chunk.page_id == Page.id)
                    .join(Document, Page.document_id == Document.id)
                    .all()
                )

            if not rows:
                logger.info("No chunks found in PostgreSQL yet.")
                return False

            corpus = []
            for chunk, page, doc in rows:
                if chunk.embedding is None:
                    continue
                corpus.append({
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "document_name": doc.name,
                    "document_title": doc.title,
                    "page_number": page.page_number,
                    "section": chunk.section,
                    "text": chunk.text,
                    "embedding": list(chunk.embedding),
                })

            if not corpus:
                return False

            self._corpus = corpus
            self._build_index()
            logger.info(f"Loaded {len(self._corpus)} corpus chunks from PostgreSQL.")
            return True

        except Exception as e:
            logger.warning(f"Could not load from PostgreSQL (will try JSON fallback): {e}")
            return False

    def _load_from_json(self):
        """Load from corpus_index.json fallback."""
        if not _FALLBACK_INDEX.exists():
            logger.warning(f"No fallback corpus_index.json at {_FALLBACK_INDEX}. Corpus empty.")
            self._corpus = []
            self._embeddings = None
            return

        try:
            with open(_FALLBACK_INDEX, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data:
                self._corpus = []
                self._embeddings = None
                return

            self._corpus = data
            self._build_index()
            logger.info(f"Loaded {len(self._corpus)} corpus chunks from JSON fallback.")
        except Exception as e:
            logger.error(f"Failed to load JSON fallback corpus: {e}")
            self._corpus = []
            self._embeddings = None

    def _build_index(self):
        """Builds the in-memory numpy similarity matrix."""
        key = "embedding" if "embedding" in self._corpus[0] else "embedding"
        vectors = [c[key] for c in self._corpus]
        self._embeddings = np.array(vectors, dtype=np.float32)
        # L2 normalise for cosine similarity via dot product
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._embeddings = self._embeddings / norms

    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.40) -> List[Dict[str, Any]]:
        """Retrieves candidate evidence chunks preserving complete provenance."""
        if self._embeddings is None or len(self._corpus) == 0:
            self._load_index()

        if self._embeddings is None or len(self._corpus) == 0:
            logger.warning("Corpus index is empty or uninitialized.")
            return []

        # Generate normalised query vector
        query_vec = np.array(embedding_service.embed_query(query), dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        similarities = np.dot(self._embeddings, query_vec)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < min_similarity:
                continue
            chunk = self._corpus[idx]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "document_title": chunk["document_title"],
                "page_number": chunk["page_number"],
                "section": chunk["section"],
                "text": chunk["text"],
                "similarity": round(score, 4),
            })

        return results


retrieval_service = RetrievalService()
