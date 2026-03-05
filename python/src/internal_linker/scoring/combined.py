"""Combined scoring: weighted ensemble of all score components."""

from __future__ import annotations

from ..config import PipelineConfig
from ..types import AnchorCandidate, Doc, ScoredAnchor
from .context import context_score
from .lexical import lexical_score
from .quality import anchor_quality_score
from .semantic import semantic_score


def score_anchor_against_target(
    source_doc: Doc,
    anchor: AnchorCandidate,
    target_doc: Doc,
    config: PipelineConfig,
) -> ScoredAnchor:
    """Compute the combined score for an anchor-target pair.

    Returns a ScoredAnchor with individual and combined scores.
    """
    # Lexical score
    target_term_strings = [t.term for t in target_doc.target_terms]
    lex = lexical_score(
        anchor_text=anchor.text,
        target_terms=target_term_strings,
        target_title=target_doc.title,
        target_headings=target_doc.headings,
    )

    # Semantic score
    sem = semantic_score(
        anchor_context_sentence=anchor.context_sentence,
        target_embedding=target_doc.embedding,
        model_name=config.embedding_model,
    )

    # Context suitability
    ctx = context_score(source_doc, anchor)

    # Anchor quality
    qual = anchor_quality_score(anchor.text)

    # Weighted combination
    combined = (
        config.weight_lexical * lex
        + config.weight_semantic * sem
        + config.weight_context * ctx
        + config.weight_quality * qual
    )

    return ScoredAnchor(
        anchor=anchor,
        target_doc_id=target_doc.doc_id,
        target_url=target_doc.url,
        lexical=lex,
        semantic=sem,
        context=ctx,
        quality=qual,
        combined=combined,
    )
