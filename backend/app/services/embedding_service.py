import logging
from typing import List, Union
import numpy as np
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
DEFAULT_DIMENSION = 384


class EmbeddingService:
    """Generates dense vector embeddings using fastembed and BAAI/bge-small-en-v1.5."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> TextEmbedding:
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name} with threads=1...")
            self._model = TextEmbedding(model_name=self.model_name, threads=1)
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates normalized vector embeddings for a list of text strings."""
        if not texts:
            return []
        embeddings = list(self.model.embed(texts, batch_size=16, parallel=1))
        # Convert numpy arrays to standard python floats list
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Embeds a single query string."""
        return self.embed_texts([query])[0]


# Global singleton instance
embedding_service = EmbeddingService()
