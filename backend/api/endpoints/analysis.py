import re
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from backend.core.database import get_db
from backend.models.core import Exam, Course, Section, Question, Topic, CourseTrack
from backend.schemas import ExamDNA, EvolutionReport
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.dna.evolution import ExamEvolutionService
from backend.services.assessment_cycle import normalize_assessment_cycle, filter_exams_by_cycle
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository


from backend.services.intelligence_cache import analysis_cache as _ANALYSIS_CACHE, BoundedAnalysisCache


router = APIRouter()

# Bounded, thread-safe in-memory cache for expensive analysis to avoid repeated DB hits
CACHE_TTL = 300  # 5 minutes


def invalidate_analysis_cache(course_id: Optional[int] = None) -> int:
    """Explicitly invalidate in-memory analysis reports for a course, or all courses if None."""
    if course_id is not None:
        return _ANALYSIS_CACHE.invalidate_course(course_id)
    cleared = len(_ANALYSIS_CACHE)
    _ANALYSIS_CACHE.clear()
    return cleared

def _resolve_track(course: Course, language: Optional[str]) -> Optional[CourseTrack]:
    if not course or not course.tracks or not language:
        return None
    lang_clean = language.strip().lower()
    for t in course.tracks:
        if (
            t.track_key.lower() == lang_clean
            or t.track_name.lower() == lang_clean
            or (t.track_code and t.track_code.lower() == lang_clean)
            or str(t.id) == lang_clean
        ):
            return t
    return None

def _get_exams_as_dicts(
    course_id: int,
    db: Session,
    assessment_cycle: Optional[str] = None,
    cutoff_year: Optional[int] = None,
    track_id: Optional[int] = None
) -> list[dict]:
    """
    Eagerly loads exams to avoid N+1 queries.
    Integrates with HistoricalRepository when cutoff_year is supplied to guarantee zero leakage.
    Maps ORM objects to the dict structure expected by DNA Analyzer.
    """
    if cutoff_year is not None:
        context = HistoricalContext(
            course_id=course_id,
            cutoff_year=cutoff_year,
            assessment_cycle=assessment_cycle,
            track_id=track_id
        )
        repo = HistoricalRepository(db, context)
        exams = repo.get_historical_exams()
    else:
        query = (
            db.query(Exam)
            .options(
                selectinload(Exam.document),
                selectinload(Exam.sections)
                .selectinload(Section.questions)
                .selectinload(Question.topics)
                .selectinload(Topic.unit),
                selectinload(Exam.sections)
                .selectinload(Section.questions)
                .selectinload(Question.family),
                selectinload(Exam.sections)
                .selectinload(Section.questions)
                .selectinload(Question.memberships),
            )
            .filter(Exam.course_id == course_id)
        )
        if track_id is not None:
            query = query.filter(Exam.track_id == track_id)
        if assessment_cycle and assessment_cycle != "ALL":
            query = filter_exams_by_cycle(query, Exam.assessment_type, assessment_cycle, course_id=course_id)
        exams = query.order_by(Exam.year.asc()).all()
    
    out = []
    for ex in exams:
        ex_dict = {
            "id": ex.id,
            "year": ex.year,
            "course_id": ex.course_id,
            "exam_type": ex.assessment_type,
            "questions": []
        }
        for sec in ex.sections:
            for q in sec.questions:
                q_topics = [t.name for t in q.topics] if getattr(q, "topics", None) else []
                q_units = (
                    list(dict.fromkeys(
                        t.unit.name for t in q.topics if getattr(t, "unit", None) and t.unit.name
                    ))
                    if getattr(q, "topics", None)
                    else []
                )
                rep_type = None
                if getattr(q, "memberships", None) and len(q.memberships) > 0:
                    rep_type = q.memberships[0].match_type
                elif q.family and q.family.repetition_type:
                    rep_type = q.family.repetition_type

                ex_dict["questions"].append({
                    "id": q.id,
                    "marks": q.marks,
                    "is_alternative": q.is_alternative,
                    "topic": q_topics[0] if q_topics else None,
                    "topics": q_topics,
                    "unit": q_units[0] if q_units else None,
                    "units": q_units,
                    "question_type": q.question_type,
                    "original_text": q.original_text or q.normalized_text,
                    "repetition_type": rep_type,
                    "family_name": q.family.canonical_name if q.family else None,
                    "family_id": q.family.id if q.family else None,
                    "difficulty": q.difficulty
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
    cutoff_year: Optional[int] = Query(None, description="Optional temporal cutoff year (strictly excludes exams on or after this year)"),
    language: Optional[str] = Query(None, description="Language track for multi-track courses (e.g. German, French)"),
    track_id: Optional[int] = Query(None, description="Optional explicit CourseTrack ID"),
    db: Session = Depends(get_db)
):
    course = _resolve_course(db, course_id)
    active_track = None
    if course and course.tracks:
        if track_id:
            active_track = next((t for t in course.tracks if t.id == track_id), None)
        elif language:
            active_track = _resolve_track(course, language)

    resolved_track_id = active_track.id if active_track else track_id
    norm_cycle = normalize_assessment_cycle(assessment_cycle)
    cache_key = (course.id, norm_cycle or "ALL", cutoff_year, resolved_track_id, "dna")
    cached_dna = _ANALYSIS_CACHE.get(cache_key)
    if cached_dna is not None:
        return cached_dna

    exams_dict = _get_exams_as_dicts(
        course.id,
        db,
        norm_cycle,
        cutoff_year=cutoff_year,
        track_id=resolved_track_id
    )
    dna_report = DNAAnalyzerService.analyze(exams_dict, target_course_id=course.id)
    
    _ANALYSIS_CACHE.set(cache_key, dna_report)
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
    cached_evolution = _ANALYSIS_CACHE.get(cache_key)
    if cached_evolution is not None:
        return cached_evolution

    exams_dict = _get_exams_as_dicts(course.id, db, norm_cycle)
    evolution_report = ExamEvolutionService.analyze_evolution(course.id, exams_dict)
    
    _ANALYSIS_CACHE.set(cache_key, evolution_report)
    return evolution_report


