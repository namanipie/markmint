from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas import SearchQuery, SearchResult, SearchFilters
from backend.services.search.discovery import DiscoverySearchEngine

router = APIRouter()

@router.post("/", response_model=list[SearchResult])
def search_intelligence(query: SearchQuery, db: Session = Depends(get_db)):
    """
    Executes a hybrid semantic and metadata search across the entire ExamScope graph.
    Automatically identifies intent (e.g., trend requests vs static concept queries).
    """
    engine = DiscoverySearchEngine(db)
    return engine.search(query)


@router.get("/", response_model=list[SearchResult])
def search_intelligence_get(
    q: str = Query("", description="Search term or phrase"),
    course_id: Optional[int] = Query(None, description="Course ID filter"),
    subject: Optional[str] = Query(None, description="Subject name or code"),
    semester: Optional[int] = Query(None, description="Semester filter"),
    year: Optional[int] = Query(None, description="Exam year filter"),
    exam_type: Optional[str] = Query(None, description="Assessment cycle filter (CT1, CT2, ENDSEM)"),
    unit: Optional[str] = Query(None, description="Unit name filter"),
    topic: Optional[str] = Query(None, description="Topic name filter"),
    marks: Optional[float] = Query(None, description="Question marks filter"),
    repetition_type: Optional[str] = Query(None, description="Repetition type filter (exact, variant, singleton)"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    db: Session = Depends(get_db),
):
    """
    GET endpoint for Search Radar queries supporting URL query params.
    """
    filters = SearchFilters(
        subject=subject,
        course_id=course_id,
        semester=semester,
        year=year,
        exam_type=exam_type,
        unit=unit,
        topic=topic,
        marks=marks,
        repetition_type=repetition_type,
    )
    query = SearchQuery(raw_query=q, filters=filters, limit=limit)
    engine = DiscoverySearchEngine(db)
    return engine.search(query)
