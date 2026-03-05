"""Rule-based page intent classification."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from ..types import PageIntent


def classify_intent(
    url: str,
    title: str,
    headings: list[str],
    body_text: str = "",
) -> PageIntent:
    """Classify page intent using URL patterns and heading keywords.

    Categories: informational, how-to, comparison, product, category,
                glossary, case-study, unknown
    """
    url_lower = url.lower()
    title_lower = title.lower()
    headings_lower = " ".join(headings).lower()
    combined = f"{title_lower} {headings_lower}"

    path = urlparse(url_lower).path

    # ── Glossary ──────────────────────────────────────────────────────
    if any(k in path for k in ["/glossary", "/dictionary", "/terminology", "/definitions"]):
        return PageIntent.GLOSSARY
    if any(k in combined for k in ["what is ", "what are ", "definition of ", "meaning of ",
                                    " refers to", " defined as"]):
        return PageIntent.GLOSSARY

    # ── How-to ────────────────────────────────────────────────────────
    if any(k in path for k in ["/how-to", "/tutorial", "/guide", "/step-by-step"]):
        return PageIntent.HOW_TO
    if any(k in combined for k in ["how to ", "step by step", "tutorial", "beginner's guide",
                                    "complete guide", "getting started"]):
        return PageIntent.HOW_TO

    # ── Comparison ────────────────────────────────────────────────────
    if any(k in path for k in ["/compare", "/comparison", "/vs-", "-vs-"]):
        return PageIntent.COMPARISON
    if any(k in combined for k in [" vs ", " versus ", "comparison", "compared to",
                                    " alternatives", "best ", "top "]):
        return PageIntent.COMPARISON

    # ── Product ───────────────────────────────────────────────────────
    if any(k in path for k in ["/product", "/pricing", "/features", "/plans"]):
        return PageIntent.PRODUCT
    if any(k in combined for k in ["pricing", "free trial", "sign up", "buy now",
                                    "get started free", "our product"]):
        return PageIntent.PRODUCT

    # ── Category ──────────────────────────────────────────────────────
    if any(k in path for k in ["/category/", "/tag/", "/topic/", "/topics/"]):
        return PageIntent.CATEGORY

    # ── Case study ────────────────────────────────────────────────────
    if any(k in path for k in ["/case-study", "/case-studies", "/success-story"]):
        return PageIntent.CASE_STUDY
    if any(k in combined for k in ["case study", "success story", "customer story",
                                    "how * achieved", "how * increased"]):
        return PageIntent.CASE_STUDY

    # ── Informational (default) ───────────────────────────────────────
    # Check for informational signals
    if any(k in combined for k in ["guide", "explained", "overview", "introduction",
                                    "everything you need to know", "understanding"]):
        return PageIntent.INFORMATIONAL

    return PageIntent.INFORMATIONAL  # safe default
