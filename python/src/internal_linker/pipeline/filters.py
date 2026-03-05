"""Steps F & G — Hard filters and soft penalties."""

from __future__ import annotations

import logging
import re
from collections import Counter

from ..config import PipelineConfig
from ..nlp.embeddings import cosine_similarity
from ..types import Doc, ExistingLinkPolicy, PageIntent, ScoredAnchor

logger = logging.getLogger(__name__)

# ── Intent compatibility matrix ───────────────────────────────────────
# (anchor_implies, target_intent) -> allowed?
_INTENT_MISMATCHES = {
    # Don't link "what is X" to a pricing page
    (PageIntent.GLOSSARY, PageIntent.PRODUCT): False,
    # Don't link definitional anchors to category pages
    (PageIntent.GLOSSARY, PageIntent.CATEGORY): False,
}


def _is_intent_mismatch(anchor_text: str, target_intent: PageIntent) -> bool:
    """Check if anchor implies a different intent than target delivers."""
    lower = anchor_text.lower()

    # Detect if anchor implies definitional content
    is_definitional = any(p in lower for p in [
        "what is", "what are", "definition of", "meaning of",
    ])
    if is_definitional and target_intent in {PageIntent.PRODUCT, PageIntent.CATEGORY}:
        return True

    return False


def hard_filter(
    scored_anchors: list[ScoredAnchor],
    source: Doc,
    docs_by_id: dict[str, Doc],
    config: PipelineConfig,
) -> list[ScoredAnchor]:
    """Apply hard rejection rules (Step F).

    Removes suggestions that violate constraints.
    """
    results: list[ScoredAnchor] = []
    anchor_freq = Counter(a.anchor.text.lower() for a in scored_anchors)

    for sa in scored_anchors:
        target = docs_by_id.get(sa.target_doc_id)
        if target is None:
            continue

        # F1: Anchor text is already inside an existing link
        anchor_lower = sa.anchor.text.lower()
        in_existing = any(
            anchor_lower in link.anchor_text.lower()
            for link in source.outbound_links
        )
        if in_existing:
            continue

        # F2: Source already links to target (if skip policy)
        if config.site_rules.existing_link_policy == ExistingLinkPolicy.SKIP:
            if target.url in source.linked_urls:
                continue

        # F3: Target is a tag/category page
        if target.intent == PageIntent.CATEGORY:
            continue

        # F4: Anchor is in avoided section (checked at extraction time, but double-check)
        avoid_lower = [s.lower() for s in config.site_rules.avoid_sections]
        if any(s in sa.anchor.context_sentence.lower() for s in avoid_lower):
            continue

        # F5: Anchor phrase appears too many times in source
        if anchor_freq.get(anchor_lower, 0) > config.max_anchor_frequency_in_source:
            continue

        # F6: Near-duplicate source <-> target (already handled in candidate_graph, but safety)
        if source.embedding is not None and target.embedding is not None:
            sim = cosine_similarity(source.embedding, target.embedding)
            if sim > config.near_duplicate_threshold:
                continue

        # F7: Intent mismatch
        if _is_intent_mismatch(sa.anchor.text, target.intent):
            continue

        results.append(sa)

    removed = len(scored_anchors) - len(results)
    if removed:
        logger.debug("Hard filter removed %d / %d suggestions for %s",
                     removed, len(scored_anchors), source.url)
    return results


def apply_soft_penalties(
    scored_anchors: list[ScoredAnchor],
    docs_by_id: dict[str, Doc],
    global_target_counts: Counter,
    config: PipelineConfig,
) -> list[ScoredAnchor]:
    """Apply soft penalty adjustments (Step G).

    Modifies combined scores in-place and returns the list.
    """
    for sa in scored_anchors:
        target = docs_by_id.get(sa.target_doc_id)
        if target is None:
            continue

        # G1: Penalize targets that already have too many suggestions
        target_count = global_target_counts.get(sa.target_url, 0)
        if target_count > 5:
            excess = target_count - 5
            penalty = excess * config.target_saturation_penalty
            sa.combined -= penalty

        # G2: Commercial penalty (if target is product page and source is informational)
        if target.intent == PageIntent.PRODUCT:
            sa.combined -= config.commercial_penalty

        # G3: Clamp score
        sa.combined = max(0.0, sa.combined)

    return scored_anchors
