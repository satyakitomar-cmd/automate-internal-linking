"""Lexical scoring: BM25 + Jaccard token overlap."""

from __future__ import annotations

import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer."""
    return re.findall(r'\b[a-z]{2,}\b', text.lower())


def jaccard_similarity(a: str, b: str) -> float:
    """Token-level Jaccard similarity between two strings."""
    tokens_a = set(_tokenize(a))
    tokens_b = set(_tokenize(b))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def token_overlap_score(anchor: str, target_terms: list[str]) -> float:
    """Fraction of anchor tokens that appear in target terms."""
    anchor_tokens = set(_tokenize(anchor))
    if not anchor_tokens:
        return 0.0
    target_tokens = set()
    for term in target_terms:
        target_tokens.update(_tokenize(term))
    if not target_tokens:
        return 0.0
    overlap = anchor_tokens & target_tokens
    return len(overlap) / len(anchor_tokens)


def bm25_score(
    anchor: str,
    target_texts: list[str],
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Simplified BM25 score of anchor against target document fields.

    target_texts: list of strings (title, headings, terms) treated as a single doc.
    """
    query_tokens = _tokenize(anchor)
    if not query_tokens:
        return 0.0

    # Combine all target texts into a single document
    doc_text = " ".join(target_texts)
    doc_tokens = _tokenize(doc_text)
    if not doc_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    avg_dl = doc_len  # single doc, so avgdl = dl
    tf_map = Counter(doc_tokens)

    score = 0.0
    for token in query_tokens:
        tf = tf_map.get(token, 0)
        if tf == 0:
            continue
        # IDF approximation: since we have one doc, use a simple log scale
        idf = math.log(2.0)  # constant since single doc
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / max(avg_dl, 1))
        score += idf * numerator / denominator

    # Normalize by query length
    return score / len(query_tokens)


def lexical_score(
    anchor_text: str,
    target_terms: list[str],
    target_title: str,
    target_headings: list[str],
) -> float:
    """Combined lexical relevance score (0-1).

    Blends: BM25 (0.5) + Jaccard with title (0.3) + token overlap with terms (0.2)
    """
    target_texts = [target_title] + target_headings + target_terms

    bm25 = bm25_score(anchor_text, target_texts)
    # Normalize BM25 to roughly 0-1 range
    bm25_norm = min(bm25 / 3.0, 1.0)

    jaccard_title = jaccard_similarity(anchor_text, target_title)

    # Also check against headings
    jaccard_headings = 0.0
    if target_headings:
        jaccard_headings = max(jaccard_similarity(anchor_text, h) for h in target_headings)

    overlap = token_overlap_score(anchor_text, target_terms)

    score = (
        0.40 * bm25_norm
        + 0.25 * jaccard_title
        + 0.15 * jaccard_headings
        + 0.20 * overlap
    )
    return min(max(score, 0.0), 1.0)
