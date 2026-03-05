"""Core data types for the internal linking pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class PageIntent(str, Enum):
    INFORMATIONAL = "informational"
    HOW_TO = "how-to"
    COMPARISON = "comparison"
    PRODUCT = "product"
    CATEGORY = "category"
    GLOSSARY = "glossary"
    CASE_STUDY = "case-study"
    UNKNOWN = "unknown"


class TargetTermType(str, Enum):
    ENTITY = "entity"
    NOUN_PHRASE = "noun_phrase"
    NGRAM = "ngram"
    KEYPHRASE = "keyphrase"


class ExistingLinkPolicy(str, Enum):
    SKIP = "skip"  # skip if source already links to target
    ALLOW_DIFFERENT_ANCHOR = "allow_different_anchor"


# ── Sentence / Paragraph ──────────────────────────────────────────────


@dataclass
class Sentence:
    text: str
    index: int  # position within paragraph
    start_char: int  # char offset in paragraph
    end_char: int


@dataclass
class OutboundLink:
    href: str
    anchor_text: str
    paragraph_index: int
    sentence_index: int
    is_internal: bool = False


@dataclass
class Paragraph:
    text: str
    index: int  # position in document
    sentences: list[Sentence] = field(default_factory=list)
    html_path: str = ""  # CSS selector / DOM path


# ── Target Term ───────────────────────────────────────────────────────


@dataclass
class TargetTerm:
    term: str
    term_type: TargetTermType
    weight: float = 1.0


# ── Document ──────────────────────────────────────────────────────────


@dataclass
class Doc:
    doc_id: str
    url: str
    title: str = ""
    headings: list[str] = field(default_factory=list)
    paragraphs: list[Paragraph] = field(default_factory=list)
    outbound_links: list[OutboundLink] = field(default_factory=list)
    internal_links: list[OutboundLink] = field(default_factory=list)
    embedding: Optional[np.ndarray] = field(default=None, repr=False)
    target_terms: list[TargetTerm] = field(default_factory=list)
    intent: PageIntent = PageIntent.UNKNOWN
    meta_description: str = ""
    word_count: int = 0
    incoming_suggestion_count: int = 0  # for orphan boosting

    @property
    def body_text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs)

    @property
    def linked_urls(self) -> set[str]:
        return {link.href for link in self.outbound_links}


# ── Anchor Candidate ─────────────────────────────────────────────────


@dataclass
class AnchorCandidate:
    text: str
    paragraph_index: int
    sentence_index: int
    start_char: int  # offset within sentence
    end_char: int
    context_sentence: str = ""


# ── Insertion Pointer ─────────────────────────────────────────────────


@dataclass
class InsertionPointer:
    paragraph_index: int
    sentence_index: int
    anchor_start: int
    anchor_end: int
    dom_path: str = ""


# ── Suggestion ────────────────────────────────────────────────────────


@dataclass
class Suggestion:
    source_url: str
    target_url: str
    anchor_text: str
    anchor_variants: list[str] = field(default_factory=list)
    context_snippet: str = ""
    insertion_hint: Optional[InsertionPointer] = None
    match_reason: str = ""
    confidence_score: float = 0.0
    risk_flags: list[str] = field(default_factory=list)

    # internal scoring breakdown
    lexical_score: float = 0.0
    semantic_score: float = 0.0
    context_score: float = 0.0
    quality_score: float = 0.0


# ── Scored pair (intermediate) ────────────────────────────────────────


@dataclass
class ScoredAnchor:
    """An anchor candidate scored against a specific target."""
    anchor: AnchorCandidate
    target_doc_id: str
    target_url: str
    lexical: float = 0.0
    semantic: float = 0.0
    context: float = 0.0
    quality: float = 0.0
    combined: float = 0.0
