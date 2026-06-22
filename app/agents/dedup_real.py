"""
Dedup Module — Person A (Week 1: hash-based, Week 3: semantic)

Week 1: Two-layer dedup
  Layer 1 — URL hash (exact duplicate, zero false positives)
  Layer 2 — Normalized title match (same circular, different URL)

Week 3 upgrade: cosine similarity over embeddings (semantic dedup)
  will catch reissued circulars with tweaked titles.

The dedup state is stored in PostgreSQL (circulars table).
This module talks to DB via a thin interface — easy to mock in tests.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

from app.agents.watcher_real import CircularDoc

logger = logging.getLogger(__name__)


# ── DB interface (Protocol = duck typing, easy to mock) ──────────────────────

class DedupStore(Protocol):
    def url_hash_exists(self, url_hash: str) -> bool: ...
    def title_hash_exists(self, title_hash: str) -> bool: ...
    def save_hashes(self, url_hash: str, title_hash: str, doc: CircularDoc) -> None: ...


# ── In-memory store for Week 1 / unit tests ──────────────────────────────────

class InMemoryDedupStore:
    """
    Drop-in store for local testing before DB is ready.
    Person B replaces this with PostgresStore once schema is up.
    """
    def __init__(self):
        self._url_hashes:   set[str] = set()
        self._title_hashes: set[str] = set()

    def url_hash_exists(self, url_hash: str) -> bool:
        return url_hash in self._url_hashes

    def title_hash_exists(self, title_hash: str) -> bool:
        return title_hash in self._title_hashes

    def save_hashes(self, url_hash: str, title_hash: str, doc: CircularDoc) -> None:
        self._url_hashes.add(url_hash)
        self._title_hashes.add(title_hash)


# ── Dedup result ─────────────────────────────────────────────────────────────

@dataclass
class DedupResult:
    is_duplicate: bool
    reason: Optional[str] = None   # "url_hash" | "title_hash" | "semantic" | None


# ── Main Dedup class ─────────────────────────────────────────────────────────

class DedupFilter:
    """
    Usage:
        dedup = DedupFilter(store=InMemoryDedupStore())
        result = dedup.check(doc)
        if result.is_duplicate:
            return  # skip
        dedup.mark_seen(doc)
    """

    def __init__(self, store: DedupStore):
        self.store = store

    # ── Public API ───────────────────────────────────────────────────────────

    def check(self, doc: CircularDoc) -> DedupResult:
        """Check if circular is duplicate. Does NOT mark it seen."""

        # Layer 1: URL hash — fastest, exact match
        if self.store.url_hash_exists(doc.url_hash):
            logger.info(f"Duplicate (url_hash): {doc.title[:60]}")
            return DedupResult(is_duplicate=True, reason="url_hash")

        # Layer 2: Normalized title match
        title_hash = self._title_hash(doc.title)
        if self.store.title_hash_exists(title_hash):
            logger.info(f"Duplicate (title_hash): {doc.title[:60]}")
            return DedupResult(is_duplicate=True, reason="title_hash")

        return DedupResult(is_duplicate=False)

    def mark_seen(self, doc: CircularDoc) -> None:
        """Persist hashes after pipeline successfully processes this doc."""
        title_hash = self._title_hash(doc.title)
        self.store.save_hashes(doc.url_hash, title_hash, doc)
        logger.debug(f"Marked seen: {doc.title[:60]}")

    def filter_batch(self, docs: list[CircularDoc]) -> list[CircularDoc]:
        """
        Filter a batch — also deduplicates within the batch itself
        (two feeds sometimes emit the same circular simultaneously).
        """
        seen_in_batch: set[str] = set()
        unique = []

        for doc in docs:
            # Check within-batch first (no DB hit needed)
            if doc.url_hash in seen_in_batch:
                logger.debug(f"Intra-batch duplicate: {doc.title[:60]}")
                continue

            result = self.check(doc)
            if not result.is_duplicate:
                unique.append(doc)
                seen_in_batch.add(doc.url_hash)

        logger.info(f"Dedup: {len(docs)} in → {len(unique)} unique")
        return unique

    # ── Title normalization ───────────────────────────────────────────────────

    @staticmethod
    def _normalize_title(title: str) -> str:
        """
        Normalize title for matching. Handles:
        - Case differences
        - Extra whitespace
        - Date suffixes (same circular reissued with new date)
        - Circular number prefixes (RBI/2024-25/83 vs RBI/2023-24/83)
        """
        t = title.lower().strip()

        # Remove circular reference numbers (date-year portions change)
        # e.g. "RBI/2024-25/83" → ""
        t = re.sub(r'\brbi/\d{4}-\d{2}/\d+\b', '', t)
        t = re.sub(r'\bsebi/\w+/\d+\b', '', t)

        # Remove standalone dates like "dated January 15, 2024" or "15.01.2024"
        t = re.sub(r'\bdated\s+\w+\s+\d{1,2},?\s+\d{4}\b', '', t)
        t = re.sub(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', '', t)

        # Collapse whitespace
        t = re.sub(r'\s+', ' ', t).strip()

        return t

    @staticmethod
    def _title_hash(title: str) -> str:
        normalized = DedupFilter._normalize_title(title)
        return hashlib.sha256(normalized.encode()).hexdigest()


# ── PostgreSQL store (stub — Person B fills DB connection) ───────────────────

class PostgresDedupStore:
    """
    Real store backed by PostgreSQL circulars table.
    Person B: wire self.conn to your DB connection pool.
    
    Expected table columns used:
        circulars.url_hash   VARCHAR(64)
        circulars.title_hash VARCHAR(64)
    """

    def __init__(self, conn):
        self.conn = conn   # psycopg2 connection or SQLAlchemy session

    def url_hash_exists(self, url_hash: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM circulars WHERE url_hash = %s LIMIT 1",
                (url_hash,)
            )
            return cur.fetchone() is not None

    def title_hash_exists(self, title_hash: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM circulars WHERE title_hash = %s LIMIT 1",
                (title_hash,)
            )
            return cur.fetchone() is not None

    def save_hashes(self, url_hash: str, title_hash: str, doc: CircularDoc) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO circulars (url_hash, title_hash, url, title, regulator, published_at, source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (url_hash) DO NOTHING
                """,
                (url_hash, title_hash, doc.url, doc.title,
                 doc.regulator, doc.published_at, doc.source)
            )
        self.conn.commit()
