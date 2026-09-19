from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question
from backend.services.assessment_cycle import normalize_assessment_cycle, filter_exams_by_cycle

router = APIRouter()

@router.get("/practice/{subject}")
def get_practice_questions(subject: str, limit: int = 20, assessment_cycle: Optional[str] = Query(None)):
    db = SessionLocal()
    try:
        from backend.api.endpoints.predictions import _find_course
        course = _find_course(db, subject)
        if not course:
            raise HTTPException(status_code=404, detail="Subject not found")

        norm_cycle = normalize_assessment_cycle(assessment_cycle)

        # Fetch recent historical questions
        query = (
            db.query(Question, Exam.year)
            .select_from(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == course.id)
        )

        if norm_cycle and norm_cycle != "ALL":
            query = filter_exams_by_cycle(query, Exam.assessment_type, norm_cycle)

        questions = (
            query
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
            "assessment_cycle": norm_cycle or "ALL",
            "questions": formatted_questions
        }
    finally:
        db.close()
