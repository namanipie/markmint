from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas import Course, CourseCreate
from backend.services.course import CourseService

router = APIRouter()

@router.post("/", response_model=Course)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)) -> Course:
    service = CourseService(db)
    return service.create_course(course_in)

@router.get("/", response_model=list[Course])
def get_courses(db: Session = Depends(get_db)) -> list[Course]:
    service = CourseService(db)
    return service.db.query(service.repo.model).all()

@router.get("/{course_id}", response_model=Course)
def get_course(course_id: int, db: Session = Depends(get_db)) -> Course:
    service = CourseService(db)
    course = service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/tracks")
def get_course_tracks(course_id: int, db: Session = Depends(get_db)):
    """Retrieve available academic tracks for a course (e.g. language electives)."""
    from backend.models.core import CourseTrack, Course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    tracks = db.query(CourseTrack).filter(CourseTrack.course_id == course_id).order_by(CourseTrack.id).all()
    return [
        {
            "id": t.id,
            "course_id": t.course_id,
            "track_key": t.track_key,
            "track_name": t.track_name,
            "track_code": t.track_code,
            "track_type": t.track_type,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tracks
    ]

