from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.core.database import get_db
from backend.models.core import SystemBroadcast
from backend.schemas import SystemBroadcastCreate, SystemBroadcastResponse

router = APIRouter()

@router.post("/broadcast", response_model=SystemBroadcastResponse)
def create_broadcast(broadcast: SystemBroadcastCreate, db: Session = Depends(get_db)):
    # Deactivate all previous broadcasts
    db.query(SystemBroadcast).update({"is_active": False})
    
    new_broadcast = SystemBroadcast(
        message=broadcast.message,
        type=broadcast.type,
        is_active=broadcast.is_active
    )
    db.add(new_broadcast)
    db.commit()
    db.refresh(new_broadcast)
    return new_broadcast

@router.get("/broadcast/active", response_model=SystemBroadcastResponse)
def get_active_broadcast(db: Session = Depends(get_db)):
    active = db.query(SystemBroadcast).filter(SystemBroadcast.is_active == True).order_by(SystemBroadcast.id.desc()).first()
    if not active:
        raise HTTPException(status_code=404, detail="No active broadcast")
    return active

from backend.models.core import FailedSearchLog
from sqlalchemy import func
from pydantic import BaseModel

class FailedSearchRequest(BaseModel):
    query: str
    assessment: str = None

@router.post("/radar/fail")
def log_failed_search(req: FailedSearchRequest, db: Session = Depends(get_db)):
    log = FailedSearchLog(query=req.query, assessment=req.assessment)
    db.add(log)
    db.commit()
    return {"status": "logged"}

@router.get("/radar/stats")
def get_radar_stats(db: Session = Depends(get_db)):
    # Group by query and count
    results = db.query(
        FailedSearchLog.query, 
        FailedSearchLog.assessment, 
        func.count(FailedSearchLog.id).label("count")
    ).group_by(FailedSearchLog.query, FailedSearchLog.assessment).order_by(func.count(FailedSearchLog.id).desc()).limit(20).all()
    
    formatted = [
        {
            "query": r.query, 
            "assessment": r.assessment or "Unknown", 
            "count": r.count
        } for r in results
    ]
    
    total_fails = db.query(func.count(FailedSearchLog.id)).scalar()
    
    return {
        "total_fails": total_fails,
        "priorities": formatted
    }
