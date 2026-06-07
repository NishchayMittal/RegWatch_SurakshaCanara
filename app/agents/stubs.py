from app.agents.base import (
    BaseWatcherAgent, BaseDedupAgent,
    BaseMAPExtractor, BaseRouterAgent, BaseNotifierAgent
)
from app.db.models import Circular

class StubWatcherAgent(BaseWatcherAgent):
    def fetch(self, url: str) -> dict:
        print(f"[STUB Watcher] Fetching: {url}")
        return {
            "url": url,
            "title": "Sample RBI Circular",
            "source": "RBI",
            "text": "All banks must submit compliance report by month end."
        }

class StubDedupAgent(BaseDedupAgent):
    def is_duplicate(self, doc: dict, db) -> bool:
        existing = db.query(Circular).filter(Circular.url == doc["url"]).first()
        is_dup = existing is not None
        print(f"[STUB Dedup] {'Duplicate found' if is_dup else 'New circular'}")
        return is_dup

class StubMAPExtractor(BaseMAPExtractor):
    def extract(self, doc: dict) -> dict:
        print("[STUB Extractor] Extracting MAPs...")
        return {
            "maps": [
                {"action": "Submit compliance report by month end", "confidence": 0.91},
                {"action": "Update KYC records for all customers", "confidence": 0.88}
            ],
            "confidence": 0.91
        }

class StubRouterAgent(BaseRouterAgent):
    def assign(self, map_item: dict) -> dict:
        print(f"[STUB Router] Assigning MAP to department...")
        return {
            "department": "Compliance",
            "sla_days": 7
        }

class StubNotifierAgent(BaseNotifierAgent):
    def dispatch(self, map_item: dict, owner: dict):
        print(f"[STUB Notifier] Notifying {owner['department']} — SLA: {owner['sla_days']} days")