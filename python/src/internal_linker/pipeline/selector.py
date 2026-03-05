"""Step E — Select the best 3-5 suggestions per source using MMR diversification."""

from __future__ import annotations

import logging
from collections import Counter

import numpy as np

from ..config import PipelineConfig
from ..nlp.embeddings import cosine_similarity
from ..types import Doc, ScoredAnchor

logger = logging.getLogger(__name__)


def mmr_diversify(
    candidates: list[ScoredAnchor],
    docs_by_id: dict[str, Doc],
    n: int = 5,
    lambd: float = 0.75,
) -> list[ScoredAnchor]:
    """Select top-N candidates using Maximal Marginal Relevance.

    Balances relevance (combined score) with diversity (dissimilarity
    to already-selected targets based on embeddings).
    """
    if len(candidates) <= n:
        return candidates

    selected: list[ScoredAnchor] = []
    remaining = list(candidates)

    # Pick the best-scoring one first
    remaining.sort(key=lambda s: s.combined, reverse=True)
    selected.append(remaining.pop(0))

    while len(selected) < n and remaining:
        best_mmr = -float("inf")
        best_idx = 0

        for i, cand in enumerate(remaining):
            relevance = cand.combined

            # Max similarity to any already-selected target
            max_sim = 0.0
            cand_target = docs_by_id.get(cand.target_doc_id)
            if cand_target and cand_target.embedding is not None:
                for sel in selected:
                    sel_target = docs_by_id.get(sel.target_doc_id)
                    if sel_target and sel_target.embedding is not None:
                        sim = cosine_similarity(cand_target.embedding, sel_target.embedding)
                        max_sim = max(max_sim, sim)

            mmr_score = lambd * relevance - (1 - lambd) * max_sim
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_idx = i

        selected.append(remaining.pop(best_idx))

    return selected


def select_suggestions(
    source: Doc,
    scored_anchors: list[ScoredAnchor],
    docs_by_id: dict[str, Doc],
    global_target_counts: Counter,
    config: PipelineConfig,
) -> list[ScoredAnchor]:
    """Select the best suggestions for a source, applying all constraints.

    Constraints:
    - max_suggestions_per_source (default 5)
    - max_same_target_per_source (default 1)
    - max_suggestions_to_same_target_global (default 20)
    - anchor uniqueness within source
    - orphan page boosting
    """
    if not scored_anchors:
        return []

    # Sort by combined score
    scored_anchors.sort(key=lambda s: s.combined, reverse=True)

    # ── Apply orphan boosting ─────────────────────────────────────────
    for sa in scored_anchors:
        target = docs_by_id.get(sa.target_doc_id)
        if target and target.incoming_suggestion_count < 2:
            sa.combined *= config.orphan_boost_factor

    # ── Constraint-aware pre-filter ───────────────────────────────────
    filtered: list[ScoredAnchor] = []
    target_count_local: Counter = Counter()
    used_anchors: set[str] = set()

    for sa in scored_anchors:
        # Max same target per source
        if target_count_local[sa.target_url] >= config.max_same_target_per_source:
            continue

        # Global target cap
        if global_target_counts.get(sa.target_url, 0) >= config.max_suggestions_to_same_target_global:
            continue

        # Anchor uniqueness
        anchor_key = sa.anchor.text.lower()
        if anchor_key in used_anchors:
            continue

        filtered.append(sa)
        target_count_local[sa.target_url] += 1
        used_anchors.add(anchor_key)

    # ── MMR diversification ───────────────────────────────────────────
    selected = mmr_diversify(
        filtered,
        docs_by_id,
        n=config.max_suggestions_per_source,
        lambd=config.mmr_lambda,
    )

    # Update global counters
    for sa in selected:
        global_target_counts[sa.target_url] += 1
        target = docs_by_id.get(sa.target_doc_id)
        if target:
            target.incoming_suggestion_count += 1

    return selected
