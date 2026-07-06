from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Circular, MAPItem, Evidence, AuditLog, HumanReviewMap, Task, Department
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
    return [{"id": c.id, "url": c.url, "title": c.title, "status": c.status, "raw_text": c.raw_text} for c in circulars]

@router.get("/circulars/{circular_id}/maps")
def get_maps(circular_id: int, db: Session = Depends(get_db)):
    maps = db.query(MAPItem).filter(MAPItem.circular_id == circular_id).all()
    return [{"id": m.id, "action": m.action, "department": m.assigned_department, "status": m.status, "confidence": m.confidence, "created_at": m.created_at, "sla_days": m.sla_days} for m in maps]

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
        created_at=datetime.now()
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
        created_at=datetime.now()
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

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_circulars = db.query(Circular).count()
    pending_maps = db.query(MAPItem).filter(MAPItem.status != "complete").count()
    complete_maps = db.query(MAPItem).filter(MAPItem.status == "complete").count()
    needs_review = db.query(HumanReviewMap).filter(HumanReviewMap.status == "pending").count()
    return {
        "total_circulars": total_circulars,
        "pending_maps": pending_maps,
        "complete_maps": complete_maps,
        "needs_review": needs_review
    }

@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()
    return [
        {
            "id": l.id,
            "event": l.event,
            "details": l.details,
            "created_at": l.created_at
        }
        for l in logs
    ]

@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    depts = db.query(Department).all()
    return [{"id": d.id, "name": d.name} for d in depts]

class RouteTaskRequest(BaseModel):
    review_id: int
    action_text: str
    department_name: str
    sla_days: int

@router.post("/tasks/route")
def route_human_review_task(req: RouteTaskRequest, db: Session = Depends(get_db)):
    from datetime import timedelta
    
    # 1. Fetch the pending review circular map
    hr_map = db.query(HumanReviewMap).filter(HumanReviewMap.id == req.review_id).first()
    if not hr_map:
        return {"error": "HumanReviewMap item not found"}
        
    # 2. Fetch the department record
    dept_rec = db.query(Department).filter(Department.name == req.department_name).first()
    dept_id = dept_rec.id if dept_rec else None
    
    # 3. Create the concrete MAPItem
    map_item = MAPItem(
        circular_id=hr_map.circular_id,
        action=req.action_text,
        assigned_department=req.department_name,
        sla_days=req.sla_days,
        status="pending",
        confidence=0.95,
        created_at=datetime.now()
    )
    db.add(map_item)
    db.flush()
    
    # 4. Create the assigned department Task
    due_date = datetime.now() + timedelta(days=req.sla_days)
    task_item = Task(
        map_id=map_item.id,
        department_id=dept_id,
        status="pending",
        due_at=due_date,
        assigned_at=datetime.now()
    )
    db.add(task_item)
    
    # 5. Mark human review map as approved
    hr_map.status = "approved"
    
    # 6. Mark circular as done
    circular = db.query(Circular).filter(Circular.id == hr_map.circular_id).first()
    if circular:
        circular.status = "done"
        
    # 7. Audit log creation
    audit = AuditLog(
        event="human_review_approved",
        details=f"Human approved MAP {map_item.id} for Circular {circular.id if circular else hr_map.circular_id}.",
        created_at=datetime.now()
    )
    db.add(audit)
    db.commit()
    
    return {"status": "ok", "map_id": map_item.id, "task_id": task_item.id}

@router.delete("/maps/{map_id}")
def delete_map(map_id: int, db: Session = Depends(get_db)):
    from app.db.models import HumanReviewQueue
    map_item = db.query(MAPItem).filter(MAPItem.id == map_id).first()
    if not map_item:
        return {"error": "MAP item not found", "ok": False}
        
    # Delete related tasks
    db.query(Task).filter(Task.map_id == map_id).delete()
    
    # Delete related evidence
    db.query(Evidence).filter(Evidence.map_id == map_id).delete()
    
    # Delete related human review queue items if any
    db.query(HumanReviewQueue).filter(HumanReviewQueue.map_id == map_id).delete()
    
    # Delete map item itself
    db.delete(map_item)
    
    # Add audit log
    audit = AuditLog(
        event="MAP_DELETED",
        details=f"MAP {map_id} deleted manually from dashboard.",
        created_at=datetime.now()
    )
    db.add(audit)
    db.commit()
    
    return {"status": "ok", "ok": True}