import re
import time
from collections import deque
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import require_admin_auth
from backend.models.beta_telemetry import BetaEvent
from backend.models.core import FailedSearchLog, SystemBroadcast
from backend.schemas import SystemBroadcastCreate, SystemBroadcastResponse

router = APIRouter()

# In-memory sliding window for spam throttling and deduplication debounce
# Stores tuples of (normalized_query, normalized_assessment, timestamp)
_recent_failed_searches: deque = deque(maxlen=2000)
_client_request_timestamps: Dict[str, deque] = {}


def _clean_string(text: Optional[str], max_len: int = 256) -> Optional[str]:
    if not text:
        return None
    # Strip non-printable/control characters (keep basic printable text)
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", str(text)).strip()
    return cleaned[:max_len] if cleaned else None


# ---------------------------------------------------------------------------
# BROADCAST ENDPOINTS
# ---------------------------------------------------------------------------

@router.post("/broadcast", response_model=SystemBroadcastResponse)
def create_broadcast(
    broadcast: SystemBroadcastCreate,
    admin: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    """Publish a site-wide broadcast banner. Requires administrative credentials."""
    # Deactivate all previous broadcasts
    db.query(SystemBroadcast).update({"is_active": False})

    new_broadcast = SystemBroadcast(
        message=broadcast.message.strip(),
        type=broadcast.type,
        is_active=broadcast.is_active,
    )
    db.add(new_broadcast)
    db.commit()
    db.refresh(new_broadcast)
    return new_broadcast


@router.get("/broadcast/active", response_model=SystemBroadcastResponse)
def get_active_broadcast(db: Session = Depends(get_db)):
    """Fetch the currently active broadcast banner (publicly accessible)."""
    active = (
        db.query(SystemBroadcast)
        .filter(SystemBroadcast.is_active == True)
        .order_by(SystemBroadcast.id.desc())
        .first()
    )
    if not active:
        raise HTTPException(status_code=404, detail="No active broadcast")
    return active


# ---------------------------------------------------------------------------
# SEARCH RADAR TELEMETRY ENDPOINTS
# ---------------------------------------------------------------------------

class FailedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=256)
    assessment: Optional[str] = Field(None, max_length=50)
    subject: Optional[str] = Field(None, max_length=100)
    course_id: Optional[int] = None


class FailedSearchLogResponse(BaseModel):
    status: str
    query: str
    deduplicated: bool = False


@router.post("/radar/fail", response_model=FailedSearchLogResponse)
def log_failed_search(
    req: FailedSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Log failed search queries from the student Command Palette.
    Includes rate-limiting, deduplication debounce, and input sanitization
    to prevent spam and storage abuse.
    """
    cleaned_query = _clean_string(req.query, max_len=256)
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty or whitespace-only.",
        )

    cleaned_assessment = _clean_string(req.assessment, max_len=50)
    cleaned_subject = _clean_string(req.subject, max_len=100)
    course_id = req.course_id

    # 1. IP rate limiting (max 60 telemetry pings per minute per client)
    client_ip = request.client.host if request.client else "unknown"
    now_ts = time.time()

    if client_ip not in _client_request_timestamps:
        _client_request_timestamps[client_ip] = deque(maxlen=100)

    ip_timestamps = _client_request_timestamps[client_ip]
    # Purge timestamps older than 60s
    while ip_timestamps and now_ts - ip_timestamps[0] > 60:
        ip_timestamps.popleft()

    if len(ip_timestamps) >= 60:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Telemetry rate limit exceeded. Please try again later.",
        )
    ip_timestamps.append(now_ts)

    # 2. Debounce duplicate searches within a 10-second window
    norm_key = (cleaned_query.lower(), (cleaned_assessment or "").lower())
    cutoff_ts = now_ts - 10.0

    # Purge stale memory cache entries older than 60 seconds
    while _recent_failed_searches and now_ts - _recent_failed_searches[0][2] > 60:
        _recent_failed_searches.popleft()

    # Check if identical query was logged within 10 seconds
    is_duplicate = any(
        k == norm_key and ts >= cutoff_ts for k, _, ts in _recent_failed_searches
    )

    if is_duplicate:
        return FailedSearchLogResponse(
            status="logged",
            query=cleaned_query,
            deduplicated=True,
        )

    # Record in debounce buffer
    _recent_failed_searches.append((norm_key, None, now_ts))

    # Persist to database
    log = FailedSearchLog(
        query=cleaned_query,
        assessment=cleaned_assessment,
        subject=cleaned_subject,
        course_id=course_id,
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()

    return FailedSearchLogResponse(
        status="logged",
        query=cleaned_query,
        deduplicated=False,
    )


class PrioritySearchItem(BaseModel):
    query: str
    assessment: str
    count: int
    latest_occurrence: Optional[str] = None


class RadarStatsResponse(BaseModel):
    total_fails: int
    time_range_days: int
    priorities: List[PrioritySearchItem]
    active_users_24h: int


@router.get("/radar/stats", response_model=RadarStatsResponse)
def get_radar_stats(
    days: int = Query(30, ge=1, le=365, description="Lookback window in days"),
    limit: int = Query(50, ge=1, le=200, description="Max aggregated items to return"),
    subject: Optional[str] = Query(None, description="Filter by subject or keyword"),
    assessment: Optional[str] = Query(None, description="Filter by assessment type"),
    admin: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    """
    Retrieve aggregated failed search telemetry for administrative analysis.
    Requires administrative credentials.
    """
    since_dt = datetime.utcnow() - timedelta(days=days)

    query = (
        db.query(
            FailedSearchLog.query,
            FailedSearchLog.assessment,
            func.count(FailedSearchLog.id).label("count"),
            func.max(FailedSearchLog.timestamp).label("latest_occurrence"),
        )
        .filter(FailedSearchLog.timestamp >= since_dt)
    )

    if subject:
        cleaned_sub = subject.strip().lower()
        query = query.filter(
            (FailedSearchLog.query.ilike(f"%{cleaned_sub}%"))
            | (FailedSearchLog.subject.ilike(f"%{cleaned_sub}%"))
        )

    if assessment:
        query = query.filter(FailedSearchLog.assessment == assessment.strip())

    results = (
        query
        .group_by(FailedSearchLog.query, FailedSearchLog.assessment)
        .order_by(func.count(FailedSearchLog.id).desc())
        .limit(limit)
        .all()
    )

    formatted = [
        PrioritySearchItem(
            query=r.query,
            assessment=r.assessment or "Unknown",
            count=r.count,
            latest_occurrence=r.latest_occurrence.isoformat() if r.latest_occurrence else None,
        )
        for r in results
    ]

    total_fails = (
        db.query(func.count(FailedSearchLog.id))
        .filter(FailedSearchLog.timestamp >= since_dt)
        .scalar()
        or 0
    )

    # Active Users (24h) from telemetry
    yesterday = datetime.utcnow() - timedelta(days=1)
    active_users_24h = (
        db.query(func.count(func.distinct(BetaEvent.session_id)))
        .filter(BetaEvent.created_at >= yesterday)
        .scalar()
        or 0
    )

    return RadarStatsResponse(
        total_fails=total_fails,
        time_range_days=days,
        priorities=formatted,
        active_users_24h=active_users_24h,
    )
