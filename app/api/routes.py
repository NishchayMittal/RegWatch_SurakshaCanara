from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Circular, MAPItem
from app.core.orchestrator import RegWatchPipeline

router = APIRouter()

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