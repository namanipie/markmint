from typing import Any, Dict, List, Optional
from datetime import datetime
import copy
import time
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.core.database import get_db
from backend.core.version import (
    MODEL_VERSION, TAXONOMY_VERSION, ENGINE_VERSION,
    CORPUS_VERSION, CALIBRATION_METHOD, SCORE_SEMANTICS
)
from backend.models.core import (
    Course, Exam, Section, Question, Topic, Unit, Syllabus, QuestionFamily, QuestionFamilyMembership,
    Document, StudyEvidence, CurriculumMapping, Concept
)
from backend.api.endpoints.predictions import _find_course, _build_historical_exam_payloads
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService, DataSufficiency
from backend.services.prediction.engine import (
    ExamScopeCombinedModel, AllTimeFrequencyBaseline, RecentFrequencyBaseline,
    RecencyWeightedBaseline, MarksWeightedBaseline, FamilyRecurrenceBaseline,
    PredictionResult
)
from backend.services.prediction.backtester import BacktestEvaluator
from backend.services.study_intelligence import StudyIntelligenceService, StudyPriority
from backend.services.assessment_cycle import AssessmentCycle, normalize_assessment_cycle, filter_exams_by_cycle
from backend.services.assessment_plan_registry import get_course_assessment_scope
from backend.services.intelligence_cache import IntelligenceCacheService

logger = logging.getLogger("markmint.intelligence")

router = APIRouter()


