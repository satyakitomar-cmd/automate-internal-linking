"""Sentence-transformers embedding wrapper with caching."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    """Lazy-load the sentence-transformer model (singleton)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", model_name)
        _model = SentenceTransformer(model_name)
    return _model


def embed_texts(
    texts: Sequence[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
) -> np.ndarray:
    """Embed a batch of texts. Returns (N, dim) array."""
    model = _get_model(model_name)
    if not texts:
        return np.empty((0, model.get_sentence_embedding_dimension()))
    embeddings = model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,  # for cosine = dot product
    )
    return np.array(embeddings)


def embed_single(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Embed a single text string."""
    result = embed_texts([text], model_name)
    return result[0]


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between all pairs. a: (M, dim), b: (N, dim) -> (M, N)."""
    # Since embeddings are L2-normalized, cosine = dot product
    return a @ b.T


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two single vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
