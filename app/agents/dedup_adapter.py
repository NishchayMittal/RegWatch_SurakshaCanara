from app.agents.base import BaseDedupAgent
from app.agents.dedup_real import DedupFilter, DedupStore
from app.agents.watcher_real import CircularDoc
from app.db.models import Circular
from datetime import datetime

# Generic/boilerplate titles that don't actually identify a unique circular —
# RBI/SEBI/MCA site templates often reuse the same <title> tag across many pages.
# Never use these for title-based duplicate matching.
GENERIC_TITLES = {
    "notifications - reserve bank of india",
    "manual fetch",
    "rbi",
    "sebi",
    "mca",
}

class SQLAlchemyDedupStore:
    """
    Implements A's DedupStore protocol using C's existing SQLAlchemy
    Circular model instead of A's assumed url_hash/title_hash columns.
    Since C's Circular model doesn't have those columns yet, we derive
    matches from the existing `url` and `title` fields directly.
    """
    def __init__(self, db):
        self.db = db

    def url_hash_exists(self, url_hash: str) -> bool:
        # C's model stores raw url, not a hash — so we can't match on hash directly.
        # This store is only used transiently inside one request, so it's fine
        # to just check by URL is handled at a higher level (see adapter below).
        return False

    def title_hash_exists(self, title_hash: str) -> bool:
        return False

    def save_hashes(self, url_hash: str, title_hash: str, doc) -> None:
        pass  # no-op — C's orchestrator already saves the Circular row itself


class DedupAgentAdapter(BaseDedupAgent):
    def __init__(self):
        self.filter = DedupFilter(store=None)

    def is_duplicate(self, doc: dict, db) -> bool:
        # Layer 1 — exact URL match (always reliable, primary signal)
        existing = db.query(Circular).filter(Circular.url == doc["url"]).first()
        if existing:
            return True

        # Layer 2 — normalized title match, but SKIP if the title is generic/boilerplate
        normalized_title = self.filter._normalize_title(doc["title"])
        if normalized_title in GENERIC_TITLES:
            return False  # title isn't unique enough to trust — rely on URL match only

        all_circulars = db.query(Circular).all()
        for c in all_circulars:
            c_normalized = self.filter._normalize_title(c.title)
            if c_normalized in GENERIC_TITLES:
                continue  # don't compare against other generic-titled rows either
            if c_normalized == normalized_title:
                return True

        return False