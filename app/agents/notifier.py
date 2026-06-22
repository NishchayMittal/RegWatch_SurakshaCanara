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
        print(f"[ESCALATION] SLA breached for {owner['department']} — '{map_item['action'][:60]}...' was not completed in time.")
        # In Week 3, this should check the MAP's actual DB status before escalating
        # (if it's already complete, skip the escalation)