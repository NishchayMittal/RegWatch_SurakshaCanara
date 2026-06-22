from app.agents.base import BaseRouterAgent
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../RAG"))
from router_agent import RouterAgent as BRouterAgent

class RouterAgentAdapter(BaseRouterAgent):
    """
    Wraps B's RouterAgent to match C's BaseRouterAgent interface.
    B's route_map_to_dict() returns more data than C's assign() needs,
    so we just extract what the orchestrator uses.
    """
    def __init__(self):
        self.agent = BRouterAgent()

    def assign(self, map_item: dict) -> dict:
        result = self.agent.route_map_to_dict(map_item["action"])
        return {
            "department": result["department"],
            "sla_days": 7,              # will come from SLA table once B's DB is seeded
            "confidence": result["confidence_score"],
            "decision": result["decision"],
            "reason": result["reason"],
            "snippet": result["matched_snippet"],
        }