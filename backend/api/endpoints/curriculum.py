from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.database import get_db
from backend.models.core import CurriculumMapping, Course, Exam, Section, Question
from backend.schemas import CurriculumSubjectResponse

router = APIRouter()


@router.get("/branches", response_model=List[str])
def get_curriculum_branches(db: Session = Depends(get_db)) -> List[str]:
    """Return all unique academic branches available in the curriculum catalog."""
    from backend.services.curriculum_seeder import ensure_curriculum_seeded
    ensure_curriculum_seeded(db)

    branches = (
        db.query(CurriculumMapping.branch_name)
        .distinct()
        .order_by(CurriculumMapping.branch_name.asc())
        .all()
    )
    return [b[0] for b in branches]


@router.get("/branches/{branch}/semesters", response_model=List[int])
def get_branch_semesters(branch: str, db: Session = Depends(get_db)) -> List[int]:
    """Return all available semesters for a specific academic branch."""
    semesters = (
        db.query(CurriculumMapping.semester)
        .filter(func.lower(CurriculumMapping.branch_name) == branch.lower())
        .distinct()
        .order_by(CurriculumMapping.semester.asc())
        .all()
    )
    if not semesters:
        raise HTTPException(status_code=404, detail="Branch not found")
    return [s[0] for s in semesters]


@router.get("/branches/{branch}/semesters/{semester}", response_model=List[CurriculumSubjectResponse])
def get_branch_semester_subjects(
    branch: str, 
    semester: int, 
    db: Session = Depends(get_db)
) -> List[CurriculumSubjectResponse]:
    """Return all subjects for a branch and semester with their canonical intelligence status."""
    mappings = (
        db.query(CurriculumMapping)
        .filter(
            func.lower(CurriculumMapping.branch_name) == branch.lower(),
            CurriculumMapping.semester == semester
        )
        .order_by(CurriculumMapping.curriculum_id.asc())
        .all()
    )

    if not mappings:
        raise HTTPException(
            status_code=404, 
            detail=f"No curriculum found for branch '{branch}' semester {semester}"
        )

    # Pre-fetch course exam counts and question counts to avoid N+1
    course_ids = [m.course_id for m in mappings if m.course_id is not None]
    exam_stats = {}
    if course_ids:
        # Query exam counts per course
        exam_rows = (
            db.query(Exam.course_id, func.count(Exam.id))
            .filter(Exam.course_id.in_(course_ids))
            .group_by(Exam.course_id)
            .all()
        )
        exam_counts = {r[0]: r[1] for r in exam_rows}

        # Query question counts per course
        q_rows = (
            db.query(Exam.course_id, func.count(Question.id))
            .join(Section, Section.exam_id == Exam.id)
            .join(Question, Question.section_id == Section.id)
            .filter(Exam.course_id.in_(course_ids))
            .group_by(Exam.course_id)
            .all()
        )
        q_counts = {r[0]: r[1] for r in q_rows}

        for cid in course_ids:
            exam_stats[cid] = {
                "exams": exam_counts.get(cid, 0),
                "questions": q_counts.get(cid, 0)
            }

    results = []
    for m in mappings:
        c_stats = exam_stats.get(m.course_id, {"exams": 0, "questions": 0})
        has_exams = c_stats["exams"] > 0
        canonical_code = m.course.canonical_code if m.course else None

        results.append(CurriculumSubjectResponse(
            curriculum_id=m.curriculum_id,
            subject_name=m.subject_name,
            credits=m.credits or 3,
            course_id=m.course_id,
            canonical_code=canonical_code,
            status=m.status,
            has_exams=has_exams,
            exam_count=c_stats["exams"],
            question_count=c_stats["questions"],
            notes=m.notes
        ))

    return results


@router.get("/stats")
def get_curriculum_stats(db: Session = Depends(get_db)) -> dict:
    """Return summary statistics of curriculum reconciliation and corpus coverage."""
    total = db.query(CurriculumMapping).count()
    branches = db.query(CurriculumMapping.branch_name).distinct().count()
    matched = db.query(CurriculumMapping).filter(CurriculumMapping.status == "MATCHED").count()
    ambiguous = db.query(CurriculumMapping).filter(CurriculumMapping.status == "AMBIGUOUS").count()
    unmatched = db.query(CurriculumMapping).filter(CurriculumMapping.status == "UNMATCHED").count()
    courses_count = db.query(Course).count()

    return {
        "total_entries": total,
        "branches_count": branches,
        "matched_entries": matched,
        "ambiguous_entries": ambiguous,
        "unmatched_entries": unmatched,
        "backend_courses_count": courses_count
    }
