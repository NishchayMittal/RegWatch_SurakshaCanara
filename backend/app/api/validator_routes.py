"""
validator_routes.py — Piece 3: FastAPI Routes for Validator Flow
=================================================================
Place at: app/api/validator_routes.py

Wire into main.py:
    from app.api.validator_routes import router as validator_router
    app.include_router(validator_router, prefix="/api/v1", tags=["validator"])

Uses SQLAlchemy session via Depends(get_db) — same pattern as the rest of the app.
Uses Person A's ValidatorAgent.validate(map_id, evidence_dict, db) directly.

Endpoints:
    GET  /api/v1/maps/pending              → MAPs assigned but not yet actioned
    GET  /api/v1/maps/{map_id}/status      → single MAP + its evidence history
    POST /api/v1/maps/{map_id}/submit      → department submits evidence
    POST /api/v1/maps/{map_id}/validate    → run ValidatorAgent on submitted evidence
    POST /api/v1/maps/validate-all         → batch validate all submitted evidence
    GET  /api/v1/validator/log             → audit trail
    GET  /api/v1/validator/stats           → dashboard summary counts
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.db.models import MAPItem, Evidence, Task, AuditLog, Circular
from app.agents.validator import ValidatorAgent
from app.agents.notifier import NotifierAgent

notifier = NotifierAgent()

router = APIRouter()
agent  = ValidatorAgent()   # stateless — safe to share


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class EvidenceSubmission(BaseModel):
    description: str = Field(
        ...,
        min_length=20,
        description="What was done to fulfil this MAP obligation.",
        example="CISO appointed on 1 Oct 2024. Board-approved cybersecurity "
                "policy implemented and signed off on 5 Oct 2024.",
    )
    file_url: Optional[str] = Field(
        default=None,
        description="URL/path to supporting document (optional but recommended).",
        example="https://internal.bank/docs/ciso-appointment-letter.pdf",
    )
    submitted_by: str = Field(
        default="Department",
        description="Name of the person or team submitting.",
        example="IT & Cybersecurity",
    )


class SubmitResponse(BaseModel):
    ok:          bool
    message:     str
    evidence_id: Optional[int] = None
    map_id:      Optional[int] = None
    missing_items: list[str]   = []


class ValidationResponse(BaseModel):
    map_id:        int
    evidence_id:   int
    decision:      str          # "complete" | "incomplete"
    missing_items: list[str]
    decided_at:    str


class MAPStatus(BaseModel):
    map_id:              int
    action:              str
    assigned_department: Optional[str]
    sla_days:            Optional[int]
    status:              str
    circular_title:      Optional[str]
    evidence_count:      int
    latest_evidence_status: Optional[str]


class ValidatorStats(BaseModel):
    total_maps:  int
    pending:     int
    submitted:   int
    complete:    int
    incomplete:  int
    approval_rate: float


# ── GET /maps/pending ─────────────────────────────────────────────────────────

@router.get(
    "/maps/pending",
    response_model=list[MAPStatus],
    summary="All MAPs that are assigned but not yet completed",
)
def list_pending_maps(db: Session = Depends(get_db)):
    maps = (
        db.query(MAPItem)
        .filter(MAPItem.status.in_(["pending", "assigned"]))
        .order_by(MAPItem.created_at.asc())
        .all()
    )
    return [_map_to_status(m, db) for m in maps]


# ── GET /maps/{map_id}/status ─────────────────────────────────────────────────

@router.get(
    "/maps/{map_id}/status",
    response_model=MAPStatus,
    summary="Status of a single MAP and its evidence history",
)
def get_map_status(
    map_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    m = db.query(MAPItem).filter(MAPItem.id == map_id).first()
    if not m:
        raise HTTPException(404, f"MAP {map_id} not found.")
    return _map_to_status(m, db)


# ── POST /maps/{map_id}/submit ────────────────────────────────────────────────

@router.post(
    "/maps/{map_id}/submit",
    response_model=SubmitResponse,
    summary="Department submits evidence for a MAP",
    description=(
        "Creates an Evidence row linked to the MAP. "
        "Moves MAPItem.status → 'submitted'. "
        "Returns missing_items if the submission is already flagged incomplete "
        "(e.g. no file_url) so the department knows what to add."
    ),
)
def submit_evidence(
    map_id: int = Path(..., gt=0),
    body: EvidenceSubmission = Body(...),
    db: Session = Depends(get_db),
):
    m = db.query(MAPItem).filter(MAPItem.id == map_id).first()
    if not m:
        raise HTTPException(404, f"MAP {map_id} not found.")

    if m.status == "complete":
        raise HTTPException(400, "MAP already marked complete. No further action needed.")

    # Create evidence row
    evidence = Evidence(
        map_id=map_id,
        description=body.description,
        file_url=body.file_url,
        submitted_by=body.submitted_by,
        status="submitted",
        created_at=datetime.utcnow(),
    )
    db.add(evidence)

    # Move MAP to submitted
    m.status = "submitted"

    # Run a quick pre-check so the department gets immediate feedback
    evidence_dict = {"description": body.description, "file_url": body.file_url}
    pre_check     = agent.validate(map_id, evidence_dict, db)
    missing       = pre_check.get("missing_items", [])

    if missing:
        evidence.status        = "incomplete"
        evidence.missing_items = ", ".join(missing)
        m.status               = "incomplete"
        message = "Evidence received but flagged incomplete — see missing_items."
    else:
        message = f"Evidence accepted for MAP {map_id}. Pending final validation."

    db.commit()
    db.refresh(evidence)

    _audit(db, "EVIDENCE_SUBMITTED",
           f"map_id={map_id} by {body.submitted_by} status={evidence.status}")

    return SubmitResponse(
        ok=True,
        message=message,
        evidence_id=evidence.id,
        map_id=map_id,
        missing_items=missing,
    )


# ── POST /maps/{map_id}/validate ──────────────────────────────────────────────

@router.post(
    "/maps/{map_id}/validate",
    response_model=ValidationResponse,
    summary="Run ValidatorAgent on the latest submitted evidence",
    description=(
        "Finds the most recent Evidence row for this MAP, "
        "runs ValidatorAgent.validate(), and updates both Evidence.status "
        "and MAPItem.status to 'complete' or 'incomplete'."
    ),
)
def validate_map(
    map_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    m = db.query(MAPItem).filter(MAPItem.id == map_id).first()
    if not m:
        raise HTTPException(404, f"MAP {map_id} not found.")

    # Get the latest evidence submission for this MAP
    evidence = (
        db.query(Evidence)
        .filter(Evidence.map_id == map_id)
        .order_by(Evidence.created_at.desc())
        .first()
    )
    if not evidence:
        raise HTTPException(
            400,
            f"No evidence submitted for MAP {map_id}. "
            "Call POST /maps/{map_id}/submit first."
        )

    # Run validator
    evidence_dict = {
        "description": evidence.description or "",
        "file_url":    evidence.file_url,
    }
    result   = agent.validate(map_id, evidence_dict, db)
    decision = result["status"]          # "complete" | "incomplete"
    missing  = result["missing_items"]   # list[str]

    # Update evidence row
    evidence.status        = decision
    evidence.missing_items = ", ".join(missing) if missing else ""

    # Update MAP status
    m.status = decision

    db.commit()

    _audit(db, f"VALIDATION_{decision.upper()}",
           f"map_id={map_id} evidence_id={evidence.id} missing={missing}")

    # Gap 2: trigger re-escalation if validator rejected the evidence
    if decision == "incomplete" and missing:
        notifier.re_escalate(
            map_item={"id": map_id, "action": m.action or ""},
            owner={"department": m.assigned_department or "Unknown", "sla_days": m.sla_days or 14},
            missing_items=missing,
        )

    return ValidationResponse(
        map_id=map_id,
        evidence_id=evidence.id,
        decision=decision,
        missing_items=missing,
        decided_at=datetime.utcnow().isoformat(),
    )


# ── POST /maps/validate-all ───────────────────────────────────────────────────

@router.post(
    "/maps/validate-all",
    response_model=list[ValidationResponse],
    summary="Batch validate all submitted evidence",
    description="Runs ValidatorAgent on every MAP currently in 'submitted' status.",
)
def validate_all(db: Session = Depends(get_db)):
    submitted_maps = (
        db.query(MAPItem)
        .filter(MAPItem.status == "submitted")
        .all()
    )

    results = []
    for m in submitted_maps:
        evidence = (
            db.query(Evidence)
            .filter(Evidence.map_id == m.id)
            .order_by(Evidence.created_at.desc())
            .first()
        )
        if not evidence:
            continue

        evidence_dict = {
            "description": evidence.description or "",
            "file_url":    evidence.file_url,
        }
        result   = agent.validate(m.id, evidence_dict, db)
        decision = result["status"]
        missing  = result["missing_items"]

        evidence.status        = decision
        evidence.missing_items = ", ".join(missing) if missing else ""
        m.status               = decision

        results.append(ValidationResponse(
            map_id=m.id,
            evidence_id=evidence.id,
            decision=decision,
            missing_items=missing,
            decided_at=datetime.utcnow().isoformat(),
        ))

    db.commit()
    _audit(db, "BATCH_VALIDATION", f"validated {len(results)} MAPs")
    return results


# ── GET /validator/log ────────────────────────────────────────────────────────

@router.get(
    "/validator/log",
    summary="Full audit trail of validation events",
)
def get_validator_log(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.event.like("VALIDATION_%"))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id":         l.id,
            "event":      l.event,
            "details":    l.details,
            "created_at": l.created_at.isoformat() if l.created_at else "",
        }
        for l in logs
    ]


# ── GET /validator/stats ──────────────────────────────────────────────────────

@router.get(
    "/validator/stats",
    response_model=ValidatorStats,
    summary="Summary counts for the dashboard cards",
)
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func

    rows = (
        db.query(MAPItem.status, func.count(MAPItem.id))
        .group_by(MAPItem.status)
        .all()
    )
    counts = {status: cnt for status, cnt in rows}

    complete   = counts.get("complete", 0)
    incomplete = counts.get("incomplete", 0)
    decided    = complete + incomplete

    return ValidatorStats(
        total_maps=sum(counts.values()),
        pending=counts.get("pending", 0) + counts.get("assigned", 0),
        submitted=counts.get("submitted", 0),
        complete=complete,
        incomplete=incomplete,
        approval_rate=round(complete / decided, 2) if decided else 0.0,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _map_to_status(m: MAPItem, db: Session) -> MAPStatus:
    evidence_rows = db.query(Evidence).filter(Evidence.map_id == m.id).all()
    latest_status = evidence_rows[-1].status if evidence_rows else None

    circular_title = None
    if m.circular_id:
        c = db.query(Circular).filter(Circular.id == m.circular_id).first()
        circular_title = c.title if c else None

    return MAPStatus(
        map_id=m.id,
        action=m.action or "",
        assigned_department=m.assigned_department,
        sla_days=m.sla_days,
        status=m.status or "pending",
        circular_title=circular_title,
        evidence_count=len(evidence_rows),
        latest_evidence_status=latest_status,
    )


def _audit(db: Session, event: str, details: str = ""):
    db.add(AuditLog(event=event, details=details, created_at=datetime.utcnow()))
    db.commit()