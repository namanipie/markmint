from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.database import get_db
from backend.models.core import CurriculumMapping, Course, Exam, Section, Question
from backend.models.beta_telemetry import StudentExamAnnouncement, BetaEvent
from backend.schemas import (
    CurriculumSubjectResponse,
    CourseTrackResponse,
    EnrollmentPlanResponse,
    EnrollmentCourseItem,
)

router = APIRouter()

_cached_branches: Optional[List[str]] = None
_cached_semesters: dict[str, List[int]] = {}


def get_cached_branches(db: Session) -> List[str]:
    global _cached_branches
    if _cached_branches is not None:
        return _cached_branches
    branches = (
        db.query(CurriculumMapping.branch_name)
        .distinct()
        .order_by(CurriculumMapping.branch_name.asc())
        .all()
    )
    _cached_branches = [b[0] for b in branches]
    return _cached_branches


def get_cached_semesters(branch: str, db: Session) -> List[int]:
    global _cached_semesters
    branch_key = branch.strip().lower()
    if branch_key in _cached_semesters:
        return _cached_semesters[branch_key]
    semesters = (
        db.query(CurriculumMapping.semester)
        .filter(func.lower(CurriculumMapping.branch_name) == branch_key)
        .distinct()
        .order_by(CurriculumMapping.semester.asc())
        .all()
    )
    if not semesters:
        return []
    res = [s[0] for s in semesters]
    _cached_semesters[branch_key] = res
    return res


@router.get("/branches", response_model=List[str])
def get_curriculum_branches(db: Session = Depends(get_db)) -> List[str]:
    """Return all unique academic branches available in the curriculum catalog (cached)."""
    return get_cached_branches(db)


@router.get("/branches/{branch}/semesters", response_model=List[int])
def get_branch_semesters(branch: str, db: Session = Depends(get_db)) -> List[int]:
    """Return all available semesters for a specific academic branch (cached)."""
    semesters = get_cached_semesters(branch, db)
    if not semesters:
        raise HTTPException(status_code=404, detail="Branch not found")
    return semesters


@router.get("/initial-scope")
def get_initial_scope(
    branch: Optional[str] = None,
    semester: Optional[int] = None,
    db: Session = Depends(get_db)
) -> dict:
    """Return branches, default branch, semesters, and subjects in ONE single network round-trip."""
    branches = get_cached_branches(db)
    if not branches:
        return {
            "branches": [],
            "default_branch": "",
            "semesters": [],
            "default_semester": 1,
            "subjects": []
        }

    selected_branch = branch if branch and branch in branches else (
        "Aerospace Engineering" if "Aerospace Engineering" in branches else branches[0]
    )
    semesters = get_cached_semesters(selected_branch, db)
    selected_semester = semester if semester and semester in semesters else (
        semesters[0] if semesters else 1
    )

    subjects = get_branch_semester_subjects(selected_branch, selected_semester, db)
    serialized_subjects = [
        s.model_dump() if hasattr(s, "model_dump") else s.dict()
        for s in subjects
    ]

    return {
        "branches": branches,
        "default_branch": selected_branch,
        "semesters": semesters,
        "default_semester": selected_semester,
        "subjects": serialized_subjects
    }


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

        course_tracks = []
        if m.course and getattr(m.course, "tracks", None):
            course_tracks = [
                CourseTrackResponse(
                    id=t.id,
                    course_id=t.course_id,
                    track_key=t.track_key,
                    track_name=t.track_name,
                    track_code=t.track_code,
                    track_type=t.track_type,
                )
                for t in m.course.tracks
            ]

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
            has_tracks=len(course_tracks) > 0,
            tracks=course_tracks,
            notes=m.notes
        ))

    return results


SRMIST_GRADE_SCALE = {
    "O": 10.0,
    "A+": 9.0,
    "A": 8.0,
    "B+": 7.0,
    "B": 6.0,
    "C": 5.0,
    "W": 0.0,
    "F": 0.0,
    "Ab": 0.0,
}


