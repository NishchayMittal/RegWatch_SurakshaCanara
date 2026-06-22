from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Circular, MAPItem, Evidence, AuditLog, HumanReviewMap
from app.core.orchestrator import RegWatchPipeline
from app.agents.validator import ValidatorAgent
from app.agents.stubs import StubNotifierAgent  # already used elsewhere
from datetime import datetime
from app.agents.notifier import NotifierAgent

validator = ValidatorAgent()

router = APIRouter()

@router.get("/review/maps")
def list_pending_map_reviews(db: Session = Depends(get_db)):
    items = db.query(HumanReviewMap).filter(HumanReviewMap.status == "pending").all()
    return [{"id": i.id, "circular_id": i.circular_id, "raw_extraction": i.raw_extraction, "confidence": i.confidence} for i in items]

@router.post("/review/maps/{review_id}/approve")
def approve_map_review(review_id: int, db: Session = Depends(get_db)):
    item = db.query(HumanReviewMap).filter(HumanReviewMap.id == review_id).first()
    if not item:
        return {"error": "not found"}
    item.status = "approved"
    db.commit()
    return {"status": "approved", "id": review_id}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/pipeline/run")
def run_pipeline(url: str, db: Session = Depends(get_db)):
    pipeline = RegWatchPipeline(db=db)
    result = pipeline.run(url)
    return result

@router.get("/circulars")
def list_circulars(db: Session = Depends(get_db)):
    circulars = db.query(Circular).all()
    return [{"id": c.id, "url": c.url, "title": c.title, "status": c.status} for c in circulars]

@router.get("/circulars/{circular_id}/maps")
def get_maps(circular_id: int, db: Session = Depends(get_db)):
    maps = db.query(MAPItem).filter(MAPItem.circular_id == circular_id).all()
    return [{"id": m.id, "action": m.action, "department": m.assigned_department, "status": m.status} for m in maps]

@router.get("/queue/human-review")
def human_review_queue(db: Session = Depends(get_db)):
    items = db.query(MAPItem).filter(MAPItem.confidence < 0.85).all()
    return items

@router.post("/maps/{map_id}/evidence")
def submit_evidence(map_id: int, description: str, file_url: str = None, submitted_by: str = "unknown", db: Session = Depends(get_db)):
    """
    Department submits evidence for a MAP.
    Validator checks it, updates status, and re-escalates only missing pieces.
    """
    # Step 1 — Save the evidence submission
    evidence_record = Evidence(
        map_id=map_id,
        description=description,
        file_url=file_url,
        submitted_by=submitted_by,
        status="submitted",
        created_at=datetime.utcnow()
    )
    db.add(evidence_record)
    db.commit()
    db.refresh(evidence_record)

    # Step 2 — Validate
    result = validator.validate(map_id, {"description": description, "file_url": file_url}, db)

    # Step 3 — Update evidence + MAP status based on validation result
    map_item = db.query(MAPItem).filter(MAPItem.id == map_id).first()

    if result["status"] == "complete":
        evidence_record.status = "accepted"
        map_item.status = "complete"
        db.commit()
        response = {
            "evidence_id": evidence_record.id,
            "status": "complete",
            "message": "Evidence accepted. MAP marked complete."
        }
    else:
        evidence_record.status = "incomplete"
        evidence_record.missing_items = ", ".join(result["missing_items"])
        map_item.status = "evidence_incomplete"
        db.commit()

        # Step 4 — Partial re-escalation: only missing items go back to Notifier
        notifier = NotifierAgent()
        notifier.dispatch(
            {"action": f"Missing items for MAP {map_id}: {', '.join(result['missing_items'])}"},
            {"department": map_item.assigned_department, "sla_days": 2}
        )

        response = {
            "evidence_id": evidence_record.id,
            "status": "incomplete",
            "missing_items": result["missing_items"],
            "message": "Evidence incomplete. Missing items re-escalated to department."
        }

    # Step 5 — Audit log (runs for BOTH complete and incomplete cases)
    audit_entry = AuditLog(
        event="evidence_submitted",
        details=f"map_id={map_id}, status={result['status']}, submitted_by={submitted_by}",
        created_at=datetime.utcnow()
    )
    db.add(audit_entry)
    db.commit()

    return response


@router.get("/maps/{map_id}/evidence")
def get_evidence_history(map_id: int, db: Session = Depends(get_db)):
    """View all evidence submissions for a given MAP — useful for audit trail."""
    records = db.query(Evidence).filter(Evidence.map_id == map_id).all()
    return [
        {
            "id": e.id,
            "description": e.description,
            "status": e.status,
            "missing_items": e.missing_items,
            "submitted_by": e.submitted_by,
            "created_at": e.created_at
        }
        for e in records
    ]