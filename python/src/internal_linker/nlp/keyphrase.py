"""Keyphrase extraction using RAKE algorithm."""

from __future__ import annotations

import logging
import re
from collections import Counter

from rake_nltk import Rake

logger = logging.getLogger(__name__)


def extract_keyphrases(
    text: str,
    min_words: int = 2,
    max_words: int = 6,
    top_n: int = 100,
) -> list[tuple[str, float]]:
    """Extract keyphrases with RAKE scores.

    Returns list of (phrase, score) sorted by score descending.
    """
    if not text or len(text.split()) < 10:
        return []

    rake = Rake(
        min_length=min_words,
        max_length=max_words,
    )
    rake.extract_keywords_from_text(text)
    ranked = rake.get_ranked_phrases_with_scores()

    # Filter: remove stopword-only, too generic, and clean up
    results: list[tuple[str, float]] = []
    seen = set()

    for score, phrase in ranked[:top_n * 2]:
        phrase = _clean_phrase(phrase)
        if not phrase or phrase.lower() in seen:
            continue
        if _is_generic(phrase):
            continue
        word_count = len(phrase.split())
        if word_count < min_words or word_count > max_words:
            continue
        seen.add(phrase.lower())
        results.append((phrase, float(score)))

    return results[:top_n]


def extract_informative_ngrams(
    text: str,
    n_range: tuple[int, int] = (2, 5),
    top_n: int = 50,
) -> list[tuple[str, float]]:
    """Extract frequent informative n-grams using simple TF weighting."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())

    # Stopwords (minimal set)
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
        "under", "again", "further", "then", "once", "and", "but", "or",
        "nor", "not", "so", "yet", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "only", "own", "same", "than", "too",
        "very", "just", "because", "about", "this", "that", "these", "those",
        "it", "its", "they", "them", "their", "we", "our", "you", "your",
        "he", "she", "his", "her", "which", "who", "what", "when", "where",
        "how", "all", "also", "here", "there",
    }

    ngram_counts: Counter = Counter()
    for n in range(n_range[0], n_range[1] + 1):
        for i in range(len(words) - n + 1):
            gram = tuple(words[i:i + n])
            # Skip if all stopwords
            if all(w in stopwords for w in gram):
                continue
            # Skip if starts or ends with stopword
            if gram[0] in stopwords or gram[-1] in stopwords:
                continue
            ngram_counts[gram] += 1

    # Score by frequency * length
    scored = []
    total = sum(ngram_counts.values()) or 1
    for gram, count in ngram_counts.most_common(top_n * 3):
        if count < 2:
            continue
        phrase = " ".join(gram)
        if _is_generic(phrase):
            continue
        tf = count / total
        score = tf * len(gram)  # prefer longer, more frequent
        scored.append((phrase, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def _clean_phrase(phrase: str) -> str:
    """Clean extracted phrase."""
    phrase = re.sub(r'[^\w\s\'-]', '', phrase).strip()
    phrase = re.sub(r'\s+', ' ', phrase)
    return phrase


_GENERIC_PHRASES = {
    "click here", "read more", "learn more", "introduction", "conclusion",
    "this article", "this post", "blog post", "related posts", "see also",
    "more information", "find out", "check out", "take look", "get started",
    "next step", "previous post", "latest news", "home page",
}


def _is_generic(phrase: str) -> bool:
    return phrase.lower().strip() in _GENERIC_PHRASES