@router.get("/{course_id}/questions")
def get_course_historical_questions(
    course_id: str,
    topic: Optional[str] = Query(None),
    assessment_cycle: Optional[str] = Query(None),
    assessment_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    min_marks: Optional[float] = Query(None),
    max_marks: Optional[float] = Query(None),
    family_id: Optional[int] = Query(None),
    family_name: Optional[str] = Query(None),
    repetition_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Expose verified historical examination questions chronologically for a course and optional topic or family."""
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
    )

    if course and course.tracks:
        if not language:
            raise HTTPException(
                status_code=400,
                detail="TRACK_SELECTION_REQUIRED: Language track selection is required for this subject."
            )
        lang_low = language.strip().lower()
        active_track = next(
            (t for t in course.tracks if t.track_key.lower() == lang_low or t.track_name.lower() == lang_low or str(t.id) == lang_low),
            None
        )
        if not active_track:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language track '{language}'. Available: {[t.track_key for t in course.tracks]}"
            )
        query = query.filter(Exam.track_id == active_track.id)

    if hasattr(topic, "default"):
        topic = None
    if hasattr(year, "default"):
        year = None
    if hasattr(min_marks, "default"):
        min_marks = None
    if hasattr(max_marks, "default"):
        max_marks = None
    if hasattr(family_id, "default"):
        family_id = None
    if hasattr(family_name, "default"):
        family_name = None
    if hasattr(repetition_type, "default"):
        repetition_type = None
    if hasattr(limit, "default"):
        limit = limit.default or 50
    else:
        limit = int(limit)

    if topic:
        query = query.join(Question.topics).filter(func.lower(Topic.name) == topic.lower())

    active_cycle = assessment_cycle or assessment_type
    norm_cycle = normalize_assessment_cycle(active_cycle)
    if norm_cycle and norm_cycle != AssessmentCycle.ALL.value:
        query = filter_exams_by_cycle(query, Exam.assessment_type, norm_cycle, course_id=course.id)

    if year is not None:
        query = query.filter(Exam.year == year)

    if min_marks is not None:
        query = query.filter(Question.marks >= min_marks)

    if max_marks is not None:
        query = query.filter(Question.marks <= max_marks)

    if family_id is not None:
        query = query.filter(Question.family_id == family_id)
    elif family_name:
        query = query.join(Question.family).filter(func.lower(QuestionFamily.canonical_name) == family_name.lower())

    if repetition_type:
        query = query.join(Question.memberships).filter(func.lower(QuestionFamilyMembership.match_type) == repetition_type.lower())

    # Deterministic chronological order: latest year first, then highest marks
    questions = (
        query.order_by(Exam.year.desc().nullslast(), Question.marks.desc().nullslast(), Question.id.asc())
        .limit(limit)
        .all()
    )

    formatted_questions = []
    for q in questions:
        exam = q.section.exam if q.section else None
        family = q.family if hasattr(q, "family") else None
        membership = q.memberships[0] if getattr(q, "memberships", None) else None
        topics = [t.name for t in q.topics] if getattr(q, "topics", None) else []

        family_history = []
        if family and hasattr(family, "questions") and family.questions:
            family_history = sorted(list({
                q_m.section.exam.year
                for q_m in family.questions
                if q_m.section and q_m.section.exam and q_m.section.exam.year
            }))

        source_doc_title = exam.document.title if (exam and exam.document) else None
        source_doc_url = exam.document.original_url if (exam and exam.document) else None

        formatted_questions.append({
            "id": q.id,
            "question_number": q.question_number,
            "original_text": q.original_text,
            "normalized_text": q.normalized_text,
            "marks": q.marks,
            "is_alternative": q.is_alternative,
            "difficulty": q.difficulty,
            "question_type": q.question_type,
            "cognitive_level": q.cognitive_level,
            "exam_id": exam.id if exam else None,
            "year": exam.year if exam else None,
            "assessment_type": exam.assessment_type if exam else None,
            "term": exam.term if exam else None,
            "family_id": family.id if family else None,
            "family_name": family.canonical_name if family else None,
            "family_recurrence_history": family_history,
            "source_document_title": source_doc_title,
            "source_document_url": source_doc_url,
            "repetition_type": membership.match_type if membership else (family.repetition_type if family else "singleton"),
            "topics": topics,
        })

    scope = get_course_assessment_scope(course.id, norm_cycle, db=db) if (norm_cycle and norm_cycle != AssessmentCycle.ALL.value) else None

    return {
        "course_id": course.id,
        "course_name": course.name,
        "topic_filter": topic,
        "assessment_cycle": norm_cycle or "ALL",
        "assessment_component": scope.component_code if scope else (norm_cycle or "ALL"),
        "assessment_label": scope.component_label if scope else (norm_cycle or "All Assessments"),
        "assessment_type_filter": assessment_type,
        "year_filter": year,
        "total_returned": len(formatted_questions),
        "questions": formatted_questions,
    }


@router.get("/model-performance")
def get_model_performance(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Expose real chronological backtest evaluation metrics across historical exam cutoffs."""
    courses = db.query(Course).all()
    results = []
    evaluated_courses_count = 0

    for course in courses:
        # Check years with at least 2 distinct anchored years
        years = (
            db.query(Exam.year)
            .filter(Exam.course_id == course.id, Exam.year != None)
            .distinct()
            .order_by(Exam.year.asc())
            .all()
        )
        usable_years = [y[0] for y in years]
        if len(usable_years) < 2:
            continue

        evaluated_courses_count += 1
        # Evaluate each target year after the first year
        for target_year in usable_years[1:]:
            context = HistoricalContext(course_id=course.id, cutoff_year=target_year)
            repo = HistoricalRepository(db, context)

            hist_exams_orm = repo.get_historical_exams()
            if not hist_exams_orm:
                continue

            hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)
            analyzer = DNAAnalyzerService()
            dna = analyzer.analyze(hist_exams_dicts)

            target_exams_orm = repo.get_target_exams()
            target_topics: Dict[str, Dict[str, Any]] = {}
            for exam in target_exams_orm:
                for sec in exam.sections:
                    for q in sec.questions:
                        m = q.marks or 0.0
                        for top in q.topics:
                            t = target_topics.setdefault(top.name, {"name": top.name, "count": 0, "marks": 0.0})
                            t["count"] += 1
                            if not q.is_alternative:
                                t["marks"] += m

            target_items = list(target_topics.values())
            if not target_items:
                continue

            # Evaluate model variants
            models = {
                "ExamScopeCombined": ExamScopeCombinedModel(dna),
                "AllTimeFrequency": AllTimeFrequencyBaseline(dna),
                "RecentFrequency": RecentFrequencyBaseline(dna),
                "RecencyWeighted": RecencyWeightedBaseline(dna),
                "MarksWeighted": MarksWeightedBaseline(dna),
            }

            for model_name, model in models.items():
                preds = model.predict(PredictionTarget.TOPIC)
                metrics = BacktestEvaluator.evaluate(preds, target_items, k_values=[3, 5, 10])
                results.append({
                    "course_id": course.id,
                    "course_name": course.name,
                    "target_year": target_year,
                    "model": model_name,
                    "cutoff_year": target_year,
                    "historical_papers_used": len(hist_exams_orm),
                    "target_papers_evaluated": len(target_exams_orm),
                    "metrics": metrics,
                })

    all_exam_years = [
        y[0] for y in db.query(Exam.year).filter(Exam.year != None).distinct().order_by(Exam.year.asc()).all()
    ]
    corpus_period = f"{min(all_exam_years)}-{max(all_exam_years)}" if all_exam_years else "N/A"

    return {
        "status": "COMPLETED",
        "evaluated_courses_count": evaluated_courses_count,
        "total_evaluations": len(results),
        "methodology": "Chronological backtesting with strict temporal cutoff. Only exams prior to cutoff year were provided to models.",
        "evaluation_rules": "Strict temporal isolation: Exam.year >= cutoff_year is inaccessible to models. Unknown-year data is excluded.",
        "corpus_period": corpus_period,
        "model_version": MODEL_VERSION,
        "engine_version": ENGINE_VERSION,
        "corpus_version": CORPUS_VERSION,
        "evaluations": results,
    }


