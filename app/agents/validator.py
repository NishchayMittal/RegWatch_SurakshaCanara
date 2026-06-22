from app.agents.base import BaseValidatorAgent
from app.db.models import Evidence, MAPItem
from datetime import datetime

class ValidatorAgent(BaseValidatorAgent):
    """
    Validates evidence submitted by departments against the original MAP.
    For Week 2, validation is rule-based (keyword presence check).
    Week 3+ this could be upgraded to an LLM-based evaluator.
    """

    # Minimum required keywords per MAP — a simple placeholder rule.
    # In a real system this would come from the MAP's own requirements,
    # but for Week 2 we just check evidence isn't empty/trivial.
    MIN_DESCRIPTION_LENGTH = 20

    def validate(self, map_id: int, evidence: dict, db) -> dict:
        map_item = db.query(MAPItem).filter(MAPItem.id == map_id).first()

        if not map_item:
            return {"status": "incomplete", "missing_items": ["MAP not found"]}

        missing_items = []

        # Rule 1 — description must be substantive, not just "done"
        description = evidence.get("description", "").strip()
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            missing_items.append("detailed description of action taken")

        # Rule 2 — file/proof must be attached for high-stakes MAPs
        # (Here we treat any MAP as needing proof for simplicity)
        if not evidence.get("file_url"):
            missing_items.append("supporting document/file")

        if missing_items:
            return {"status": "incomplete", "missing_items": missing_items}

        return {"status": "complete", "missing_items": []}