from typing import Any, Dict, List, Optional
from datetime import datetime
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

logger = logging.getLogger("markmint.intelligence")

router = APIRouter()


@router.get("/{course_id}/questions")
def get_course_historical_questions(
    course_id: str,
    topic: Optional[str] = Query(None),
    assessment_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    min_marks: Optional[float] = Query(None),
    max_marks: Optional[float] = Query(None),
    family_id: Optional[int] = Query(None),
    repetition_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Expose verified historical examination questions chronologically for a course and optional topic."""
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
    )

    if topic:
        query = query.join(Question.topics).filter(func.lower(Topic.name) == topic.lower())

    if assessment_type:
        query = query.filter(func.lower(Exam.assessment_type) == assessment_type.lower())

    if year is not None:
        query = query.filter(Exam.year == year)

    if min_marks is not None:
        query = query.filter(Question.marks >= min_marks)

    if max_marks is not None:
        query = query.filter(Question.marks <= max_marks)

    if family_id is not None:
        query = query.filter(Question.family_id == family_id)

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

    return {
        "course_id": course.id,
        "course_name": course.name,
        "topic_filter": topic,
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
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Unified academic intelligence snapshot endpoint.
    Orchestrates course metadata, ExamDNA sample size, chronological history,
    explainable predictions, study priorities, coverage, and exam schedules.
    """
    t_start = time.time()
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
    exam_rows = (
        db.query(Exam)
        .filter(Exam.course_id == course.id)
        .order_by(Exam.year.asc().nullslast())
        .all()
    )
    total_papers = len(exam_rows)

    if total_papers == 0:
        logger.info(
            "Intelligence snapshot resolved: course_id=%s, status=CATALOG_ONLY, latency_ms=%.2f",
            course_id, (time.time() - t_start) * 1000
        )
        return {
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

    # 4. Target year resolution
    if target_year is None:
        max_year = max([e.year for e in exam_rows if e.year is not None], default=None)
        target_year = (max_year + 1) if max_year else 2024

    context = HistoricalContext(course_id=course.id, cutoff_year=target_year)
    repo = HistoricalRepository(db, context)
    hist_exams_orm = repo.get_historical_exams()

    if not hist_exams_orm:
        logger.info(
            "Intelligence snapshot resolved: course_id=%s, status=INSUFFICIENT_EVIDENCE, latency_ms=%.2f",
            course_id, (time.time() - t_start) * 1000
        )
        return {
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
                "notes": "No historical exams found prior to target cutoff year.",
            },
            "exam_history": {
                "total_papers": total_papers,
                "total_questions": 0,
                "years": [e.year for e in exam_rows if e.year],
                "available_assessment_types": list({e.assessment_type for e in exam_rows if e.assessment_type}),
            },
            "available_assessment_types": list({e.assessment_type for e in exam_rows if e.assessment_type}),
            "message": "Insufficient historical data prior to cutoff year.",
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

    # 5. Build DNA and Predictions
    hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)
    analyzer = DNAAnalyzerService()
    dna = analyzer.analyze(hist_exams_dicts)

    total_q_count = dna.sample_size.questions if hasattr(dna, "sample_size") else 0
    sufficiency = getattr(dna.sample_size, "sufficiency", DataSufficiency.LIMITED)

    engine = ExamScopeCombinedModel(dna)
    topic_preds = engine.predict(PredictionTarget.TOPIC)
    family_preds = engine.predict(PredictionTarget.FAMILY)

    # 6. Generate Study Priorities & Coverage
    study_service = StudyIntelligenceService(db)
    study_plan = study_service.generate_study_plan(topic_preds, course.id, student_id)
    coverage_summary = study_service.calculate_coverage_gap(topic_preds, course.id, student_id)

    # 7. Exam Schedule if date provided
    priorities_objs = [
        study_service.calculate_study_priority(p, course.id, student_id)
        for p in topic_preds if getattr(p, "target", "topic") == "topic"
    ]
    exam_schedule = study_service.generate_exam_schedule(priorities_objs, target_exam_date)

    available_assessment_types = sorted(list({
        e.assessment_type for e in exam_rows if e.assessment_type
    }))

    all_years = sorted(list({e.year for e in exam_rows if e.year}))

    predictions_payload = []
    for p in topic_preds[:10]:
        p_dict = p.to_dict()
        t_obj = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Syllabus.course_id == course.id, Topic.name == p.name)
            .first()
        )
        if t_obj:
            p_dict["topic_id"] = t_obj.id
        topic_years = {
            e.year for e in hist_exams_orm
            if e.year is not None and any(
                q.topics and q.topics[0].name == p.name
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
            for y in all_years
        ]
        p_dict["historical_years"] = sorted(list(topic_years))
        predictions_payload.append(p_dict)

    for p in family_preds[:5]:
        p_dict = p.to_dict()
        fam_years = {
            e.year for e in hist_exams_orm
            if e.year is not None and any(
                q.family and q.family.canonical_name == p.name
                for s in e.sections for q in s.questions
            )
        }
        p_dict["timeline"] = [
            {
                "year": y,
                "exam_exists": True,
                "topic_present": False,
                "family_present": y in fam_years,
                "present": y in fam_years,
                "status": "FAMILY_PRESENT" if (y in fam_years) else "FAMILY_ABSENT",
            }
            for y in all_years
        ]
        p_dict["historical_years"] = sorted(list(fam_years))
        predictions_payload.append(p_dict)

    all_span_years = list(range(all_years[0], all_years[-1] + 1)) if all_years else []
    gap_years = [y for y in all_span_years if y not in all_years]

    availability_status = "READY"
    if sufficiency == DataSufficiency.INSUFFICIENT:
        availability_status = "INSUFFICIENT_EVIDENCE"

    snapshot_payload = {
        "data_availability_status": availability_status,
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
            "notes": None,
        },
        "exam_history": {
            "total_papers": total_papers,
            "historical_papers_analyzed": len(hist_exams_orm),
            "total_questions": total_q_count,
            "years": all_years,
            "observed_years": all_years,
            "unobserved_years": gap_years,
            "gap_years": gap_years,
            "available_assessment_types": available_assessment_types,
            "target_year": target_year,
        },
        "available_assessment_types": available_assessment_types,
        "predictions": predictions_payload,
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

    logger.info(
        "Synthesized intelligence snapshot: course_id=%s, papers=%d, questions=%d, latency_ms=%.2f, status=%s",
        course.id, len(hist_exams_orm), total_q_count, (time.time() - t_start) * 1000, availability_status
    )

    return snapshot_payload
