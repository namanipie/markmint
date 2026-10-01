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
