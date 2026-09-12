import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.embedding_service import embedding_service

logger = logging.getLogger("rulelens.retrieval")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_FILE = REPO_ROOT / "data" / "processed" / "corpus_index.json"


class RetrievalService:
    """Performs semantic vector search over the verified regulation corpus."""

    def __init__(self):
        self._corpus: List[Dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None
        self._load_index()

    def clear(self):
        """Clears in-memory corpus index and vectors."""
        self._corpus = []
        self._embeddings = None

    def _load_index(self):
        if not INDEX_FILE.exists():
            logger.warning(f"Corpus index not found at: {INDEX_FILE}. Ingestion required.")
            self._corpus = []
            self._embeddings = None
            return

        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                self._corpus = json.load(f)

            if self._corpus:
                vectors = [c["embedding"] for c in self._corpus]
                self._embeddings = np.array(vectors, dtype=np.float32)
                # Ensure L2 normalized
                norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self._embeddings = self._embeddings / norms
                logger.info(f"Loaded {len(self._corpus)} corpus chunks into vector index.")
            else:
                self._embeddings = None
        except Exception as e:
            logger.error(f"Failed to load corpus index: {e}")
            self._corpus = []
            self._embeddings = None

    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.40) -> List[Dict[str, Any]]:
        """Retrieves candidate evidence chunks preserving complete provenance."""
        if self._embeddings is None or len(self._corpus) == 0:
            self._load_index()

        if self._embeddings is None or len(self._corpus) == 0:
            logger.warning("Corpus index is empty or uninitialized.")
            return []

        # Generate normalized query vector
        query_vec = np.array(embedding_service.embed_query(query), dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        # Compute cosine similarity
        similarities = np.dot(self._embeddings, query_vec)

        # Rank indices descending
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
