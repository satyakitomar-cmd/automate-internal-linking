"""Pipeline configuration with sensible defaults."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .types import ExistingLinkPolicy


class SiteRules(BaseModel):
    """Per-site overrides."""
    domain: str = ""
    allowed_subdomains: list[str] = Field(default_factory=list)
    max_links_per_source_page: int = 5
    max_links_per_target_page: int = 20
    anchor_length_min_words: int = 2
    anchor_length_max_words: int = 6
    avoid_sections: list[str] = Field(
        default_factory=lambda: ["Related Posts", "nav", "footer", "sidebar", "author bio", "comments"]
    )
    existing_link_policy: ExistingLinkPolicy = ExistingLinkPolicy.SKIP
    language: Optional[str] = None  # auto-detect if None


class PipelineConfig(BaseModel):
    """All tunable parameters for the linking pipeline."""

    # ── Fetching ──────────────────────────────────────────────────────
    fetch_timeout_seconds: int = 30
    fetch_max_concurrent: int = 10
    user_agent: str = "InternalLinker/0.1"

    # ── Embedding ─────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_intro_paragraphs: int = 3  # how many leading paragraphs to embed

    # ── Target term extraction ────────────────────────────────────────
    min_target_terms: int = 30
    max_target_terms: int = 200

    # ── Candidate graph (Step C) ──────────────────────────────────────
    top_k_targets_per_source: int = 20
    near_duplicate_threshold: float = 0.92

    # ── Anchor scoring (Step D) ───────────────────────────────────────
    weight_lexical: float = 0.35
    weight_semantic: float = 0.35
    weight_context: float = 0.15
    weight_quality: float = 0.15
    score_threshold: float = 0.62
    max_anchors_per_pair: int = 3

    # ── Selection (Step E) ────────────────────────────────────────────
    max_suggestions_per_source: int = 5
    max_same_target_per_source: int = 1
    max_suggestions_to_same_target_global: int = 20
    mmr_lambda: float = 0.75
    orphan_boost_factor: float = 1.15  # multiplier for targets with few inlinks

    # ── Filters (Steps F & G) ─────────────────────────────────────────
    max_anchor_frequency_in_source: int = 10  # reject if anchor phrase appears >N times
    commercial_penalty: float = 0.10
    target_saturation_penalty: float = 0.05  # per extra suggestion to same target

    # ── Site rules ────────────────────────────────────────────────────
    site_rules: SiteRules = Field(default_factory=SiteRules)

    # ── Output ────────────────────────────────────────────────────────
    output_format: str = "json"  # json | csv
