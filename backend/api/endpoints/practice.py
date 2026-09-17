from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question

router = APIRouter()

@router.get("/practice/{subject}")
def get_practice_questions(subject: str, limit: int = 20):
    db = SessionLocal()
    try:
        from backend.api.endpoints.predictions import _find_course
        course = _find_course(db, subject)
        if not course:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Fetch recent historical questions
        questions = (
            db.query(Question, Exam.year)
            .select_from(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == course.id)
            .order_by(Exam.year.desc().nullslast(), Question.id.asc())
            .limit(limit)
            .all()
        )

        formatted_questions = []
        for q, year in questions:
            formatted_questions.append({
                "id": q.id,
                "text": q.original_text,
                "year": year,
                "marks": q.marks,
                "family": q.family.canonical_name if q.family else None
            })

        return {
            "subject": subject,
            "questions": formatted_questions
        }
    finally:
        db.close()
