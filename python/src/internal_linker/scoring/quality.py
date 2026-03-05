"""Anchor text quality scoring."""

from __future__ import annotations

import re

# Known generic/bad anchors
_GENERIC_ANCHORS = {
    "here", "this", "click", "link", "page", "article", "post", "blog",
    "read", "more", "see", "view", "check", "guide", "resource",
}

# Known acceptable single-word anchors (acronyms/brands)
_ALLOWED_SINGLE_WORDS = {
    "seo", "crm", "saas", "api", "sdk", "html", "css", "sql", "aws",
    "gdpr", "hipaa", "oauth", "devops", "kubernetes", "docker", "react",
    "python", "javascript", "typescript", "golang", "rust",
}


def anchor_quality_score(anchor_text: str) -> float:
    """Score the quality of an anchor text (0-1).

    Rewards: 2-6 words, descriptive, specific.
    Penalizes: too short/long, generic, punctuation-heavy, numbers-only.
    """
    text = anchor_text.strip()
    if not text:
        return 0.0

    score = 0.7  # base
    words = text.split()
    word_count = len(words)

    # ── Length checks ─────────────────────────────────────────────────
    if word_count == 1:
        lower = text.lower()
        if lower in _ALLOWED_SINGLE_WORDS:
            score += 0.05  # acceptable acronym/brand
        elif lower in _GENERIC_ANCHORS:
            return 0.05  # terrible anchor
        else:
            score -= 0.20  # single word, not ideal
    elif 2 <= word_count <= 4:
        score += 0.15  # sweet spot
    elif word_count == 5 or word_count == 6:
        score += 0.05  # acceptable
    elif word_count > 6:
        score -= 0.10 * (word_count - 6)  # penalty grows with excess

    # ── Generic check ─────────────────────────────────────────────────
    lower_words = {w.lower() for w in words}
    generic_overlap = lower_words & _GENERIC_ANCHORS
    if len(generic_overlap) / max(word_count, 1) > 0.5:
        score -= 0.25

    # ── Punctuation heavy ─────────────────────────────────────────────
    alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / max(len(text), 1)
    if alpha_ratio < 0.7:
        score -= 0.20

    # ── Numbers only ──────────────────────────────────────────────────
    if re.match(r'^[\d\s\.\,\-]+$', text):
        return 0.05

    # ── All caps (spammy) ─────────────────────────────────────────────
    if text.isupper() and word_count > 1:
        score -= 0.10

    # ── Contains "click here" type patterns ───────────────────────────
    text_lower = text.lower()
    if any(p in text_lower for p in ["click here", "read more", "learn more", "find out"]):
        return 0.05

    return max(0.0, min(score, 1.0))
