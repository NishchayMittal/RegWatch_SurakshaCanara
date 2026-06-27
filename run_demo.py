"""
run_demo.py — RegWatch Pipeline Demo (SQLAlchemy & Validator Flow Integration)
=============================================================================
Run:
    python run_demo.py
Then:
    streamlit run dashboard.py
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

# Prevent UnicodeEncodeError on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from sqlalchemy import func, desc

# Import SQLAlchemy database dependencies
from app.db.database import engine, SessionLocal, Base
from app.db.seed_data import seed
from app.db.models import Circular, MAPItem, Task, AuditLog, Department, Evidence, HumanReviewMap

# Import real agents
from app.agents.watcher_real import WatcherAgent, CircularDoc
from app.agents.dedup_real import DedupFilter, InMemoryDedupStore
from app.agents.map_extractor import MAPExtractor
from app.agents.router_adapter import RouterAgentAdapter as RouterAgent
from app.agents.notifier import NotifierAgent
from app.agents.validator import ValidatorAgent

# ── colour helpers ────────────────────────────────────────────────────────────
RESET  = "\033[0m"; BOLD = "\033[1m"; GREEN  = "\033[92m"
YELLOW = "\033[93m"; RED  = "\033[91m"; CYAN  = "\033[96m"
BLUE   = "\033[94m"; DIM  = "\033[2m"

def banner(text, colour=CYAN):
    w = 72
    print(f"\n{colour}{BOLD}{'═'*w}{RESET}")
    print(f"{colour}{BOLD}  {text}{RESET}")
    print(f"{colour}{BOLD}{'═'*w}{RESET}")

def step(n, text): print(f"\n{BLUE}{BOLD}[{n}]{RESET} {BOLD}{text}{RESET}")
def ok(text):      print(f"  {GREEN}✔{RESET}  {text}")
def warn(text):    print(f"  {YELLOW}⚠{RESET}  {text}")
def info(text):    print(f"  {DIM}→{RESET}  {text}")

def slack_notify(dept, circular_id, map_text, sla_days):
    ts = datetime.now().strftime("%H:%M")
    print(f"""
  {CYAN}┌─────────────────────────────────────────────────────┐{RESET}
  {CYAN}│{RESET} {BOLD}🔔  RegWatch Compliance Alert{RESET}  {DIM}[{ts}]{RESET}
  {CYAN}│{RESET}  Department : {BOLD}{dept}{RESET}
  {CYAN}│{RESET}  Circular   : {circular_id[:60]}
  {CYAN}│{RESET}  Action     : {map_text[:70]}{'…' if len(map_text) > 70 else ''}
  {CYAN}│{RESET}  SLA        : {YELLOW}{sla_days} days{RESET}
  {CYAN}└─────────────────────────────────────────────────────┘{RESET}""")

# ── 13 mock circulars (12 standard + 1 low-confidence for Human Review) ───────
MOCK_CIRCULARS = [
    {"url": "https://rbi.org.in/mock/001", "regulator": "RBI",
     "title": "Guidelines on Digital Lending – KYC Norms",
     "raw_text": "Banks shall complete KYC verification within 7 days of account opening. Institutions must implement digital lending frameworks by Q3 2024. All lenders are mandated to submit compliance reports quarterly. Banks shall maintain audit trails for all digital transactions for a minimum of 5 years."},
    {"url": "https://rbi.org.in/mock/002", "regulator": "RBI",
     "title": "Prudential Norms for Asset Classification",
     "raw_text": "Banks must classify non-performing assets within 90 days of default. Institutions shall provision at least 15% for sub-standard assets. Lenders are mandated to disclose restructured accounts in quarterly reports. All banks shall submit NPA data to the central repository by the 10th of each month."},
    {"url": "https://sebi.gov.in/mock/001", "regulator": "SEBI",
     "title": "Insider Trading – Code of Conduct Circular",
     "raw_text": "Listed companies must maintain an insider trading policy accessible to all employees. Compliance officers shall monitor trading windows and report violations within 48 hours. Companies are mandated to file disclosures with SEBI within 2 business days of a transaction."},
    {"url": "https://sebi.gov.in/mock/002", "regulator": "SEBI",
     "title": "Mutual Fund Expense Ratio – Revised Framework",
     "raw_text": "Asset management companies shall cap total expense ratio at 1.05% for equity schemes. AMCs must disclose expense ratio changes on their website within 24 hours. Distributors are mandated to display commission structures transparently to investors."},
    {"url": "https://mca.gov.in/mock/001", "regulator": "MCA",
     "title": "Annual Return Filing – Companies Act Amendment",
     "raw_text": "All companies shall file annual returns within 60 days of the AGM. Defaulting companies must pay an additional fee of Rs 100 per day of delay. Directors are mandated to certify financial statements before submission."},
    {"url": "https://mca.gov.in/mock/002", "regulator": "MCA",
     "title": "CSR Expenditure Reporting Requirements",
     "raw_text": "Companies with net profit above Rs 5 crore must spend 2% on CSR activities. Boards shall constitute a CSR committee with at least one independent director. Unspent CSR funds must be transferred to the PM National Relief Fund within 6 months."},
    {"url": "https://rbi.org.in/mock/003", "regulator": "RBI",
     "title": "Cybersecurity Framework for Banks",
     "raw_text": "Banks shall implement a Board-approved cybersecurity policy by December 2024. Institutions must conduct penetration testing at least twice a year. All banks are mandated to report cybersecurity incidents to RBI within 6 hours of detection."},
    {"url": "https://sebi.gov.in/mock/003", "regulator": "SEBI",
     "title": "Corporate Governance – Board Composition",
     "raw_text": "Listed entities shall have at least one-third of the board as independent directors. Companies must conduct Board evaluations annually and disclose results in annual reports. Audit committees are mandated to meet at least four times a year."},
    {"url": "https://rbi.org.in/mock/004", "regulator": "RBI",
     "title": "Priority Sector Lending – Updated Targets",
     "raw_text": "Commercial banks shall achieve 40% of adjusted net bank credit as priority sector lending. Banks must allocate 18% of ANBC to agriculture by year-end. Institutions are mandated to report PSL shortfalls to NABARD by the 15th of the following month."},
    {"url": "https://mca.gov.in/mock/003", "regulator": "MCA",
     "title": "Mergers and Acquisitions – Disclosure Norms",
     "raw_text": "Acquiring companies must disclose M&A transactions to MCA within 30 days of completion. Boards shall obtain fairness opinions from independent valuers before approval. Companies are mandated to file Form FC-GPR within 30 days of allotting shares to foreign investors."},
    {"url": "https://sebi.gov.in/mock/004", "regulator": "SEBI",
     "title": "ESG Disclosures – Business Responsibility Report",
     "raw_text": "Top 1000 listed companies by market cap shall submit Business Responsibility and Sustainability Reports. Companies must disclose Scope 1 and Scope 2 carbon emissions from FY 2024-25. Boards are mandated to define ESG targets and report progress annually."},
    {"url": "https://rbi.org.in/mock/005", "regulator": "RBI",
     "title": "Liquidity Coverage Ratio – Basel III Compliance",
     "raw_text": "Banks shall maintain a Liquidity Coverage Ratio of at least 100% at all times. Institutions must submit daily LCR reports to RBI through the XBRL portal. Banks are mandated to conduct monthly liquidity stress tests and submit results to the Board."},
    # Low-Confidence Circular (designed to trigger overall confidence < 0.85 and hit the human review queue)
    {"url": "https://rbi.org.in/mock/006", "regulator": "RBI",
     "title": "Advisory on Credit Information Sharing",
     "raw_text": "Banks are advised to verify credit history of borrowers before extending large commercial loans. Regulated entities are directed to ensure that credit information is shared securely with credit info companies."}
]

def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()
    ok("Database reset and seeded via SQLAlchemy models successfully.")

def seed_data_directory():
    """Write mock circulars as JSON files for WatcherAgent to read."""
    data_dir = Path("data/circulars")
    data_dir.mkdir(parents=True, exist_ok=True)
    for f in data_dir.glob("demo_*.json"):
        f.unlink()
    for i, circ in enumerate(MOCK_CIRCULARS, 1):
        (data_dir / f"demo_{i:02d}.json").write_text(
            json.dumps(circ, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    ok(f"Wrote {len(MOCK_CIRCULARS)} JSON files → data/circulars/")

# ── Return-type normalisers ───────────────────────────────────────────────────

def extract_maps(agent, text: str) -> list[dict]:
    # MAPExtractor.extract() expects {"text": "..."}
    result = agent.extract({"text": text})

    if result is None:
        return []

    if isinstance(result, dict):
        # We also want to know overall confidence
        maps_list = result.get("maps", [])
        overall_confidence = result.get("confidence", 0.0)
        return maps_list, overall_confidence

    return [], 0.0

def router_route(agent, map_text: str, source: str) -> tuple[str, int]:
    # RouterAgentAdapter.assign() expects {"action": "...", "source": regulator}
    result = agent.assign({"action": map_text, "source": source})
    return str(result.get("department", "Compliance & Legal")), int(result.get("sla_days", 14))

def notifier_dispatch(agent, circular_url, dept, map_text, sla_days):
    map_item = {"action": map_text, "id": circular_url}
    owner    = {"department": dept, "sla_days": sla_days}
    agent.dispatch(map_item, owner)
    slack_notify(dept, circular_url, map_text, sla_days)

# ── Audit Log Writer ──────────────────────────────────────────────────────────
def log_audit_event(db, event, details=""):
    log = AuditLog(
        event=event,
        details=details,
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()

# ── Main Pipeline Runner ──────────────────────────────────────────────────────

def run_pipeline(db):
    watcher   = WatcherAgent()
    dedup     = DedupFilter(store=InMemoryDedupStore())
    extractor = MAPExtractor()
    router    = RouterAgent(db=db)
    notifier  = NotifierAgent()

    info("WatcherAgent.fetch_all(use_local_only=True)…")
    docs = watcher.fetch_all(use_local_only=True)  # list[CircularDoc]

    if not docs:
        print(f"\n  {RED}✘  WatcherAgent returned 0 docs. Check data/circulars/ exists.{RESET}")
        sys.exit(1)

    ok(f"Watcher returned {len(docs)} CircularDoc(s)")

    total_maps = total_tasks = dupes = human_reviews = 0
    results = []

    print()
    for i, doc in enumerate(docs, 1):
        print(f"\n{BOLD}  ── Circular {i:02d}/{len(docs)} ─────────────────────────{RESET}")
        info(f"[{doc.regulator}] {doc.title}")

        # ── Dedup check ───────────────────────────────────────────────────────
        dedup_result = dedup.check(doc)
        if dedup_result.is_duplicate:
            warn(f"Duplicate ({dedup_result.reason}) — skipping.")
            dupes += 1
            log_audit_event(db, "DUPLICATE_SKIPPED", doc.url)
            continue

        # ── Persist Circular (status=processing initially) ────────────────────
        circular = Circular(
            url=doc.url,
            title=doc.title,
            source=doc.regulator,
            raw_text=doc.raw_text,
            status="processing",
            created_at=datetime.utcnow()
        )
        db.add(circular)
        db.commit()
        db.refresh(circular)
        
        dedup.mark_seen(doc)
        log_audit_event(db, "CIRCULAR_INGESTED", doc.url)

        # ── Extract MAPs and overall confidence ───────────────────────────────
        maps, overall_confidence = extract_maps(extractor, doc.raw_text)
        if not maps:
            warn("No MAPs extracted.")
            circular.status = "done"
            db.commit()
            log_audit_event(db, "NO_MAPS", doc.url)
            continue

        # ── Confidence Gate (< 0.85 triggers Human Review Queue) ──────────────
        if overall_confidence < 0.85:
            warn(f"Low overall confidence ({overall_confidence:.2f} < 0.85) — routing to human review queue.")
            review_entry = HumanReviewMap(
                circular_id=circular.id,
                raw_extraction=json.dumps({"maps": maps, "confidence": overall_confidence}),
                confidence=overall_confidence,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(review_entry)
            circular.status = "needs_review"
            db.commit()
            human_reviews += 1
            log_audit_event(db, "LOW_CONFIDENCE_QUEUED", f"circular_id={circular.id}, confidence={overall_confidence}")
            continue

        ok(f"Extracted {len(maps)} MAP(s) with confidence {overall_confidence:.2f}")
        total_maps += len(maps)

        # ── Route + Notify ────────────────────────────────────────────────────
        for m in maps:
            dept, sla = router_route(router, m["action"], doc.regulator)
            
            # Create MAPItem
            map_item = MAPItem(
                circular_id=circular.id,
                action=m["action"],
                confidence=m["confidence"],
                assigned_department=dept,
                sla_days=sla,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(map_item)
            db.commit()
            db.refresh(map_item)

            # Create Task
            dept_row = db.query(Department).filter(Department.name == dept).first()
            dept_id = dept_row.id if dept_row else None
            due_date = datetime.utcnow() + timedelta(days=sla)
            
            task = Task(
                map_id=map_item.id,
                department_id=dept_id,
                assigned_at=datetime.utcnow(),
                due_at=due_date,
                status="assigned",
                notes=""
            )
            db.add(task)
            db.commit()
            
            total_tasks += 1
            notifier_dispatch(notifier, doc.url, dept, m["action"], sla)
            time.sleep(0.05)

        # Set status = done
        circular.status = "done"
        db.commit()

        results.append({"url": doc.url, "regulator": doc.regulator, "maps": len(maps)})
        log_audit_event(db, "CIRCULAR_PROCESSED", f"{doc.url} → {len(maps)} MAPs")
        time.sleep(0.1)

    return total_maps, total_tasks, dupes, human_reviews, results


# ── Validator Flow Simulation ─────────────────────────────────────────────────

def run_validator_simulation(db):
    banner("SIMULATING CLOSED-LOOP VALIDATOR FLOW", YELLOW)
    validator = ValidatorAgent()
    notifier = NotifierAgent()

    # Query created MAPItems that are currently pending
    pending_maps = db.query(MAPItem).filter(MAPItem.status == "pending").all()
    if not pending_maps:
        warn("No pending maps available for validation simulation.")
        return

    info(f"Found {len(pending_maps)} pending compliance tasks. Simulating submissions...")

    # Case 1: Submit VALID evidence for 6 tasks
    valid_count = 0
    for map_item in pending_maps[:6]:
        description = (
            f"Implemented full compliance frameworks for MAP {map_item.id}. "
            f"Department has appointed supervisors, updated corporate policies, "
            f"and established audit schedules as requested by the regulator circular."
        )
        file_url = f"https://internal.bank/compliance/docs/audit_proof_map_{map_item.id}.pdf"
        submitted_by = map_item.assigned_department

        info(f"Submitting VALID evidence for MAP {map_item.id} ({map_item.assigned_department})...")
        
        # Save evidence record (analogous to routes.py submit_evidence)
        evidence = Evidence(
            map_id=map_item.id,
            description=description,
            file_url=file_url,
            submitted_by=submitted_by,
            status="submitted",
            created_at=datetime.utcnow()
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        # Validate
        res = validator.validate(map_item.id, {"description": description, "file_url": file_url}, db)
        if res["status"] == "complete":
            evidence.status = "accepted"
            map_item.status = "complete"
            db.commit()
            ok(f"  ✔ Evidence ACCEPTED. MAP {map_item.id} status set to COMPLETE.")
            log_audit_event(db, "evidence_submitted", f"map_id={map_item.id}, status=complete, submitted_by={submitted_by}")
            valid_count += 1
        else:
            warn(f"  ✘ Unexpected rejection: {res['missing_items']}")

    # Case 2: Submit INCOMPLETE evidence (description too short) for 2 tasks
    for map_item in pending_maps[6:8]:
        description = "Done." # too short
        file_url = "https://internal.bank/compliance/proof.pdf"
        submitted_by = map_item.assigned_department

        info(f"Submitting INVALID evidence (too short) for MAP {map_item.id} ({map_item.assigned_department})...")
        
        evidence = Evidence(
            map_id=map_item.id,
            description=description,
            file_url=file_url,
            submitted_by=submitted_by,
            status="submitted",
            created_at=datetime.utcnow()
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        res = validator.validate(map_item.id, {"description": description, "file_url": file_url}, db)
        evidence.status = "incomplete"
        evidence.missing_items = ", ".join(res["missing_items"])
        map_item.status = "evidence_incomplete"
        db.commit()

        warn(f"  ✘ Evidence REJECTED. Missing: {res['missing_items']}")
        
        # Escalation
        notifier.re_escalate(
            {"id": map_item.id, "action": map_item.action},
            {"department": map_item.assigned_department, "sla_days": map_item.sla_days},
            res["missing_items"]
        )
        log_audit_event(db, "evidence_submitted", f"map_id={map_item.id}, status=incomplete, submitted_by={submitted_by}")

    # Case 3: Submit INCOMPLETE evidence (missing file URL) for 2 tasks
    for map_item in pending_maps[8:10]:
        description = "Cybersecurity penetration tests conducted. Compliance signed off by CIO."
        file_url = None # missing file
        submitted_by = map_item.assigned_department

        info(f"Submitting INVALID evidence (missing file) for MAP {map_item.id} ({map_item.assigned_department})...")
        
        evidence = Evidence(
            map_id=map_item.id,
            description=description,
            file_url=file_url,
            submitted_by=submitted_by,
            status="submitted",
            created_at=datetime.utcnow()
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        res = validator.validate(map_item.id, {"description": description, "file_url": file_url}, db)
        evidence.status = "incomplete"
        evidence.missing_items = ", ".join(res["missing_items"])
        map_item.status = "evidence_incomplete"
        db.commit()

        warn(f"  ✘ Evidence REJECTED. Missing: {res['missing_items']}")
        
        # Escalation
        notifier.re_escalate(
            {"id": map_item.id, "action": map_item.action},
            {"department": map_item.assigned_department, "sla_days": map_item.sla_days},
            res["missing_items"]
        )
        log_audit_event(db, "evidence_submitted", f"map_id={map_item.id}, status=incomplete, submitted_by={submitted_by}")

    # Case 4: Simulate a correction (resubmit good evidence for one rejected task)
    corrected_map = pending_maps[6] # was rejected in case 2
    info(f"Simulating CORRECTION: Resubmitting VALID evidence for previously rejected MAP {corrected_map.id}...")
    good_description = "Updated description with details. All internal systems have been successfully audit-tested."
    good_file_url = "https://internal.bank/compliance/docs/audit_proof_map_corrected.pdf"
    
    evidence = Evidence(
        map_id=corrected_map.id,
        description=good_description,
        file_url=good_file_url,
        submitted_by=corrected_map.assigned_department,
        status="submitted",
        created_at=datetime.utcnow()
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    res = validator.validate(corrected_map.id, {"description": good_description, "file_url": good_file_url}, db)
    if res["status"] == "complete":
        evidence.status = "accepted"
        corrected_map.status = "complete"
        db.commit()
        ok(f"  ✔ Correction ACCEPTED. MAP {corrected_map.id} status set to COMPLETE.")
        log_audit_event(db, "evidence_submitted", f"map_id={corrected_map.id}, status=complete, submitted_by={corrected_map.assigned_department}")


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(db, total_maps, total_tasks, dupes, human_reviews, results):
    banner("PIPELINE SUMMARY", GREEN)
    print(f"\n  {'Circulars processed':<30} {GREEN}{len(results)}{RESET}")
    print(f"  {'MAPs extracted':<30} {GREEN}{total_maps}{RESET}")
    print(f"  {'Tasks assigned':<30} {GREEN}{total_tasks}{RESET}")
    print(f"  {'Duplicates skipped':<30} {YELLOW}{dupes}{RESET}")
    print(f"  {'Human Review Queued':<30} {RED}{human_reviews}{RESET}")

    rows = db.query(MAPItem.assigned_department, func.count(MAPItem.id).label("cnt"))\
             .group_by(MAPItem.assigned_department)\
             .order_by(desc("cnt")).all()
    if rows:
        print(f"\n  {BOLD}Department Workload (Active MAPs):{RESET}")
        for dept, cnt in rows:
            bar = "█" * min(cnt * 2, 30)
            print(f"  {dept:<35} {CYAN}{bar}{RESET} {cnt}")

    src_rows = db.query(Circular.source, func.count(MAPItem.id))\
                 .join(Circular, MAPItem.circular_id == Circular.id)\
                 .group_by(Circular.source).all()
    if src_rows:
        print(f"\n  {BOLD}Tasks by Regulator:{RESET}")
        for src, cnt in src_rows:
            print(f"  {src:<10} {cnt} tasks")

    # Display evidence validation status
    completed_maps = db.query(func.count(MAPItem.id)).filter(MAPItem.status == "complete").scalar()
    incomplete_maps = db.query(func.count(MAPItem.id)).filter(MAPItem.status == "evidence_incomplete").scalar()
    print(f"\n  {BOLD}Validator Statistics:{RESET}")
    print(f"  {'Completed (Validated)':<30} {GREEN}{completed_maps}{RESET}")
    print(f"  {'Evidence Incomplete (Rejected)':<30} {RED}{incomplete_maps}{RESET}")

    print(f"\n  {DIM}DB Path: {os.path.abspath('regwatch.db')}{RESET}")
    print(f"\n  {GREEN}{BOLD}Next step → streamlit run dashboard.py{RESET}\n")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    banner("RegWatch — Automated Regulatory Compliance Pipeline")

    step(1, "Resetting SQLite database via SQLAlchemy models")
    reset_database()

    step(2, "Seeding data/circulars/ with 13 mock JSON files (incl. 1 low-confidence)")
    seed_data_directory()

    db = SessionLocal()
    try:
        step(3, "Running pipeline")
        t0 = time.time()
        total_maps, total_tasks, dupes, human_reviews, results = run_pipeline(db)
        print(f"\n  {DIM}Pipeline completed in {time.time() - t0:.1f}s{RESET}")

        step(4, "Simulating evidence validation workflow")
        run_validator_simulation(db)

        step(5, "Summary")
        print_summary(db, total_maps, total_tasks, dupes, human_reviews, results)
    finally:
        db.close()


if __name__ == "__main__":
    main()