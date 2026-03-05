"""Step D — Discover linkable anchor phrases in source docs and score against targets."""

from __future__ import annotations

import logging
import re

from ..config import PipelineConfig
from ..nlp.entities import extract_entities
from ..nlp.keyphrase import extract_keyphrases
from ..nlp.noun_phrases import extract_noun_phrases
from ..scoring.combined import score_anchor_against_target
from ..types import AnchorCandidate, Doc, ScoredAnchor

logger = logging.getLogger(__name__)


def _extract_anchor_candidates(
    doc: Doc,
    min_words: int = 2,
    max_words: int = 6,
) -> list[AnchorCandidate]:
    """Extract all candidate anchor spans from a document's paragraphs.

    Combines noun phrases, entities, and keyphrase spans.
    """
    candidates: list[AnchorCandidate] = []
    seen_texts: set[str] = set()

    for para in doc.paragraphs:
        for sent in para.sentences:
            sent_text = sent.text

            # ── Noun phrases ──────────────────────────────────────────
            nps = extract_noun_phrases(sent_text, min_words, max_words)
            for phrase, start, end in nps:
                key = f"{para.index}:{sent.index}:{phrase.lower()}"
                if key not in seen_texts:
                    seen_texts.add(key)
                    candidates.append(AnchorCandidate(
                        text=phrase,
                        paragraph_index=para.index,
                        sentence_index=sent.index,
                        start_char=start,
                        end_char=end,
                        context_sentence=sent_text,
                    ))

            # ── Named entities ────────────────────────────────────────
            entities = extract_entities(sent_text)
            for ent_text, label, start, end in entities:
                word_count = len(ent_text.split())
                # Allow single-word entities (brand names, etc.)
                if word_count > max_words:
                    continue
                key = f"{para.index}:{sent.index}:{ent_text.lower()}"
                if key not in seen_texts:
                    seen_texts.add(key)
                    candidates.append(AnchorCandidate(
                        text=ent_text,
                        paragraph_index=para.index,
                        sentence_index=sent.index,
                        start_char=start,
                        end_char=end,
                        context_sentence=sent_text,
                    ))

            # ── Keyphrase spans ───────────────────────────────────────
            keyphrases = extract_keyphrases(sent_text, min_words, max_words, top_n=10)
            for phrase, score in keyphrases:
                # Find position in sentence
                match = re.search(re.escape(phrase), sent_text, re.IGNORECASE)
                if match:
                    key = f"{para.index}:{sent.index}:{phrase.lower()}"
                    if key not in seen_texts:
                        seen_texts.add(key)
                        candidates.append(AnchorCandidate(
                            text=phrase,
                            paragraph_index=para.index,
                            sentence_index=sent.index,
                            start_char=match.start(),
                            end_char=match.end(),
                            context_sentence=sent_text,
                        ))

    return candidates


def _is_anchor_in_existing_link(doc: Doc, anchor: AnchorCandidate) -> bool:
    """Check if the anchor text overlaps with an existing <a> link in the source."""
    anchor_lower = anchor.text.lower()
    for link in doc.outbound_links:
        if anchor_lower in link.anchor_text.lower():
            return True
    return False


def discover_anchors(
    source: Doc,
    targets: list[Doc],
    config: PipelineConfig,
) -> list[ScoredAnchor]:
    """For a source doc, find and score anchor opportunities against each target.

    Returns all scored anchors above threshold.
    """
    min_w = config.site_rules.anchor_length_min_words
    max_w = config.site_rules.anchor_length_max_words

    # D1: Extract all anchor candidates from source
    all_anchors = _extract_anchor_candidates(source, min_w, max_w)
    logger.debug("Source %s: %d anchor candidates", source.url, len(all_anchors))

    scored: list[ScoredAnchor] = []

    for target in targets:
        pair_scores: list[ScoredAnchor] = []

        for anchor in all_anchors:
            # Skip if anchor is inside an existing link
            if _is_anchor_in_existing_link(source, anchor):
                continue

            # D2: Score this anchor against this target
            sa = score_anchor_against_target(source, anchor, target, config)

            if sa.combined >= config.score_threshold:
                pair_scores.append(sa)

        # Keep top N per (source, target) pair
        pair_scores.sort(key=lambda s: s.combined, reverse=True)
        scored.extend(pair_scores[:config.max_anchors_per_pair])

    logger.debug(
        "Source %s: %d scored anchors across %d targets",
        source.url, len(scored), len(targets),
    )
    return scored
