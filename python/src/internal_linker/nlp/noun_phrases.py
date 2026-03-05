"""Noun phrase (NP) chunking using spaCy."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_nlp = None


def _get_nlp():
    """Lazy-load spaCy model (singleton, shared with entities)."""
    global _nlp
    if _nlp is None:
        import spacy
        logger.info("Loading spaCy model for NP chunking: en_core_web_sm")
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_noun_phrases(
    text: str,
    min_words: int = 2,
    max_words: int = 6,
) -> list[tuple[str, int, int]]:
    """Extract noun phrases from text.

    Returns list of (phrase_text, start_char, end_char).
    """
    if not text:
        return []

    nlp = _get_nlp()
    doc = nlp(text[:100_000])  # cap input

    results: list[tuple[str, int, int]] = []
    seen = set()

    for chunk in doc.noun_chunks:
        # Remove leading determiners/articles
        phrase = _clean_np(chunk.text)
        if not phrase:
            continue

        word_count = len(phrase.split())
        if word_count < min_words or word_count > max_words:
            continue

        lower = phrase.lower()
        if lower in seen:
            continue
        if _is_stopword_heavy(phrase):
            continue

        seen.add(lower)
        results.append((phrase, chunk.start_char, chunk.end_char))

    return results


def _clean_np(text: str) -> str:
    """Strip leading articles/determiners and clean up."""
    text = text.strip()
    # Remove leading determiners
    text = re.sub(r'^(the|a|an|this|that|these|those|some|any|each|every|my|your|his|her|its|our|their)\s+',
                  '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _is_stopword_heavy(phrase: str) -> bool:
    """Reject phrases that are mostly stopwords."""
    stopwords = {"the", "a", "an", "is", "are", "of", "in", "to", "and", "or",
                 "it", "this", "that", "for", "on", "with", "as", "by", "at"}
    words = phrase.lower().split()
    if not words:
        return True
    stop_count = sum(1 for w in words if w in stopwords)
    return stop_count / len(words) > 0.6
