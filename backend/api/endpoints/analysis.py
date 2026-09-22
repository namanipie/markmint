import re
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.core.database import get_db
from backend.models.core import Exam, Course, Section, Question, QuestionConcept
from backend.schemas import ExamDNA
from backend.schemas import EvolutionReport
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.dna.evolution import ExamEvolutionService
from backend.services.assessment_cycle import normalize_assessment_cycle, filter_exams_by_cycle


router = APIRouter()

# Simple in-memory cache for expensive analysis to avoid repeated DB hits
# Key: (course_id, assessment_cycle, analysis_type), Value: (timestamp, data)
_ANALYSIS_CACHE = {}
CACHE_TTL = 300 # 5 minutes

def _get_exams_as_dicts(course_id: int, db: Session, assessment_cycle: Optional[str] = None) -> list[dict]:
    """
    Eagerly loads exams to avoid N+1 queries.
    Maps ORM objects to the dict structure expected by DNA Analyzer.
    """
    # Eager load relationships to prevent N+1
    query = (
        db.query(Exam)
        .options(
            joinedload(Exam.document),
            joinedload(Exam.sections).joinedload(Section.questions).joinedload(Question.family)
        )
        .filter(Exam.course_id == course_id)
    )
    if assessment_cycle and assessment_cycle != "ALL":
        query = filter_exams_by_cycle(query, Exam.assessment_type, assessment_cycle)
    exams = query.all()
    
    out = []
    for ex in exams:
        ex_dict = {
            "id": ex.id,
            "year": ex.year,
            "exam_type": ex.assessment_type,
            "questions": []
        }
        for sec in ex.sections:
            for q in sec.questions:
                ex_dict["questions"].append({
                    "id": q.id,
                    "marks": q.marks,
                    "is_alternative": q.is_alternative,
                    "topic": q.topics[0].name if q.topics else None,
                    "topics": [t.name for t in q.topics] if getattr(q, "topics", None) else [],
                    "unit": q.topics[0].unit.name if (q.topics and getattr(q.topics[0], "unit", None)) else None,
                    "units": (
                        list(dict.fromkeys(
                            t.unit.name for t in q.topics if getattr(t, "unit", None) and t.unit.name
                        ))
                        if getattr(q, "topics", None)
                        else []
                    ),
                    "question_type": q.question_type,
                    "repetition_type": q.family.repetition_type if q.family else None,
                    "family_name": q.family.canonical_name if q.family else None,
                    "difficulty": None # Fallback
                })
        out.append(ex_dict)
    return out

def _resolve_course(db: Session, course_identifier: str) -> Course:
    """Generically resolve a course by numeric ID, code, name, or normalized string."""
    identifier_str = str(course_identifier).strip()
    course = None
    if identifier_str.isdigit():
        course = db.query(Course).filter(Course.id == int(identifier_str)).first()
    if not course:
        course = db.query(Course).filter(func.lower(Course.code) == identifier_str.lower()).first()
    if not course:
        course = db.query(Course).filter(func.lower(Course.name) == identifier_str.lower()).first()
    if not course:
        norm_id = re.sub(r'[^a-zA-Z0-9]', '', identifier_str).lower()
        if norm_id:
            for c in db.query(Course).all():
                if re.sub(r'[^a-zA-Z0-9]', '', c.name).lower() == norm_id:
                    course = c
                    break
                if re.sub(r'[^a-zA-Z0-9]', '', c.code).lower() == norm_id:
                    course = c
                    break
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/dna", response_model=ExamDNA)
def get_course_dna(
    course_id: str = Query(..., description="The ID, code, or name of the course to analyze"),
    assessment_cycle: Optional[str] = Query(None, description="Assessment cycle filter: ALL, CT1, CT2, ENDSEM"),
    db: Session = Depends(get_db)
):
    course = _resolve_course(db, course_id)
    norm_cycle = normalize_assessment_cycle(assessment_cycle)
    cache_key = (course.id, norm_cycle or "ALL", "dna")
    if cache_key in _ANALYSIS_CACHE:
        ts, data = _ANALYSIS_CACHE[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data

    exams_dict = _get_exams_as_dicts(course.id, db, norm_cycle)
    dna_report = DNAAnalyzerService.analyze(exams_dict)
    
    _ANALYSIS_CACHE[cache_key] = (time.time(), dna_report)
    return dna_report

@router.get("/evolution", response_model=EvolutionReport)
def get_course_evolution(
    course_id: str = Query(..., description="The ID, code, or name of the course to track"),
    assessment_cycle: Optional[str] = Query(None, description="Assessment cycle filter: ALL, CT1, CT2, ENDSEM"),
    db: Session = Depends(get_db)
):
    course = _resolve_course(db, course_id)
    norm_cycle = normalize_assessment_cycle(assessment_cycle)
    cache_key = (course.id, norm_cycle or "ALL", "evolution")
    if cache_key in _ANALYSIS_CACHE:
        ts, data = _ANALYSIS_CACHE[cache_key]
        if time.time() - ts < CACHE_TTL:
            return data

    exams_dict = _get_exams_as_dicts(course.id, db, norm_cycle)
    evolution_report = ExamEvolutionService.analyze_evolution(course.id, exams_dict)
    
    _ANALYSIS_CACHE[cache_key] = (time.time(), evolution_report)
    return evolution_report


