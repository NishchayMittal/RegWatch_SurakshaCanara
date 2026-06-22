from app.agents.base import (
    BaseWatcherAgent, BaseDedupAgent,
    BaseMAPExtractor, BaseRouterAgent, BaseNotifierAgent
)
from app.agents.stubs import (
    StubWatcherAgent, StubDedupAgent,
    StubMAPExtractor
)
from app.agents.router_adapter import RouterAgentAdapter
from sqlalchemy.orm import Session
from datetime import datetime
from app.agents.watcher_adapter import WatcherAgentAdapter
from app.agents.dedup_adapter import DedupAgentAdapter
from app.agents.map_extractor import MAPExtractor
from app.agents.notifier import NotifierAgent
from app.db.models import Circular, MAPItem, AuditLog, HumanReviewMap
import json
# remove: from app.agents.stubs import StubNotifierAgent (if no longer needed elsewhere)

class RegWatchPipeline:
    def __init__(
        self,
        db: Session,
        watcher: BaseWatcherAgent = None,
        dedup: BaseDedupAgent = None,
        extractor: BaseMAPExtractor = None,
        router: BaseRouterAgent = None,
        notifier: BaseNotifierAgent = None,
    ):
        self.db = db
        self.watcher = watcher or WatcherAgentAdapter()
        self.dedup = dedup or DedupAgentAdapter()
        self.extractor = extractor or MAPExtractor()
        self.router = router or RouterAgentAdapter(db=self.db)
        self.notifier = notifier or NotifierAgent()
        self.extractor = extractor or MAPExtractor()

    def _log(self, event: str, details: str):
        entry = AuditLog(
            event=event,
            details=details,
            created_at=datetime.utcnow()
        )
        self.db.add(entry)
        self.db.commit()
        print(f"[Audit] {event}: {details}")

    def run(self, circular_url: str):
        print(f"\n{'='*50}")
        print(f"Pipeline started for: {circular_url}")
        print(f"{'='*50}")

        # Step 1 — Fetch
        doc = self.watcher.fetch(circular_url)
        self._log("circular_fetched", f"url={circular_url}")

        # Step 2 — Dedup check
        if self.dedup.is_duplicate(doc, self.db):
            self._log("duplicate_skipped", f"url={circular_url}")
            return {"status": "duplicate", "url": circular_url}

        # Step 3 — Save to DB
        circular = Circular(
            url=doc["url"],
            title=doc["title"],
            source=doc["source"],
            raw_text=doc["text"],
            status="processing"
        )
        self.db.add(circular)
        self.db.commit()
        self.db.refresh(circular)
        self._log("circular_saved", f"id={circular.id}")

        # Step 4 — Extract MAPs
        # Step 4 — Extract MAPs
        try:
            result = self.extractor.extract(doc)
        except Exception as e:
            self._log("extraction_failed", f"error={str(e)}")
            circular.status = "extraction_failed"
            self.db.commit()
            return {"status": "extraction_failed", "error": str(e)}

        self._log("maps_extracted", f"count={len(result['maps'])}, confidence={result['confidence']}")

        # Step 5 — Confidence gate
        if result["confidence"] < 0.85:
            self._log("low_confidence_queued", f"confidence={result['confidence']}")
            review_entry = HumanReviewMap(
                circular_id=circular.id,
                raw_extraction=json.dumps(result),
                confidence=result["confidence"]
            )
            self.db.add(review_entry)
            circular.status = "needs_review"
            self.db.commit()
            return {"status": "needs_review", "confidence": result["confidence"]}

        # Step 6 — Route and notify each MAP
        for map_data in result["maps"]:
            owner = self.router.assign(map_data)

            map_item = MAPItem(
                circular_id=circular.id,
                action=map_data["action"],
                confidence=map_data["confidence"],
                assigned_department=owner["department"],
                sla_days=owner["sla_days"],
                status="pending"
            )
            self.db.add(map_item)
            self.db.commit()
            self._log("map_routed", f"dept={owner['department']}, sla={owner['sla_days']}d")

            self.notifier.dispatch(map_data, owner)
            self._log("notification_sent", f"dept={owner['department']}")

        circular.status = "done"
        self.db.commit()

        print(f"\nPipeline complete for circular id={circular.id}")
        return {
            "status": "success",
            "circular_id": circular.id,
            "maps_count": len(result["maps"])
        }