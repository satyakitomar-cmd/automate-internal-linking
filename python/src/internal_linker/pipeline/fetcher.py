"""Step A — Fetch HTML and extract clean, structured content."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup, Tag
from readability import Document as ReadabilityDoc

from ..config import PipelineConfig
from ..types import Doc, OutboundLink, Paragraph, Sentence

logger = logging.getLogger(__name__)

# Sections to strip before extraction
_STRIP_SELECTORS = [
    "nav", "footer", "aside", "header",
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    ".sidebar", ".widget", ".comments", ".comment-list",
    ".author-bio", ".author-info", ".byline",
    ".related-posts", ".related-articles", ".more-stories",
    ".social-share", ".share-buttons",
    ".ad", ".advertisement", ".sponsored",
    "script", "style", "noscript", "iframe",
]


def _make_doc_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _sentence_split(text: str) -> list[str]:
    """Simple rule-based sentence splitter (avoids spaCy dependency at fetch time)."""
    # Split on sentence-ending punctuation followed by space+uppercase
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    return [s.strip() for s in parts if s.strip()]


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[OutboundLink]:
    """Extract all <a> links with context."""
    links: list[OutboundLink] = []
    base_domain = urlparse(base_url).netloc

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        anchor_text = a_tag.get_text(strip=True)
        if not anchor_text or not href:
            continue

        target_domain = urlparse(full_url).netloc
        is_internal = target_domain == base_domain

        links.append(OutboundLink(
            href=full_url,
            anchor_text=anchor_text,
            paragraph_index=-1,  # will be refined later
            sentence_index=-1,
            is_internal=is_internal,
        ))

    return links


def _clean_text(text: str) -> str:
    """Collapse whitespace, strip."""
    return re.sub(r'\s+', ' ', text).strip()


def _extract_headings(soup: BeautifulSoup) -> list[str]:
    headings: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = _clean_text(tag.get_text())
        if text:
            headings.append(text)
    return headings


def _should_skip_section(text: str, avoid_sections: list[str]) -> bool:
    text_lower = text.lower()
    for section in avoid_sections:
        if section.lower() in text_lower:
            return True
    return False


def _extract_paragraphs(
    soup: BeautifulSoup,
    avoid_sections: list[str],
) -> list[Paragraph]:
    """Extract paragraphs with sentences and stable indices."""
    paragraphs: list[Paragraph] = []
    para_index = 0

    for p_tag in soup.find_all("p"):
        text = _clean_text(p_tag.get_text())
        if not text or len(text) < 20:
            continue

        # Skip avoided sections
        if _should_skip_section(text, avoid_sections):
            continue

        # Build CSS-like path
        html_path = _build_dom_path(p_tag)

        # Split into sentences
        raw_sentences = _sentence_split(text)
        sentences: list[Sentence] = []
        char_offset = 0
        for sent_i, sent_text in enumerate(raw_sentences):
            start = text.find(sent_text, char_offset)
            if start == -1:
                start = char_offset
            end = start + len(sent_text)
            sentences.append(Sentence(
                text=sent_text,
                index=sent_i,
                start_char=start,
                end_char=end,
            ))
            char_offset = end

        paragraphs.append(Paragraph(
            text=text,
            index=para_index,
            sentences=sentences,
            html_path=html_path,
        ))
        para_index += 1

    return paragraphs


def _build_dom_path(tag: Tag) -> str:
    """Build a simplified CSS selector path for a tag."""
    parts: list[str] = []
    current = tag
    for _ in range(6):  # max depth
        if current is None or current.name is None:
            break
        name = current.name
        if current.get("id"):
            parts.append(f"{name}#{current['id']}")
            break
        css_class = current.get("class")
        if css_class:
            parts.append(f"{name}.{css_class[0]}")
        else:
            parts.append(name)
        current = current.parent
    return " > ".join(reversed(parts))


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    """Remove nav, footer, sidebar, comments, author bio, etc. in-place."""
    for selector in _STRIP_SELECTORS:
        for el in soup.select(selector):
            el.decompose()


async def fetch_single(
    url: str,
    session: aiohttp.ClientSession,
    config: PipelineConfig,
) -> Doc | None:
    """Fetch and parse a single URL into a Doc."""
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=config.fetch_timeout_seconds),
            headers={"User-Agent": config.user_agent},
        ) as resp:
            if resp.status != 200:
                logger.warning("HTTP %d for %s", resp.status, url)
                return None
            html = await resp.text()
    except Exception as exc:
        logger.error("Fetch failed for %s: %s", url, exc)
        return None

    # Use readability to get main content
    try:
        readable = ReadabilityDoc(html)
        title = readable.title()
        content_html = readable.summary()
    except Exception as exc:
        logger.error("Readability extraction failed for %s: %s", url, exc)
        return None

    # Parse the cleaned content
    soup = BeautifulSoup(content_html, "lxml")
    _strip_boilerplate(soup)

    # Also parse full HTML for link extraction
    full_soup = BeautifulSoup(html, "lxml")

    headings = _extract_headings(soup)
    avoid = config.site_rules.avoid_sections
    paragraphs = _extract_paragraphs(soup, avoid)
    all_links = _extract_links(full_soup, url)

    internal_links = [l for l in all_links if l.is_internal]
    outbound_links = all_links

    word_count = sum(len(p.text.split()) for p in paragraphs)

    # Try to get meta description from full HTML
    meta_desc = ""
    meta_tag = full_soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = str(meta_tag["content"])

    return Doc(
        doc_id=_make_doc_id(url),
        url=url,
        title=title,
        headings=headings,
        paragraphs=paragraphs,
        outbound_links=outbound_links,
        internal_links=internal_links,
        meta_description=meta_desc,
        word_count=word_count,
    )


async def fetch_all(
    urls: list[str],
    config: PipelineConfig,
    on_progress: callable | None = None,
) -> list[Doc]:
    """Fetch all URLs concurrently with rate limiting."""
    semaphore = asyncio.Semaphore(config.fetch_max_concurrent)
    docs: list[Doc] = []
    total = len(urls)

    async def _fetch_with_sem(url: str, idx: int) -> Doc | None:
        async with semaphore:
            doc = await fetch_single(url, session, config)
            if on_progress:
                on_progress(idx + 1, total, url)
            return doc

    connector = aiohttp.TCPConnector(limit=config.fetch_max_concurrent, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [_fetch_with_sem(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Doc):
            docs.append(result)
        elif isinstance(result, Exception):
            logger.error("Fetch task exception: %s", result)

    logger.info("Fetched %d / %d URLs successfully", len(docs), total)
    return docs
