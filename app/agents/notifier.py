from app.agents.base import BaseNotifierAgent
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import atexit

scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

class NotifierAgent(BaseNotifierAgent):
    """
    Real notifier — mocks email/Slack dispatch (prints instead of actually sending),
    and schedules an escalation check after the SLA window expires.
    """

    def dispatch(self, map_item: dict, owner: dict):
        print(f"[EMAIL/SLACK MOCK] To: {owner['department']} | Action required: {map_item['action']}")
        print(f"[EMAIL/SLACK MOCK] Due in {owner['sla_days']} days.")

        run_date = datetime.now() + timedelta(days=owner["sla_days"])
        scheduler.add_job(
            self._escalate,
            "date",
            run_date=run_date,
            args=[map_item, owner],
            id=f"escalation_{map_item.get('id', datetime.now().timestamp())}",
            replace_existing=True
        )

    def _escalate(self, map_item: dict, owner: dict):
        """
        Fires when SLA expires. Now checks actual MAP status in DB first —
        skips escalation if it's already been marked complete.
        """
        from app.db.database import SessionLocal
        from app.db.models import MAPItem

        db = SessionLocal()
        try:
            map_id   = map_item.get("id")
            map_row  = db.query(MAPItem).filter(MAPItem.id == map_id).first() if map_id else None
            status   = map_row.status if map_row else None

            if status == "complete":
                print(f"[ESCALATION SKIPPED] MAP {map_id} already complete for "
                      f"{owner['department']} — no action needed.")
                return

            print(f"[ESCALATION] SLA breached for {owner['department']} — "
                  f"'{map_item['action'][:60]}...' was not completed in time.")

            # Update MAP status to 'overdue' so dashboard can highlight it
            if map_row:
                map_row.status = "overdue"
                db.commit()

        finally:
            db.close()

    def re_escalate(self, map_item: dict, owner: dict, missing_items: list[str]):
        """
        Called by validator_routes when ValidatorAgent returns 'incomplete'.
        Sends a targeted rejection notice with exactly what's missing,
        and schedules a shorter follow-up SLA (half the original).
        """
        department   = owner.get("department", "Unknown")
        action_short = map_item.get("action", "")[:80]
        missing_str  = "\n".join(f"  • {item}" for item in missing_items)

        print(f"\n[REJECTION NOTICE] To: {department}")
        print(f"[REJECTION NOTICE] Your evidence for the following MAP was insufficient:")
        print(f"[REJECTION NOTICE] '{action_short}...'")
        print(f"[REJECTION NOTICE] Missing:\n{missing_str}")

        # Schedule a follow-up escalation at half the original SLA
        original_sla    = owner.get("sla_days", 14)
        followup_days   = max(1, original_sla // 2)
        followup_owner  = {**owner, "sla_days": followup_days}

        print(f"[REJECTION NOTICE] Resubmit within {followup_days} days or this will escalate.\n")

        run_date = datetime.now() + timedelta(days=followup_days)
        scheduler.add_job(
            self._escalate,
            "date",
            run_date=run_date,
            args=[map_item, followup_owner],
            id=f"reescalation_{map_item.get('id', datetime.now().timestamp())}",
            replace_existing=True,
        )