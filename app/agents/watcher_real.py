"""
Watcher Agent — Person A (Week 1)
Polls RSS feeds for RBI, SEBI, MCA circulars.
Returns structured CircularDoc objects ready for the pipeline.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Data contract shared across all agents ──────────────────────────────────

@dataclass
class CircularDoc:
    url: str
    title: str
    regulator: str          # "RBI" | "SEBI" | "MCA"
    published_at: datetime
    raw_text: str           # full extracted text for MAP extractor
    source: str             # "rss" | "email"
    url_hash: str = field(init=False)

    def __post_init__(self):
        self.url_hash = hashlib.sha256(self.url.encode()).hexdigest()


# ── RSS feed registry ────────────────────────────────────────────────────────

FEEDS = {
    "RBI": [
        "https://www.rbi.org.in/scripts/rss.aspx?Id=13",   # Circulars
        "https://www.rbi.org.in/scripts/rss.aspx?Id=7",    # Press releases
        "https://www.rbi.org.in/scripts/rss.aspx?Id=37",   # Master Directions
    ],
    "SEBI": [
        "https://www.sebi.gov.in/sebirss.xml",              # All SEBI updates
    ],
    "MCA": [
        # MCA doesn't have a clean RSS — we scrape their notifications page
        # handled separately in _fetch_mca_circulars()
    ],
}

MCA_NOTIFICATIONS_URL = "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html"


class WatcherAgent:
    """
    Polls all configured feeds and returns new CircularDoc objects.
    Person C's orchestrator calls .fetch_all() on a schedule.
    """

    def __init__(self, request_timeout: int = 15):
        self.timeout = request_timeout

    # ── Public API ───────────────────────────────────────────────────────────

    def fetch_all(self) -> list[CircularDoc]:
        """Fetch from all regulators. Returns deduplicated list of CircularDocs."""
        docs = []
        docs.extend(self._fetch_rss_feeds())
        docs.extend(self._fetch_mca_circulars())
        logger.info(f"WatcherAgent fetched {len(docs)} circulars total")
        return docs

    def fetch_single(self, url: str, regulator: str) -> Optional[CircularDoc]:
        """Fetch a single circular by URL — used by orchestrator for manual triggers."""
        text = self._extract_text_from_url(url)
        if not text:
            return None
        return CircularDoc(
            url=url,
            title="Manual fetch",
            regulator=regulator,
            published_at=datetime.utcnow(),
            raw_text=text,
            source="manual",
        )

    # ── RSS fetching ─────────────────────────────────────────────────────────

    def _fetch_rss_feeds(self) -> list[CircularDoc]:
        docs = []
        for regulator, urls in FEEDS.items():
            for feed_url in urls:
                try:
                    docs.extend(self._parse_feed(feed_url, regulator))
                except Exception as e:
                    logger.error(f"Feed failed [{regulator}] {feed_url}: {e}")
        return docs

    def _parse_feed(self, feed_url: str, regulator: str) -> list[CircularDoc]:
        feed = feedparser.parse(feed_url)
        docs = []

        for entry in feed.entries:
            url   = entry.get("link", "")
            title = entry.get("title", "No title")

            if not url:
                continue

            pub = self._parse_date(entry)
            text = self._extract_text_from_url(url)

            if text:
                docs.append(CircularDoc(
                    url=url,
                    title=title.strip(),
                    regulator=regulator,
                    published_at=pub,
                    raw_text=text,
                    source="rss",
                ))
                logger.debug(f"Fetched [{regulator}] {title[:60]}")

        return docs

    # ── MCA scraper (no RSS available) ───────────────────────────────────────

    def _fetch_mca_circulars(self) -> list[CircularDoc]:
        """
        MCA doesn't publish RSS. We scrape their circulars listing page
        and extract links to individual circular PDFs/pages.
        """
        docs = []
        try:
            resp = requests.get(MCA_NOTIFICATIONS_URL, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # MCA lists circulars as anchor tags inside a table
            for a in soup.select("table a[href]"):
                href = a["href"]
                title = a.get_text(strip=True)
                if not href.startswith("http"):
                    href = "https://www.mca.gov.in" + href

                text = self._extract_text_from_url(href)
                if text:
                    docs.append(CircularDoc(
                        url=href,
                        title=title,
                        regulator="MCA",
                        published_at=datetime.utcnow(),
                        raw_text=text,
                        source="rss",  # treated as rss for pipeline purposes
                    ))
        except Exception as e:
            logger.error(f"MCA scraper failed: {e}")

        return docs

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_text_from_url(self, url: str) -> Optional[str]:
        """
        Extracts readable text from a URL.
        Handles HTML pages. PDF handling added in Week 2 (pdfplumber).
        """
        try:
            resp = requests.get(url, timeout=self.timeout, headers={
                "User-Agent": "RegWatch/1.0 (compliance-bot)"
            })
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")

            if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                import pdfplumber
                from io import BytesIO
                try:
                    with pdfplumber.open(BytesIO(resp.content)) as pdf:
                        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    return text if len(text) > 100 else None
                except Exception as pdf_e:
                    logger.error(f"PDF extraction failed for {url}: {pdf_e}")
                    return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove nav, footer, scripts, styles — keep body content
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            return text if len(text) > 100 else None

        except Exception as e:
            logger.debug(f"Text extraction failed for {url}: {e}")
            return None

    def _parse_date(self, entry) -> datetime:
        """Safely parse published date from feed entry."""
        try:
            import time
            t = entry.get("published_parsed") or entry.get("updated_parsed")
            if t:
                return datetime.fromtimestamp(time.mktime(t))
        except Exception:
            pass
        return datetime.utcnow()
