"""Semantic scoring: cosine similarity between anchor context and target embedding."""

from __future__ import annotations

import numpy as np

from ..nlp.embeddings import cosine_similarity, embed_single


def semantic_score(
    anchor_context_sentence: str,
    target_embedding: np.ndarray,
    model_name: str = "all-MiniLM-L6-v2",
) -> float:
    """Compute semantic similarity between anchor's context sentence and target doc.

    Returns score in [0, 1].
    """
    if not anchor_context_sentence or target_embedding is None:
        return 0.0

    context_emb = embed_single(anchor_context_sentence, model_name)
    sim = cosine_similarity(context_emb, target_embedding)
    # Cosine with normalized vectors is in [-1, 1]; clamp to [0, 1]
    return max(0.0, min(float(sim), 1.0))