@router.get("/branches/{branch}/semesters/{semester}/enrollment", response_model=EnrollmentPlanResponse)
def get_branch_semester_enrollment(
    branch: str,
    semester: int,
    db: Session = Depends(get_db)
) -> EnrollmentPlanResponse:
    """Return pre-populated course enrollment plan for GPA and CGPA calculations."""
    branches = get_cached_branches(db)
    target_branch = branch
    matched = False
    for b in branches:
        if b.lower() == branch.lower() or b.lower().replace(" ", "-") == branch.lower():
            target_branch = b
            matched = True
            break
    if not matched:
        for b in branches:
            if branch.lower() in b.lower():
                target_branch = b
                matched = True
                break

    subjects = get_branch_semester_subjects(target_branch, semester, db)
    
    courses = []
    for s in subjects:
        name_lower = s.subject_name.lower()
        if "lab" in name_lower or "laboratory" in name_lower or "practical" in name_lower:
            course_type = "PRACTICAL"
            credits = float(s.credits) if (s.credits and s.credits > 0) else 1.5
        elif "project" in name_lower or "capstone" in name_lower or "internship" in name_lower:
            course_type = "PROJECT"
            credits = float(s.credits) if (s.credits and s.credits > 0) else 2.0
        elif s.canonical_code and s.canonical_code.strip().endswith("J"):
            course_type = "INTEGRATED"
            credits = float(s.credits) if (s.credits and s.credits > 0) else 4.0
        elif s.canonical_code and s.canonical_code.strip().endswith("L"):
            course_type = "PRACTICAL"
            credits = float(s.credits) if (s.credits and s.credits > 0) else 1.5
        else:
            course_type = "THEORY"
            credits = float(s.credits) if (s.credits and s.credits > 0) else 3.0

        is_elective = "elective" in name_lower or (s.notes is not None and "elective" in s.notes.lower())

        courses.append(EnrollmentCourseItem(
            curriculum_id=s.curriculum_id,
            subject_name=s.subject_name,
            canonical_code=s.canonical_code,
            course_id=s.course_id,
            credits=credits,
            course_type=course_type,
            is_elective=is_elective,
            has_exams=s.has_exams,
            exam_count=s.exam_count,
            question_count=s.question_count,
            status=s.status,
            notes=s.notes,
        ))

    total_credits = sum(c.credits for c in courses)

    return EnrollmentPlanResponse(
        branch_name=target_branch,
        semester=semester,
        total_default_credits=total_credits,
        grade_scale=SRMIST_GRADE_SCALE,
        courses=courses,
    )


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


# ---------------------------------------------------------------------------
# STUDENT EXAM SCOPE & ANNOUNCEMENTS
# ---------------------------------------------------------------------------

_in_memory_announcements: List[Dict[str, Any]] = []

class ExamAnnouncementCreate(BaseModel):
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    course_name: str = Field(..., min_length=2, max_length=255)
    exam_type: str = Field(..., max_length=64)
    exam_title: Optional[str] = Field(None, max_length=128)
    units: List[int] = Field(..., min_length=1)
    batch_department: Optional[str] = Field(None, max_length=128)
    announced_date: Optional[str] = Field(None, max_length=64)
    notes: Optional[str] = Field(None, max_length=1000)
    session_id: Optional[str] = Field(None, max_length=64)


@router.post("/exam-announcements")
def create_exam_announcement(
    data: ExamAnnouncementCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Allows students to report upcoming exam portions (units, exam type, batch)
    to help calibrate forecasts and practice questions for their classmates.
    """
    clean_units = sorted(list({int(u) for u in data.units if 1 <= int(u) <= 10}))
    if not clean_units:
        clean_units = [1, 2]

    announcement_dict = {
        "course_id": data.course_id,
        "course_code": data.course_code,
        "course_name": data.course_name,
        "exam_type": data.exam_type,
        "exam_title": data.exam_title or data.exam_type,
        "units": clean_units,
        "batch_department": data.batch_department,
        "announced_date": data.announced_date,
        "notes": data.notes,
        "created_at": datetime.utcnow().isoformat()
    }

    record_id = None
    try:
        record = StudentExamAnnouncement(
            course_id=data.course_id,
            course_code=data.course_code,
            course_name=data.course_name,
            exam_type=data.exam_type,
            exam_title=data.exam_title or data.exam_type,
            units=clean_units,
            batch_department=data.batch_department,
            announced_date=data.announced_date,
            notes=data.notes,
            session_id=data.session_id
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id
    except Exception:
        db.rollback()
        record_id = len(_in_memory_announcements) + 1

    announcement_dict["id"] = record_id
    _in_memory_announcements.append(announcement_dict)

    return {
        "status": "success",
        "message": f"Exam portion for {data.course_name} recorded successfully! Thank you for helping your classmates.",
        "announcement": announcement_dict
    }


@router.get("/exam-announcements/{course_id}")
def get_exam_announcements_for_course(
    course_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Fetch recent student-reported exam portions and unit scopes for a course."""
    results = []
    try:
        db_records = (
            db.query(StudentExamAnnouncement)
            .filter(StudentExamAnnouncement.course_id == course_id)
            .order_by(StudentExamAnnouncement.id.desc())
            .limit(limit)
            .all()
        )
        for r in db_records:
            results.append({
                "id": r.id,
                "course_id": r.course_id,
                "course_code": r.course_code,
                "course_name": r.course_name,
                "exam_type": r.exam_type,
                "exam_title": r.exam_title,
                "units": r.units,
                "batch_department": r.batch_department,
                "announced_date": r.announced_date,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else "Just now"
            })
    except Exception:
        pass

    # Combine with in-memory fallback
    for mem in reversed(_in_memory_announcements):
        if mem.get("course_id") == course_id and not any(r["id"] == mem.get("id") for r in results):
            results.append(mem)
        if len(results) >= limit:
            break

    return results
