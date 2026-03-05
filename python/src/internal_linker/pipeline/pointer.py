"""Step H — Generate actionable insertion hints for each suggestion."""

from __future__ import annotations

import re

from ..types import Doc, InsertionPointer, ScoredAnchor, Suggestion


def _build_context_snippet(
    doc: Doc,
    para_idx: int,
    sent_idx: int,
    anchor_text: str,
) -> str:
    """Build a context snippet (1-2 sentences) with anchor highlighted."""
    if para_idx >= len(doc.paragraphs):
        return ""

    para = doc.paragraphs[para_idx]
    sentences = para.sentences

    # Get the target sentence and optionally one neighbor
    snippets: list[str] = []
    for s in sentences:
        if abs(s.index - sent_idx) <= 1:
            snippets.append(s.text)

    context = " ".join(snippets)

    # Highlight anchor in context
    highlighted = re.sub(
        re.escape(anchor_text),
        f"[{anchor_text}]",
        context,
        count=1,
        flags=re.IGNORECASE,
    )
    return highlighted


def _get_dom_path(doc: Doc, para_idx: int) -> str:
    """Get the DOM path for a paragraph."""
    if para_idx < len(doc.paragraphs):
        return doc.paragraphs[para_idx].html_path
    return ""


def _generate_match_reason(scored: ScoredAnchor) -> str:
    """Generate a human-readable match reason."""
    reasons: list[str] = []
    if scored.lexical > 0.5:
        reasons.append("strong lexical match")
    elif scored.lexical > 0.3:
        reasons.append("topic overlap")
    if scored.semantic > 0.6:
        reasons.append("high semantic similarity")
    elif scored.semantic > 0.4:
        reasons.append("semantic relevance")
    if scored.context > 0.7:
        reasons.append("good context placement")
    if scored.quality > 0.7:
        reasons.append("quality anchor text")
    if not reasons:
        reasons.append("multi-signal match")
    return ", ".join(reasons)


def _generate_risk_flags(
    scored: ScoredAnchor,
    anchor_global_usage: dict[str, int],
) -> list[str]:
    """Generate risk flags for a suggestion."""
    flags: list[str] = []
    anchor_lower = scored.anchor.text.lower()
    usage = anchor_global_usage.get(anchor_lower, 0)

    if usage >= 4:
        flags.append(f"anchor already used {usage}x")
    if scored.lexical < 0.2:
        flags.append("weak lexical match")
    if scored.semantic < 0.3:
        flags.append("weak topical match")
    if scored.quality < 0.5:
        flags.append("low anchor quality")
    if scored.combined < 0.65:
        flags.append("borderline confidence")

    return flags


def build_suggestions(
    source: Doc,
    selected: list[ScoredAnchor],
    docs_by_id: dict[str, Doc],
    anchor_global_usage: dict[str, int],
) -> list[Suggestion]:
    """Convert scored anchors into final Suggestion objects with insertion hints."""
    suggestions: list[Suggestion] = []

    for scored in selected:
        target = docs_by_id.get(scored.target_doc_id)
        if target is None:
            continue

        pointer = InsertionPointer(
            paragraph_index=scored.anchor.paragraph_index,
            sentence_index=scored.anchor.sentence_index,
            anchor_start=scored.anchor.start_char,
            anchor_end=scored.anchor.end_char,
            dom_path=_get_dom_path(source, scored.anchor.paragraph_index),
        )

        context = _build_context_snippet(
            source,
            scored.anchor.paragraph_index,
            scored.anchor.sentence_index,
            scored.anchor.text,
        )

        reason = _generate_match_reason(scored)
        risk_flags = _generate_risk_flags(scored, anchor_global_usage)

        # Track anchor usage globally
        anchor_lower = scored.anchor.text.lower()
        anchor_global_usage[anchor_lower] = anchor_global_usage.get(anchor_lower, 0) + 1

        suggestion = Suggestion(
            source_url=source.url,
            target_url=target.url,
            anchor_text=scored.anchor.text,
            context_snippet=context,
            insertion_hint=pointer,
            match_reason=reason,
            confidence_score=round(scored.combined, 4),
            risk_flags=risk_flags,
            lexical_score=round(scored.lexical, 4),
            semantic_score=round(scored.semantic, 4),
            context_score=round(scored.context, 4),
            quality_score=round(scored.quality, 4),
        )
        suggestions.append(suggestion)

    return suggestions
