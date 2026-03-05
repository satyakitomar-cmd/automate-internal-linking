"""Named Entity Recognition using spaCy."""

from __future__ import annotations

import logging
from typing import Sequence

logger = logging.getLogger(__name__)

_nlp = None

# Entity types we care about for internal linking
_RELEVANT_LABELS = {"PERSON", "ORG", "PRODUCT", "GPE", "LOC", "EVENT", "WORK_OF_ART", "LAW"}


def _get_nlp():
    """Lazy-load spaCy model (singleton)."""
    global _nlp
    if _nlp is None:
        import spacy
        logger.info("Loading spaCy model: en_core_web_sm")
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
    return _nlp


def extract_entities(
    text: str,
    relevant_labels: set[str] | None = None,
) -> list[tuple[str, str, int, int]]:
    """Extract named entities from text.

    Returns list of (entity_text, label, start_char, end_char).
    """
    if not text:
        return []

    nlp = _get_nlp()
    labels = relevant_labels or _RELEVANT_LABELS

    doc = nlp(text[:100_000])  # cap for safety
    results: list[tuple[str, str, int, int]] = []
    seen = set()

    for ent in doc.ents:
        if ent.label_ not in labels:
            continue
        text_clean = ent.text.strip()
        if not text_clean or text_clean.lower() in seen:
            continue
        if len(text_clean.split()) > 6:
            continue
        seen.add(text_clean.lower())
        results.append((text_clean, ent.label_, ent.start_char, ent.end_char))

    return results


def extract_entities_batch(
    texts: Sequence[str],
    relevant_labels: set[str] | None = None,
) -> list[list[tuple[str, str, int, int]]]:
    """Extract entities from multiple texts using spaCy pipe for efficiency."""
    if not texts:
        return []

    nlp = _get_nlp()
    labels = relevant_labels or _RELEVANT_LABELS
    all_results: list[list[tuple[str, str, int, int]]] = []

    for doc in nlp.pipe(texts, batch_size=32):
        results: list[tuple[str, str, int, int]] = []
        seen = set()
        for ent in doc.ents:
            if ent.label_ not in labels:
                continue
            text_clean = ent.text.strip()
            if not text_clean or text_clean.lower() in seen:
                continue
            if len(text_clean.split()) > 6:
                continue
            seen.add(text_clean.lower())
            results.append((text_clean, ent.label_, ent.start_char, ent.end_char))
        all_results.append(results)

    return all_results
