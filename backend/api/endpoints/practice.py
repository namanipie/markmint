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

        scope = None
        if norm_cycle and norm_cycle != "ALL":
            from backend.services.assessment_plan_registry import get_course_assessment_scope
            scope = get_course_assessment_scope(course.id, norm_cycle, db=db)
            query = filter_exams_by_cycle(query, Exam.assessment_type, norm_cycle, course_id=course.id)

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
            "assessment_component": scope.component_code if scope else (norm_cycle or "ALL"),
            "assessment_label": scope.component_label if scope else (norm_cycle or "All Assessments"),
            "evidence_status": scope.evidence_status if scope else "ALL_SCOPE",
            "intended_scope": scope.intended_scope if scope else None,
            "observed_scope": scope.observed_scope if scope else None,
            "assessment_scope": {
                "student_cycle": norm_cycle or "ALL",
                "component_code": scope.component_code,
                "component_label": scope.component_label,
                "student_label": scope.student_label,
                "role": scope.role,
                "marks": scope.marks,
                "evidence_status": scope.evidence_status,
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "unit_numbers": sorted(list(scope.in_scope_unit_numbers)),
            } if scope else None,
            "questions": formatted_questions
        }
    finally:
        db.close()
