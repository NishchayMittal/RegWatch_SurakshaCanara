from app.agents.base import BaseRouterAgent
from app.db.models import Department, SLA
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../RAG"))
from router_agent import RouterAgent as BRouterAgent

class RouterAgentAdapter(BaseRouterAgent):
    def __init__(self, db=None):
        self.agent = BRouterAgent()
        self.db = db

    def assign(self, map_item: dict) -> dict:
        result = self.agent.route_map_to_dict(map_item["action"])
        sla_days = self._get_sla_days(result["department"], map_item.get("source", "RBI"))
        return {
            "department": result["department"],
            "sla_days": sla_days,
            "confidence": result["confidence_score"],
            "decision": result["decision"],
            "reason": result["reason"],
            "snippet": result["matched_snippet"],
        }

    def _get_sla_days(self, department_name: str, source: str) -> int:
        if not self.db:
            return 7  # fallback if no db session passed
        dept = self.db.query(Department).filter(Department.name == department_name).first()
        if not dept:
            return 7
        sla = self.db.query(SLA).filter(
            SLA.department_id == dept.id,
            SLA.circular_source == source
        ).first()
        return sla.days_to_complete if sla else 7