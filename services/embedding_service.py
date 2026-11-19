"""Embedding generation service using Sentence Transformers."""

import os
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.config import Config


class EmbeddingError(Exception):
    """Exception raised when embedding generation fails."""
    pass


class EmbeddingService:
    """Manages embedding generation with batching and local caching."""

    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    def __init__(self, model_name: str = Config.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        # Model is loaded lazily on first embedding call to enable instantaneous UI startup

    @classmethod
    def get_instance(cls, model_name: str = Config.EMBEDDING_MODEL_NAME) -> "EmbeddingService":
        """Get or create singleton instance of EmbeddingService."""
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    def _load_model(self) -> None:
        """Load SentenceTransformer model with fallback for offline execution."""
        if self._model is not None:
            return

        try:
            # First attempt: load instantly from local cache (avoids network timeout)
            self._model = SentenceTransformer(self.model_name, local_files_only=True)
        except Exception:
            try:
                # Second attempt: load normally with online download if not cached yet
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise EmbeddingError(
                    f"Failed to load embedding model '{self.model_name}': {str(e)}"
                ) from e

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate normalized vector embeddings for a list of texts in batches.

        Args:
            texts: List of strings to embed.
            batch_size: Number of texts per batch.

        Returns:
            List of 384-dimensional float lists.
        """
        if not texts:
            return []

        if self._model is None:
            self._load_model()

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,  # Normalized embeddings enable direct cosine similarity
            )
            # Ensure Python float list
            if isinstance(embeddings, np.ndarray):
                return embeddings.tolist()
            return [list(e) for e in embeddings]
        except Exception as e:
            raise EmbeddingError(f"Error computing text embeddings: {str(e)}") from e

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a search query string.

        Args:
            query: The question or query string.

        Returns:
            Single 384-dimensional float list.
        """
        if not query or not query.strip():
            raise EmbeddingError("Cannot embed an empty query.")

        results = self.embed_texts([query.strip()], batch_size=1)
        return results[0]

    @property
    def embedding_dimension(self) -> int:
        """Return the vector dimensionality of the model (384 for all-MiniLM-L6-v2)."""
        return 384