@router.get("/corpus-health")
def get_corpus_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Admin and observability health summary of the corpus and ingestion pipeline."""
    courses_count = db.query(func.count(Course.id)).scalar() or 0
    exams_count = db.query(func.count(Exam.id)).scalar() or 0
    questions_count = db.query(func.count(Question.id)).scalar() or 0
    topics_count = db.query(func.count(Topic.id)).scalar() or 0
    concepts_count = db.query(func.count(Concept.id)).scalar() or 0
    families_count = db.query(func.count(QuestionFamily.id)).scalar() or 0
    family_memberships_count = db.query(func.count(QuestionFamilyMembership.id)).scalar() or 0
    study_evidence_count = db.query(func.count(StudyEvidence.id)).scalar() or 0
    documents_count = db.query(func.count(Document.id)).scalar() or 0

    # Curriculum mapping status breakdown
    mapping_stats = (
        db.query(CurriculumMapping.status, func.count(CurriculumMapping.id))
        .group_by(CurriculumMapping.status)
        .all()
    )
    status_counts = {r[0]: r[1] for r in mapping_stats}

    # Unresolved question classification count
    unresolved_questions = (
        db.query(func.count(Question.id))
        .filter((Question.needs_review == True) | (Question.classification_confidence < 0.5))
        .scalar() or 0
    )

    # Document extraction breakdown
    doc_status_rows = (
        db.query(Document.extraction_status, func.count(Document.id))
        .group_by(Document.extraction_status)
        .all()
    )
    doc_status_breakdown = {r[0]: r[1] for r in doc_status_rows}
    extraction_failures = doc_status_breakdown.get("FAILED", 0)
    extraction_successes = doc_status_breakdown.get("COMPLETED", 0) + doc_status_breakdown.get("SUCCESS", 0)

    return {
        "status": "HEALTHY",
        "model_version": MODEL_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "engine_version": ENGINE_VERSION,
        "corpus_version": CORPUS_VERSION,
        "generated_at": datetime.utcnow().isoformat(),
        "corpus_entities": {
            "courses": courses_count,
            "exams": exams_count,
            "questions": questions_count,
            "topics": topics_count,
            "concepts": concepts_count,
            "question_families": families_count,
            "family_memberships": family_memberships_count,
            "study_evidences": study_evidence_count,
            "documents": documents_count,
        },
        "ingestion_health": {
            "documents_total": documents_count,
            "extraction_successes": extraction_successes,
            "extraction_failures": extraction_failures,
            "unresolved_question_classifications": unresolved_questions,
        },
        "curriculum_mappings": {
            "total": sum(status_counts.values()),
            "matched": status_counts.get("MATCHED", 0),
            "ambiguous": status_counts.get("AMBIGUOUS", 0),
            "unmatched": status_counts.get("UNMATCHED", 0),
        },
        "data_quality": {
            "unresolved_classifications": unresolved_questions,
            "documents_by_extraction_status": doc_status_breakdown,
        },
    }


@router.get("/{course_id}")
def get_intelligence_snapshot(
    course_id: str,
    target_year: Optional[int] = Query(None),
    target_exam_date: Optional[str] = Query(None),
    student_id: str = Query("anonymous"),
    assessment_cycle: Optional[str] = Query(None),
    cycle: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    track: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Unified academic intelligence snapshot endpoint.
    Orchestrates course metadata, ExamDNA sample size, chronological history,
    explainable predictions, study priorities, coverage, and exam schedules.
    """
    t_start = time.time()
    if not isinstance(target_year, int):
        target_year = None
    if not isinstance(target_exam_date, str):
        target_exam_date = None
    if not isinstance(student_id, str) or hasattr(student_id, "default"):
        student_id = "anonymous"
    clean_student_id = student_id.strip() if isinstance(student_id, str) and student_id.strip() else "anonymous"
    if not isinstance(assessment_cycle, str) or hasattr(assessment_cycle, "default"):
        assessment_cycle = None
    if not assessment_cycle and isinstance(cycle, str) and not hasattr(cycle, "default"):
        assessment_cycle = cycle.strip() or None
    if not isinstance(language, str) or hasattr(language, "default"):
        language = None
    if not language and isinstance(track, str) and not hasattr(track, "default"):
        language = track.strip() or None

    norm_cycle = normalize_assessment_cycle(assessment_cycle)
    is_cache_eligible = (clean_student_id == "anonymous" and target_year is None and target_exam_date is None)
    if is_cache_eligible:
        try:
            cached_snapshot = IntelligenceCacheService.get_snapshot(
                db, course_id, norm_cycle, language
            )
            if cached_snapshot:
                res = copy.deepcopy(cached_snapshot)
                if "metadata" in res and isinstance(res["metadata"], dict):
                    res["metadata"]["latency_ms"] = round((time.time() - t_start) * 1000, 2)
                    res["metadata"]["cache_hit"] = True
                logger.info(
                    "Intelligence snapshot served from cache: course_id=%s, cycle=%s, latency_ms=%.2f",
                    course_id, norm_cycle, (time.time() - t_start) * 1000
                )
                return res
        except Exception as cache_err:
            logger.warning("Safe cache fallback on error for course_id=%s: %s", course_id, cache_err)

    course = _find_course(db, course_id)

    # If course is not directly resolved, check if course_id matches curriculum_mapping
    curriculum_row = None
    if not course:
        curriculum_row = (
            db.query(CurriculumMapping)
            .filter(
                (CurriculumMapping.curriculum_id == course_id) |
                (func.lower(CurriculumMapping.subject_name) == course_id.lower())
            )
            .first()
        )
        if curriculum_row and curriculum_row.course_id:
            course = db.query(Course).filter(Course.id == curriculum_row.course_id).first()

    # Determine canonical curriculum context if course exists
    if course and not curriculum_row:
        curriculum_row = (
            db.query(CurriculumMapping)
            .filter(CurriculumMapping.course_id == course.id)
            .first()
        )

    # Track resolution for multi-track courses (e.g. Foreign Languages course_id=8)
    active_track = None
    if course and course.tracks:
        if not (isinstance(language, str) and language.strip()):
            raise HTTPException(
                status_code=400,
                detail="TRACK_SELECTION_REQUIRED: This course has multiple tracks (e.g. languages). A specific track must be selected.",
            )

        lang_low = language.strip().lower()
        active_track = next(
            (t for t in course.tracks if t.track_key.lower() == lang_low or t.track_name.lower() == lang_low or str(t.id) == lang_low),
            None
        )
        if not active_track:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language track '{language}' for course '{course.name}'. Available: {[t.track_key for t in course.tracks]}"
            )

    # Secondary persistent cache check: if request used a slug/code alias (e.g. 'calculus')
    # and memory cache was cleared (process restart), check DB under canonical course.id
    if is_cache_eligible and course and str(course_id).lower().strip() != str(course.id):
        track_param = active_track.track_key if active_track else language
        try:
            cached_canonical = IntelligenceCacheService.get_snapshot(
                db, course.id, norm_cycle, track_param
            )
            if cached_canonical:
                IntelligenceCacheService.alias_memory_cache(
                    course_id, norm_cycle, track_param, cached_canonical
                )
                res = copy.deepcopy(cached_canonical)
                if "metadata" in res and isinstance(res["metadata"], dict):
                    res["metadata"]["latency_ms"] = round((time.time() - t_start) * 1000, 2)
                    res["metadata"]["cache_hit"] = True
                logger.info(
                    "Intelligence snapshot served from secondary persistent cache: slug=%s -> course_id=%s, latency_ms=%.2f",
                    course_id, course.id, (time.time() - t_start) * 1000
                )
                return res
        except Exception as cache_err:
            logger.warning("Safe secondary persistent cache fallback on error for course_id=%s: %s", course.id, cache_err)

    # 1. Handle AMBIGUOUS State
    if curriculum_row and curriculum_row.status == "AMBIGUOUS":
        logger.info(
            "Intelligence snapshot resolved: course_id=%s, status=AMBIGUOUS, latency_ms=%.2f",
            course_id, (time.time() - t_start) * 1000
        )
        return {
            "data_availability_status": "AMBIGUOUS",
            "course": None,
            "curriculum": {
                "curriculum_id": curriculum_row.curriculum_id,
                "subject_name": curriculum_row.subject_name,
                "branch_name": curriculum_row.branch_name,
                "semester": curriculum_row.semester,
                "credits": curriculum_row.credits,
                "status": "AMBIGUOUS",
                "notes": curriculum_row.notes or "General subject with multiple academic syllabus options.",
            },
            "message": "This subject has multiple syllabus variants and cannot synthesize a deterministic forecast.",
            "predictions": [],
            "study_priorities": [],
            "coverage_summary": None,
            "metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.utcnow().isoformat(),
            }
        }

    # 2. Handle UNMATCHED State
    if (curriculum_row and curriculum_row.status == "UNMATCHED") or not course:
        subject_name = curriculum_row.subject_name if curriculum_row else course_id
        logger.info(
            "Intelligence snapshot resolved: course_id=%s, status=UNMATCHED, latency_ms=%.2f",
            course_id, (time.time() - t_start) * 1000
        )
        return {
            "data_availability_status": "UNMATCHED",
            "course": None,
            "curriculum": {
                "curriculum_id": curriculum_row.curriculum_id if curriculum_row else course_id,
                "subject_name": subject_name,
                "branch_name": curriculum_row.branch_name if curriculum_row else None,
                "semester": curriculum_row.semester if curriculum_row else None,
                "credits": curriculum_row.credits if curriculum_row else 3,
                "status": "UNMATCHED",
                "notes": "No historical examination papers indexed in registry.",
            },
            "message": f"Historical examination papers have not been indexed for '{subject_name}' yet.",
            "predictions": [],
            "study_priorities": [],
            "coverage_summary": None,
            "metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.utcnow().isoformat(),
            }
        }

    # 3. Course exists: inspect examination history
    exam_query = db.query(Exam).filter(Exam.course_id == course.id)
    if active_track:
        exam_query = exam_query.filter(Exam.track_id == active_track.id)
    exam_rows = exam_query.order_by(Exam.year.asc().nullslast()).all()
    total_papers = len(exam_rows)

    if total_papers == 0:
        logger.info(
            "Intelligence snapshot resolved: course_id=%s, status=CATALOG_ONLY, latency_ms=%.2f",
            course_id, (time.time() - t_start) * 1000
        )
        catalog_payload = {
            "data_availability_status": "CATALOG_ONLY",
            "course": {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "canonical_code": course.canonical_code,
                "department": course.department,
                "regulation_year": course.regulation_year,
            },
            "curriculum": {
                "curriculum_id": curriculum_row.curriculum_id if curriculum_row else None,
                "subject_name": curriculum_row.subject_name if curriculum_row else course.name,
                "branch_name": curriculum_row.branch_name if curriculum_row else None,
                "semester": curriculum_row.semester if curriculum_row else None,
                "credits": curriculum_row.credits if curriculum_row else 3,
                "status": "MATCHED",
                "notes": "Verified course in catalog; awaiting historical paper upload.",
            },
            "exam_history": {
                "total_papers": 0,
                "total_questions": 0,
                "years": [],
                "available_assessment_types": [],
            },
            "available_assessment_types": [],
            "message": f"'{course.name}' is verified in academic registry, but 0 historical exam papers exist.",
            "predictions": [],
            "study_priorities": [],
            "coverage_summary": None,
            "metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.utcnow().isoformat(),
            }
        }
        if is_cache_eligible and course:
            IntelligenceCacheService.store_snapshot(
                db=db,
                course_id=course.id,
                assessment_cycle=norm_cycle,
                track_id=active_track.id if active_track else None,
                payload=catalog_payload,
                identifier=course_id,
                track_key=active_track.track_key if active_track else None,
            )
        return catalog_payload

    # 4. Target year and assessment cycle resolution

    # Detect available assessment cycles across all exams for this course
    cycles_found = set()
    for e in exam_rows:
        c = normalize_assessment_cycle(e.assessment_type)
        if c and c in [AssessmentCycle.CT1.value, AssessmentCycle.CT2.value, AssessmentCycle.ENDSEM.value]:
            cycles_found.add(c)
    available_cycles = ["ALL"]
    for c in ["CT1", "CT2", "ENDSEM"]:
        if c in cycles_found:
            available_cycles.append(c)

    if target_year is None:
        max_year = max([e.year for e in exam_rows if e.year is not None], default=None)
        target_year = (max_year + 1) if max_year else 2024

    context = HistoricalContext(
        course_id=course.id,
        cutoff_year=target_year,
        assessment_cycle=norm_cycle,
        track_id=active_track.id if active_track else None
    )
    repo = HistoricalRepository(db, context)
    hist_exams_orm = repo.get_historical_exams()

    if not hist_exams_orm:
        logger.info(
            "Intelligence snapshot resolved: course_id=%s, assessment_cycle=%s, status=INSUFFICIENT_EVIDENCE, latency_ms=%.2f",
            course_id, norm_cycle, (time.time() - t_start) * 1000
        )
        scope = get_course_assessment_scope(
            course.id,
            norm_cycle,
            db=db,
            track_id=active_track.id if active_track else None
        )
        unobserved_in_scope = (
            [
                {
                    "name": name,
                    "status": "UNOBSERVED_IN_SCOPE",
                    "message": "In syllabus scope, but no historical evidence available",
                }
                for name in sorted(list(scope.in_scope_topic_names))
            ]
            if (not scope.is_all and scope.in_scope_topic_names)
            else []
        )
        assessment_scope_payload = {
            "student_cycle": norm_cycle or "ALL",
            "component_code": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "component_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "student_label": scope.student_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "role": scope.role,
            "marks": scope.marks,
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "source_document": scope.source_document,
            "unit_numbers": sorted(list(scope.in_scope_unit_numbers)),
            "total_in_scope_topics": len(scope.in_scope_topic_names),
            "observed_in_scope_topics": 0,
            "unobserved_in_scope_topics": unobserved_in_scope,
            "out_of_scope_observed_topics": [],
        }
        msg = f"Insufficient historical examination papers prior to cutoff year for '{course.name}'."
        if norm_cycle and norm_cycle != AssessmentCycle.ALL.value:
            msg = f"Insufficient historical examination papers prior to cutoff year for '{course.name}' under assessment cycle '{norm_cycle}'."
        insufficient_payload = {
            "data_availability_status": "INSUFFICIENT_EVIDENCE",
            "course": {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "canonical_code": course.canonical_code,
                "department": course.department,
                "regulation_year": course.regulation_year,
            },
            "curriculum": {
                "curriculum_id": curriculum_row.curriculum_id if curriculum_row else None,
                "subject_name": curriculum_row.subject_name if curriculum_row else course.name,
                "branch_name": curriculum_row.branch_name if curriculum_row else None,
                "semester": curriculum_row.semester if curriculum_row else None,
                "credits": curriculum_row.credits if curriculum_row else 3,
                "status": "MATCHED",
                "notes": f"No historical exams found prior to target cutoff year for assessment cycle '{norm_cycle or 'ALL'}'.",
            },
            "exam_history": {
                "total_papers": 0,
                "historical_papers_analyzed": 0,
                "total_questions": 0,
                "years": [],
                "available_assessment_types": sorted(list({e.assessment_type for e in exam_rows if e.assessment_type})),
                "available_assessment_cycles": available_cycles,
                "assessment_cycle": norm_cycle or "ALL",
            },
            "available_assessment_types": sorted(list({e.assessment_type for e in exam_rows if e.assessment_type})),
            "available_assessment_cycles": available_cycles,
            "assessment_cycle": norm_cycle or "ALL",
            "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "assessment_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "assessment_scope": assessment_scope_payload,
            "message": msg,
            "predictions": [],
            "study_priorities": [],
            "coverage_summary": None,
            "metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.utcnow().isoformat(),
            }
        }
        if is_cache_eligible and course:
            IntelligenceCacheService.store_snapshot(
                db=db,
                course_id=course.id,
                assessment_cycle=norm_cycle,
                track_id=active_track.id if active_track else None,
                payload=insufficient_payload,
                identifier=course_id,
                track_key=active_track.track_key if active_track else None,
            )
        return insufficient_payload

    # 5. Build DNA and Predictions
    hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)
    analyzer = DNAAnalyzerService()
    dna = analyzer.analyze(hist_exams_dicts)

    total_q_count = dna.sample_size.questions if hasattr(dna, "sample_size") else 0
    sufficiency = getattr(dna.sample_size, "sufficiency", DataSufficiency.LIMITED)

    engine = ExamScopeCombinedModel(dna)
    all_topic_preds = engine.predict(PredictionTarget.TOPIC)
    family_preds = engine.predict(PredictionTarget.FAMILY)

    # Resolve course-specific assessment plan scope & candidate restriction
    scope = get_course_assessment_scope(
        course.id,
        norm_cycle,
        db=db,
        track_id=active_track.id if active_track else None
    )
    
    if not scope.is_all and scope.in_scope_topic_names:
        topic_preds = [p for p in all_topic_preds if p.name in scope.in_scope_topic_names]
        out_of_scope_preds = [p for p in all_topic_preds if p.name not in scope.in_scope_topic_names]
    else:
        topic_preds = all_topic_preds
        out_of_scope_preds = []

    unobserved_in_scope = (
        [
            {
                "name": name,
                "status": "UNOBSERVED_IN_SCOPE",
                "message": "In syllabus scope, but no historical evidence available",
            }
            for name in sorted(list(scope.in_scope_topic_names - {p.name for p in topic_preds}))
        ]
        if (not scope.is_all and scope.in_scope_topic_names)
        else []
    )
    assessment_scope_payload = {
        "student_cycle": norm_cycle or "ALL",
        "component_code": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
        "component_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
        "student_label": scope.student_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
        "role": scope.role,
        "marks": scope.marks,
        "evidence_status": scope.evidence_status,
        "intended_scope": scope.intended_scope,
        "observed_scope": scope.observed_scope,
        "source_document": scope.source_document,
        "unit_numbers": sorted(list(scope.in_scope_unit_numbers)),
        "total_in_scope_topics": len(scope.in_scope_topic_names),
        "observed_in_scope_topics": len(topic_preds) if (not scope.is_all and scope.in_scope_topic_names) else len(all_topic_preds),
        "unobserved_in_scope_topics": unobserved_in_scope,
        "out_of_scope_observed_topics": [
            {
                "name": p.name,
                "status": "OUT_OF_SCOPE_OBSERVED",
                "score": round(float(p.score or 0.0), 4),
                "message": "Observed on historical examination papers despite being outside intended syllabus plan.",
            }
            for p in out_of_scope_preds
        ],
    }

    # 6. Generate Study Priorities & Coverage
    study_service = StudyIntelligenceService(db)
    study_service.preload_course_resources(course.id)
    study_service.preload_student_progress(course.id, clean_student_id)

    priorities_objs = [
        study_service.calculate_study_priority(p, course.id, clean_student_id)
        for p in topic_preds if getattr(p, "target", "topic") == "topic"
    ]
    study_plan = study_service.generate_study_plan(topic_preds, course.id, clean_student_id, priorities=priorities_objs)
    family_plan = []
    if not study_plan and family_preds:
        for index, item in enumerate(family_preds[:5], start=1):
            p_dict = item.to_dict()
            fam_id = item.family_id
            score = float(item.score or 0.0)
            p_cnt = item.distinct_paper_count or 1
            occ = item.evidence.get("occurrences", 1) if isinstance(item.evidence, dict) else 1
            years = item.observed_years or []
            years_str = f" ({', '.join(map(str, sorted(years)))})" if years else ""
            rep_type = item.repetition_type or "family_repeat"
            rep_label = "Exact verbatim repeat" if rep_type == "exact_repeat" else "Recurring question family"
            priority_band = "HIGH" if score >= 0.5 or occ >= 3 else "MEDIUM"

            # Personalize family status and priority based on student progress on associated topic
            student_status = "NOT_STARTED"
            practice_accuracy = None
            resolved_topic = None
            if fam_id and course:
                resolved_topic = study_service.resolve_family_to_topic(fam_id, course.id)

            if resolved_topic and clean_student_id != "anonymous":
                prog = None
                if study_service._student_progress_by_topic_id is not None:
                    prog = study_service._student_progress_by_topic_id.get(resolved_topic.id)
                if not prog:
                    prog = db.query(StudentTopicProgress).filter_by(
                        student_id=clean_student_id, topic_id=resolved_topic.id
                    ).first()
                if prog:
                    student_status = prog.status
                    if prog.practice_attempted:
                        practice_accuracy = round((prog.practice_correct or 0) / prog.practice_attempted, 2)

            reasons = [
                f"{rep_label} observed across {p_cnt} examination papers{years_str}.",
                f"Verified historical frequency: {occ} questions examined.",
            ]
            if student_status == "COMPLETED" and (practice_accuracy is None or practice_accuracy >= 0.8):
                reasons.append("Topic completed with high mastery (>= 80%); deprioritized for active study.")
                if priority_band == "VERY_HIGH":
                    priority_band = "HIGH"
                elif priority_band == "HIGH":
                    priority_band = "MEDIUM"
                elif priority_band == "MEDIUM":
                    priority_band = "LOW"
            elif student_status in {"STARTED", "IN_PROGRESS"}:
                reasons.append("In progress: student has begun practicing questions in this topic.")

            family_plan.append({
                "topic": item.name,
                "name": item.name,
                "category": "family",
                "family_id": fam_id,
                "topic_id": resolved_topic.id if resolved_topic else None,
                "prediction_score": round(score, 4),
                "probability": round(float(p_dict.get("probability", score)), 4),
                "confidence": item.confidence or "MEDIUM",
                "priority": priority_band,
                "repetition_type": rep_type,
                "distinct_paper_count": p_cnt,
                "historical_occurrences": occ,
                "observed_years": years,
                "reason": f"{rep_label}: appeared across {p_cnt} past examination papers{years_str} with {occ} total occurrences.",
                "reasons": reasons,
                "resources": [
                    {
                        "id": f"fam-{fam_id}" if fam_id else f"res-{index}",
                        "title": f"Past Exam Questions (Family #{fam_id})" if fam_id else "Past Exam Questions",
                        "source": "pyq",
                        "resource_type": "family_questions",
                        "family_id": fam_id,
                        "question_count": occ,
                    }
                ],
                "student_status": student_status,
                "practice_accuracy": practice_accuracy,
            })
        study_plan = family_plan

    if topic_preds:
        coverage_summary = study_service.calculate_coverage_gap(topic_preds, course.id, clean_student_id, priorities=priorities_objs)
    elif family_plan:
        total_predicted = len(family_plan)
        mastered = sum(1 for f in family_plan if f.get("student_status") == "COMPLETED")
        in_prog = sum(1 for f in family_plan if f.get("student_status") in {"STARTED", "IN_PROGRESS"})
        unstudied = sum(1 for f in family_plan if f.get("student_status") == "NOT_STARTED")
        gap_topics = [f["name"] for f in family_plan if f.get("priority") in {"VERY_HIGH", "HIGH"} and f.get("student_status") != "COMPLETED"]
        coverage_pct = round(((mastered + 0.5 * in_prog) / total_predicted) * 100.0, 1) if total_predicted > 0 else 0.0
        coverage_summary = {
            "total_predicted_topics": total_predicted,
            "mastered_topics": mastered,
            "in_progress_topics": in_prog,
            "unstudied_topics": unstudied,
            "student_preparation_coverage": coverage_pct,
            "coverage_gap_topics": gap_topics,
            "high_priority_gap_count": len(gap_topics),
            "mastered_topic_count": mastered,
            "in_progress_count": in_prog,
            "unstudied_count": unstudied,
        }
    else:
        coverage_summary = None

    # 7. Exam Schedule if date provided
    exam_schedule = study_service.generate_exam_schedule(priorities_objs, target_exam_date)

    available_assessment_types = sorted(list({
        e.assessment_type for e in exam_rows if e.assessment_type
    }))

    all_years = sorted(list({e.year for e in exam_rows if e.year}))
    cycle_years = sorted(list({e.year for e in hist_exams_orm if e.year is not None}))
    cycle_papers_count = len(hist_exams_orm)

    topic_predictions_payload = []
    for p in topic_preds[:10]:
        p_dict = p.to_dict()
        t_obj = study_service.get_topic_by_name(p.name, course.id)
        if t_obj:
            p_dict["topic_id"] = t_obj.id
        topic_years = {
            e.year for e in hist_exams_orm
            if e.year is not None and any(
                any(t.name == p.name for t in q.topics)
                for s in e.sections for q in s.questions
            )
        }
        p_dict["timeline"] = [
            {
                "year": y,
                "exam_exists": True,
                "topic_present": y in topic_years,
                "family_present": False,
                "present": y in topic_years,
                "status": "TOPIC_PRESENT" if (y in topic_years) else "TOPIC_ABSENT",
            }
            for y in (cycle_years if cycle_years else all_years)
        ]
        p_dict["historical_years"] = sorted(list(topic_years))
        topic_predictions_payload.append(p_dict)

    family_predictions_payload = []
    missing_fam_names = [p.name for p in family_preds[:5] if not p.family_id]
    fam_recs_map = {}
    if missing_fam_names:
        fam_recs = db.query(QuestionFamily.canonical_name, QuestionFamily.id, QuestionFamily.repetition_type).filter(QuestionFamily.canonical_name.in_(missing_fam_names)).all()
        fam_recs_map = {r[0]: (r[1], r[2]) for r in fam_recs}

    for p in family_preds[:5]:
        p_dict = p.to_dict()

        # Deterministic family lookup to ensure stable family_id and repetition_type
        fam_id = p.family_id
        fam_repetition_type = p.repetition_type
        if not fam_id:
            fam_rec = fam_recs_map.get(p.name)
            if fam_rec:
                fam_id = fam_rec[0]
                if not fam_repetition_type:
                    fam_repetition_type = fam_rec[1]

        # Distinct paper IDs where this family appeared in this course
        fam_exams = {
            e.id for e in hist_exams_orm
            if any(
                (q.family_id == fam_id if fam_id else (q.family and q.family.canonical_name == p.name))
                for s in e.sections for q in s.questions
            )
        }
        distinct_papers = len(fam_exams) if fam_exams else (p.distinct_paper_count or 1)

        # Observed years
        fam_years = {
            e.year for e in hist_exams_orm
            if e.year is not None and e.id in fam_exams
        }
        if not fam_years:
            fam_years = {
                e.year for e in hist_exams_orm
                if e.year is not None and any(
                    q.family and q.family.canonical_name == p.name
                    for s in e.sections for q in s.questions
                )
            }

        p_dict["family_id"] = fam_id
        p_dict["repetition_type"] = fam_repetition_type or p_dict.get("repetition_type") or "singleton"
        p_dict["distinct_paper_count"] = distinct_papers
        p_dict["papers_with_family"] = distinct_papers
        p_dict["papers_with_topic"] = distinct_papers
        p_dict["papers_analyzed"] = cycle_papers_count
        p_dict["paper_coverage"] = round(distinct_papers / cycle_papers_count, 4) if cycle_papers_count > 0 else 0.0
        p_dict["observed_years"] = sorted(list(fam_years))
        p_dict["historical_years"] = sorted(list(fam_years))
        p_dict["timeline"] = [
            {
                "year": y,
                "exam_exists": True,
                "topic_present": False,
                "family_present": y in fam_years,
                "present": y in fam_years,
                "status": "FAMILY_PRESENT" if (y in fam_years) else "FAMILY_ABSENT",
            }
            for y in (cycle_years if cycle_years else all_years)
        ]
        family_predictions_payload.append(p_dict)

    if active_track:
        syl_ids = [s.id for s in course.syllabuses if s.track_id == active_track.id]
        taxonomy_topic_count = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.syllabus_id.in_(syl_ids))
            .count()
            if syl_ids else 0
        )
    else:
        taxonomy_topic_count = len(study_service._course_topics)
    has_topic_taxonomy = taxonomy_topic_count > 0

    if has_topic_taxonomy and len(topic_preds) > 0:
        prediction_mode = "topic"
    elif len(family_preds) > 0:
        prediction_mode = "family"
    else:
        prediction_mode = "insufficient"

    predictions_payload = topic_predictions_payload if prediction_mode == "topic" else family_predictions_payload

    all_span_years = list(range(cycle_years[0], cycle_years[-1] + 1)) if cycle_years else []
    gap_years = [y for y in all_span_years if y not in cycle_years]

    availability_status = "READY"
    if sufficiency == DataSufficiency.INSUFFICIENT:
        availability_status = "INSUFFICIENT_EVIDENCE"

    snapshot_payload = {
        "data_availability_status": availability_status,
        "prediction_mode": prediction_mode,
        "has_topic_taxonomy": has_topic_taxonomy,
        "taxonomy_topic_count": taxonomy_topic_count,
        "topic_predictions_count": len(topic_preds),
        "family_predictions_count": len(family_preds),
        "track": {
            "id": active_track.id,
            "key": active_track.track_key,
            "track_key": active_track.track_key,
            "name": active_track.track_name,
            "track_name": active_track.track_name,
            "code": active_track.track_code,
            "track_code": active_track.track_code,
            "track_type": active_track.track_type,
        } if active_track else None,
        "tracks": [
            {
                "id": t.id,
                "key": t.track_key,
                "track_key": t.track_key,
                "name": t.track_name,
                "track_name": t.track_name,
                "code": t.track_code,
                "track_code": t.track_code,
                "track_type": t.track_type,
            }
            for t in sorted(course.tracks, key=lambda x: x.id)
        ] if course.tracks else [],
        "course": {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "canonical_code": course.canonical_code,
            "department": course.department,
            "regulation_year": course.regulation_year,
            "has_tracks": bool(course.tracks),
            "tracks": [
                {
                    "id": t.id,
                    "key": t.track_key,
                    "track_key": t.track_key,
                    "name": t.track_name,
                    "track_name": t.track_name,
                    "code": t.track_code,
                    "track_code": t.track_code,
                    "track_type": t.track_type,
                }
                for t in sorted(course.tracks, key=lambda x: x.id)
            ] if course.tracks else [],
        },
        "curriculum": {
            "curriculum_id": curriculum_row.curriculum_id if curriculum_row else None,
            "subject_name": curriculum_row.subject_name if curriculum_row else course.name,
            "branch_name": curriculum_row.branch_name if curriculum_row else None,
            "semester": curriculum_row.semester if curriculum_row else None,
            "credits": curriculum_row.credits if curriculum_row else 3,
            "status": "MATCHED",
            "notes": None,
        },
        "exam_history": {
            "total_papers": cycle_papers_count if (norm_cycle and norm_cycle != AssessmentCycle.ALL.value) else total_papers,
            "all_course_papers": total_papers,
            "historical_papers_analyzed": cycle_papers_count,
            "total_questions": total_q_count,
            "years": cycle_years if (norm_cycle and norm_cycle != AssessmentCycle.ALL.value) else all_years,
            "observed_years": cycle_years if (norm_cycle and norm_cycle != AssessmentCycle.ALL.value) else all_years,
            "unobserved_years": gap_years,
            "gap_years": gap_years,
            "available_assessment_types": available_assessment_types,
            "available_assessment_cycles": available_cycles,
            "assessment_cycle": norm_cycle or "ALL",
            "target_year": target_year,
        },
        "available_assessment_types": available_assessment_types,
        "available_assessment_cycles": available_cycles,
        "assessment_cycle": norm_cycle or "ALL",
        "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
        "assessment_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
        "evidence_status": scope.evidence_status,
        "intended_scope": scope.intended_scope,
        "observed_scope": scope.observed_scope,
        "assessment_scope": assessment_scope_payload,
        "predictions": predictions_payload,
        "topic_predictions": topic_predictions_payload,
        "family_predictions": family_predictions_payload,
        "study_priorities": study_plan,
        "coverage_summary": coverage_summary,
        "exam_schedule": exam_schedule,
        "metadata": {
            "model_version": MODEL_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "engine_version": ENGINE_VERSION,
            "corpus_version": CORPUS_VERSION,
            "calibration_method": CALIBRATION_METHOD,
            "score_semantics": SCORE_SEMANTICS,
            "sufficiency": sufficiency.value if hasattr(sufficiency, "value") else str(sufficiency),
            "generated_at": datetime.utcnow().isoformat(),
            "latency_ms": round((time.time() - t_start) * 1000, 2),
        }
    }

    if is_cache_eligible and course:
        IntelligenceCacheService.store_snapshot(
            db=db,
            course_id=course.id,
            assessment_cycle=norm_cycle,
            track_id=active_track.id if active_track else None,
            payload=snapshot_payload,
            identifier=course_id,
            track_key=active_track.track_key if active_track else None,
        )

    return snapshot_payload
