"""Step B — Build document profiles: embeddings, target terms, intent."""

from __future__ import annotations

import logging

from ..config import PipelineConfig
from ..nlp.embeddings import embed_texts
from ..nlp.entities import extract_entities
from ..nlp.intent import classify_intent
from ..nlp.keyphrase import extract_informative_ngrams, extract_keyphrases
from ..nlp.noun_phrases import extract_noun_phrases
from ..types import Doc, TargetTerm, TargetTermType

logger = logging.getLogger(__name__)


def _build_embedding_text(doc: Doc, intro_paragraphs: int = 3) -> str:
    """Combine title + headings + first N paragraphs for embedding."""
    parts = [doc.title]
    parts.extend(doc.headings)
    for p in doc.paragraphs[:intro_paragraphs]:
        parts.append(p.text)
    if doc.meta_description:
        parts.append(doc.meta_description)
    return " ".join(parts)


def profile_documents(
    docs: list[Doc],
    config: PipelineConfig,
    on_progress: callable | None = None,
) -> None:
    """Profile all documents in-place: add embeddings, target terms, and intent.

    Mutates docs directly.
    """
    total = len(docs)
    if not docs:
        return

    # ── B1: Compute embeddings in batch ──────────────────────────────
    logger.info("Computing embeddings for %d documents...", total)
    embed_inputs = [
        _build_embedding_text(doc, config.embedding_intro_paragraphs)
        for doc in docs
    ]
    embeddings = embed_texts(embed_inputs, model_name=config.embedding_model)

    for i, doc in enumerate(docs):
        doc.embedding = embeddings[i]

    # ── B2: Extract target terms + B3: classify intent ───────────────
    for i, doc in enumerate(docs):
        body = doc.body_text

        # Keyphrases (RAKE)
        keyphrases = extract_keyphrases(
            body,
            min_words=config.site_rules.anchor_length_min_words,
            max_words=config.site_rules.anchor_length_max_words,
        )
        for phrase, score in keyphrases:
            doc.target_terms.append(TargetTerm(
                term=phrase,
                term_type=TargetTermType.KEYPHRASE,
                weight=score,
            ))

        # Noun phrases
        nps = extract_noun_phrases(
            body,
            min_words=config.site_rules.anchor_length_min_words,
            max_words=config.site_rules.anchor_length_max_words,
        )
        existing = {t.term.lower() for t in doc.target_terms}
        for phrase, _, _ in nps:
            if phrase.lower() not in existing:
                doc.target_terms.append(TargetTerm(
                    term=phrase,
                    term_type=TargetTermType.NOUN_PHRASE,
                    weight=1.0,
                ))
                existing.add(phrase.lower())

        # Named entities
        entities = extract_entities(body)
        for ent_text, label, _, _ in entities:
            if ent_text.lower() not in existing:
                doc.target_terms.append(TargetTerm(
                    term=ent_text,
                    term_type=TargetTermType.ENTITY,
                    weight=1.5,  # entities get a boost
                ))
                existing.add(ent_text.lower())

        # Informative n-grams
        ngrams = extract_informative_ngrams(body)
        for phrase, score in ngrams:
            if phrase.lower() not in existing:
                doc.target_terms.append(TargetTerm(
                    term=phrase,
                    term_type=TargetTermType.NGRAM,
                    weight=score,
                ))
                existing.add(phrase.lower())

        # Cap target terms
        if len(doc.target_terms) > config.max_target_terms:
            doc.target_terms.sort(key=lambda t: t.weight, reverse=True)
            doc.target_terms = doc.target_terms[:config.max_target_terms]

        # ── B3: Intent classification ─────────────────────────────────
        doc.intent = classify_intent(doc.url, doc.title, doc.headings, body)

        if on_progress:
            on_progress(i + 1, total, f"Profiled {doc.url}")

    logger.info(
        "Profiled %d documents (avg %.0f target terms each)",
        total,
        sum(len(d.target_terms) for d in docs) / max(total, 1),
    )
