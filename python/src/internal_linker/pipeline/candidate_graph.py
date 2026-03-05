"""Step C — Build candidate graph of potential links via embedding similarity."""

from __future__ import annotations

import logging

import numpy as np

from ..config import PipelineConfig
from ..nlp.embeddings import cosine_similarity_matrix
from ..types import Doc, ExistingLinkPolicy

logger = logging.getLogger(__name__)


def build_candidate_graph(
    docs: list[Doc],
    config: PipelineConfig,
) -> dict[str, list[Doc]]:
    """For each source doc, find the top-K most similar target docs.

    Returns dict mapping source doc_id -> list of candidate target Docs.
    """
    n = len(docs)
    if n < 2:
        return {}

    # Build embedding matrix
    embeddings = np.array([doc.embedding for doc in docs if doc.embedding is not None])
    doc_map = {doc.doc_id: doc for doc in docs}

    # Compute full similarity matrix (N x N)
    sim_matrix = cosine_similarity_matrix(embeddings, embeddings)

    candidates: dict[str, list[Doc]] = {}
    k = config.top_k_targets_per_source

    for i, source in enumerate(docs):
        if source.embedding is None:
            continue

        similarities = sim_matrix[i]
        scored_targets: list[tuple[float, int]] = []

        for j in range(n):
            if i == j:
                continue  # exclude self

            target = docs[j]
            sim = float(similarities[j])

            # ── Pre-filters ───────────────────────────────────────────
            # Near-duplicate check
            if sim > config.near_duplicate_threshold:
                logger.debug(
                    "Near-duplicate: %s <-> %s (cosine=%.3f)",
                    source.url, target.url, sim,
                )
                continue

            # Already linked check (per policy)
            if config.site_rules.existing_link_policy == ExistingLinkPolicy.SKIP:
                if target.url in source.linked_urls:
                    continue

            scored_targets.append((sim, j))

        # Sort by similarity descending, take top K
        scored_targets.sort(key=lambda x: x[0], reverse=True)
        top_targets = [docs[j] for _, j in scored_targets[:k]]
        candidates[source.doc_id] = top_targets

    logger.info(
        "Built candidate graph: %d sources, avg %.1f targets each",
        len(candidates),
        sum(len(v) for v in candidates.values()) / max(len(candidates), 1),
    )
    return candidates
