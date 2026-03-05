"""Context suitability scoring: where in the document the anchor appears."""

from __future__ import annotations

import re

from ..types import AnchorCandidate, Doc


def context_score(doc: Doc, anchor: AnchorCandidate) -> float:
    """Score how suitable the anchor's position is for a link (0-1).

    Rewards: mid-body paragraphs, regular sentences, "learn more" patterns.
    Penalizes: headings, very short sentences, list items, captions, boilerplate.
    """
    score = 0.7  # base score

    # ── Paragraph position ────────────────────────────────────────────
    total_paras = len(doc.paragraphs)
    if total_paras > 0:
        rel_pos = anchor.paragraph_index / total_paras
        # Prefer middle paragraphs (not first or last)
        if 0.1 < rel_pos < 0.85:
            score += 0.1
        elif rel_pos <= 0.05 or rel_pos >= 0.95:
            score -= 0.1  # intro/conclusion slightly less ideal

    # ── Sentence length ───────────────────────────────────────────────
    sent_words = len(anchor.context_sentence.split())
    if sent_words < 5:
        score -= 0.25  # very short sentence, likely heading/caption
    elif sent_words < 10:
        score -= 0.05
    elif sent_words > 15:
        score += 0.05  # substantive sentence

    # ── List item detection ───────────────────────────────────────────
    if re.match(r'^[\-\*\d]+[\.\)]\s', anchor.context_sentence):
        score -= 0.10  # list item

    # ── "Learn more" patterns (positive) ──────────────────────────────
    learn_patterns = [
        r'\blearn\s+(?:more\s+)?about\b',
        r'\bfor\s+more\s+(?:information|details)\b',
        r'\brelated\s+to\b',
        r'\bsuch\s+as\b',
        r'\bincluding\b',
        r'\bexplained\s+in\b',
    ]
    sent_lower = anchor.context_sentence.lower()
    for pat in learn_patterns:
        if re.search(pat, sent_lower):
            score += 0.05
            break

    # ── Boilerplate patterns (negative) ───────────────────────────────
    boilerplate = [
        r'\b(?:copyright|all\s+rights\s+reserved)\b',
        r'\b(?:subscribe|newsletter|follow\s+us)\b',
        r'\b(?:share\s+this|tweet\s+this)\b',
        r'\b(?:filed\s+under|tagged|categories?)\b',
        r'\b(?:previous|next)\s+(?:post|article)\b',
    ]
    for pat in boilerplate:
        if re.search(pat, sent_lower):
            score -= 0.20
            break

    return max(0.0, min(score, 1.0))
