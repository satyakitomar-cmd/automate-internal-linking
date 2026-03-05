"""Pipeline orchestrator — runs Steps A through H in sequence."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import Counter
from dataclasses import asdict
from typing import Any, Callable

from ..config import PipelineConfig
from ..types import Doc, Suggestion
from .anchor_discovery import discover_anchors
from .candidate_graph import build_candidate_graph
from .fetcher import fetch_all
from .filters import apply_soft_penalties, hard_filter
from .pointer import build_suggestions
from .profiler import profile_documents
from .selector import select_suggestions

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, int, int, str], None]


def _default_progress(stage: str, current: int, total: int, detail: str = "") -> None:
    pct = (current / total * 100) if total else 0
    logger.info("[%s] %d/%d (%.0f%%) %s", stage, current, total, pct, detail)


class PipelineResult:
    """Container for pipeline output."""

    def __init__(self) -> None:
        self.suggestions: dict[str, list[Suggestion]] = {}  # source_url -> suggestions
        self.docs: list[Doc] = []
        self.stats: dict[str, Any] = {}
        self.errors: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        output: dict[str, Any] = {
            "stats": self.stats,
            "errors": self.errors,
            "results": {},
        }
        for source_url, suggs in self.suggestions.items():
            output["results"][source_url] = [
                _suggestion_to_dict(s) for s in suggs
            ]
        return output

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def _suggestion_to_dict(s: Suggestion) -> dict[str, Any]:
    d: dict[str, Any] = {
        "source_url": s.source_url,
        "target_url": s.target_url,
        "anchor_text": s.anchor_text,
        "anchor_variants": s.anchor_variants,
        "context_snippet": s.context_snippet,
        "match_reason": s.match_reason,
        "confidence_score": s.confidence_score,
        "risk_flags": s.risk_flags,
        "scores": {
            "lexical": s.lexical_score,
            "semantic": s.semantic_score,
            "context": s.context_score,
            "quality": s.quality_score,
        },
    }
    if s.insertion_hint:
        d["insertion_hint"] = {
            "paragraph_index": s.insertion_hint.paragraph_index,
            "sentence_index": s.insertion_hint.sentence_index,
            "anchor_start": s.insertion_hint.anchor_start,
            "anchor_end": s.insertion_hint.anchor_end,
            "dom_path": s.insertion_hint.dom_path,
        }
    return d


def run_pipeline(
    urls: list[str],
    config: PipelineConfig | None = None,
    on_progress: ProgressCallback | None = None,
) -> PipelineResult:
    """Run the full internal linking pipeline synchronously.

    This is the main entry point for the pipeline.
    """
    return asyncio.run(_run_pipeline_async(urls, config, on_progress))


async def _run_pipeline_async(
    urls: list[str],
    config: PipelineConfig | None = None,
    on_progress: ProgressCallback | None = None,
) -> PipelineResult:
    """Async implementation of the pipeline."""
    if config is None:
        config = PipelineConfig()
    if on_progress is None:
        on_progress = _default_progress

    result = PipelineResult()
    start_time = time.time()

    # ── Step A: Fetch & extract ───────────────────────────────────────
    on_progress("fetch", 0, len(urls), "Starting fetch...")
    docs = await fetch_all(
        urls, config,
        on_progress=lambda cur, tot, url: on_progress("fetch", cur, tot, url),
    )
    result.docs = docs

    if len(docs) < 2:
        result.errors.append(f"Only {len(docs)} docs fetched successfully; need at least 2.")
        return result

    on_progress("fetch", len(docs), len(urls), f"Fetched {len(docs)} pages")

    # ── Step B: Profile documents ─────────────────────────────────────
    on_progress("profile", 0, len(docs), "Profiling documents...")
    profile_documents(
        docs, config,
        on_progress=lambda cur, tot, detail: on_progress("profile", cur, tot, detail),
    )
    on_progress("profile", len(docs), len(docs), "Profiling complete")

    # ── Step C: Build candidate graph ─────────────────────────────────
    on_progress("candidates", 0, 1, "Building candidate graph...")
    candidate_graph = build_candidate_graph(docs, config)
    on_progress("candidates", 1, 1, "Candidate graph built")

    # ── Steps D-H: For each source, discover, filter, select ──────────
    docs_by_id = {doc.doc_id: doc for doc in docs}
    global_target_counts: Counter = Counter()
    anchor_global_usage: dict[str, int] = {}
    total_sources = len(candidate_graph)

    for idx, (source_id, targets) in enumerate(candidate_graph.items()):
        source = docs_by_id[source_id]
        on_progress("analyze", idx + 1, total_sources, source.url)

        # Step D: Anchor discovery
        scored_anchors = discover_anchors(source, targets, config)

        if not scored_anchors:
            continue

        # Step F: Hard filters
        scored_anchors = hard_filter(scored_anchors, source, docs_by_id, config)

        # Step G: Soft penalties
        scored_anchors = apply_soft_penalties(
            scored_anchors, docs_by_id, global_target_counts, config
        )

        # Step E: Selection with MMR
        selected = select_suggestions(
            source, scored_anchors, docs_by_id, global_target_counts, config
        )

        # Step H: Build final suggestions
        suggestions = build_suggestions(source, selected, docs_by_id, anchor_global_usage)

        if suggestions:
            result.suggestions[source.url] = suggestions

    # ── Stats ─────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    total_suggestions = sum(len(v) for v in result.suggestions.values())
    result.stats = {
        "urls_submitted": len(urls),
        "urls_fetched": len(docs),
        "sources_with_suggestions": len(result.suggestions),
        "total_suggestions": total_suggestions,
        "elapsed_seconds": round(elapsed, 2),
    }

    on_progress("done", 1, 1, f"Complete: {total_suggestions} suggestions in {elapsed:.1f}s")
    return result
