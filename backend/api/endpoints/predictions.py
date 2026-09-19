from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.core.database import get_db
from backend.models.core import Course, Exam, Topic, Unit, Syllabus
from backend.services.assessment_cycle import normalize_assessment_cycle, AssessmentCycle
from backend.services.assessment_plan_registry import get_course_assessment_scope
import re
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

router = APIRouter()


def _find_course(db: Session, identifier: str) -> Optional[Course]:
    """Generically resolve a course by exact name, case-insensitive name, code, canonical code, ID, or alphanumeric string."""
    if not identifier:
        return None

    # 1. Canonical code match (e.g. 21MAB101T)
    course = db.query(Course).filter(func.lower(Course.canonical_code) == identifier.lower()).first()
    if course:
        return course

    # 2. Exact or case-insensitive name match
    course = db.query(Course).filter(func.lower(Course.name) == identifier.lower()).first()
    if course:
        return course

    # 3. Case-insensitive code match (e.g. SEM1-CALC)
    course = db.query(Course).filter(func.lower(Course.code) == identifier.lower()).first()
    if course:
        return course

    # 4. Numeric ID match
    if str(identifier).isdigit():
        course = db.query(Course).filter(Course.id == int(identifier)).first()
        if course:
            return course

    # 5. Normalized alphanumeric match (ignores spaces, punctuation, case)
    norm_id = re.sub(r'[^a-zA-Z0-9]', '', str(identifier)).lower()
    if norm_id:
        all_courses = db.query(Course).all()
        for c in all_courses:
            if c.canonical_code and re.sub(r'[^a-zA-Z0-9]', '', c.canonical_code).lower() == norm_id:
                return c
            if re.sub(r'[^a-zA-Z0-9]', '', c.name).lower() == norm_id:
                return c
            if re.sub(r'[^a-zA-Z0-9]', '', c.code).lower() == norm_id:
                return c

        # 6. Prefix / substring match for course names (e.g. 'Calculus' -> 'Calculus And Linear Algebra')
        for c in all_courses:
            if norm_id in re.sub(r'[^a-zA-Z0-9]', '', c.name).lower():
                return c

    return None


find_course = _find_course
resolve_course = _find_course


def _build_historical_exam_payloads(hist_exams_orm: list[Any]) -> list[dict[str, Any]]:
    """Map ORM exams to the stable payload consumed by ExamDNA."""
    return [
        {
            "id": exam.id,
            "year": exam.year,
            "exam_type": exam.assessment_type,
            "questions": [
                {
                    "id": question.id,
                    "marks": question.marks,
                    "is_alternative": question.is_alternative,
                    "topic": question.topics[0].name if question.topics else None,
                    "topics": [t.name for t in question.topics] if getattr(question, "topics", None) else [],
                    "unit": (
                        question.topics[0].unit.name
                        if (question.topics and getattr(question.topics[0], "unit", None))
                        else None
                    ),
                    "units": (
                        list(dict.fromkeys(
                            t.unit.name for t in question.topics if getattr(t, "unit", None) and t.unit.name
                        ))
                        if getattr(question, "topics", None)
                        else []
                    ),
                    "topic_mappings": [
                        {
                            "topic": t.name,
                            "unit": t.unit.name if getattr(t, "unit", None) else None
                        }
                        for t in question.topics
                    ] if getattr(question, "topics", None) else [],
                    "question_type": question.question_type,
                    "repetition_type": (
                        question.memberships[0].match_type
                        if getattr(question, "memberships", None)
                        else "singleton"
                    ),
                    "family_id": (
                        getattr(question, "family_id", None)
                        or (getattr(getattr(question, "family", None), "id", None))
                    ),
                    "family_name": (
                        getattr(getattr(question, "family", None), "canonical_name", None)
                    ),
                    "difficulty": getattr(question, "difficulty", None),
                }
                for section in exam.sections
                for question in section.questions
            ],
        }
        for exam in hist_exams_orm
    ]

@router.get("/predictions/{subject}")
def get_prediction(
    subject: str,
    target_year: Optional[int] = Query(None),
    assessment_cycle: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        course = _find_course(db, subject)
        if not course:
            raise HTTPException(status_code=404, detail="Subject not found")

        norm_cycle = normalize_assessment_cycle(assessment_cycle)

        if hasattr(target_year, "default"):
            target_year = None

        # Determine target year dynamically if not provided.
        # Rule: Target the next unseen exam year (most_recent_year + 1)
        if target_year is None:
            max_year = db.query(func.max(Exam.year)).filter(Exam.course_id == course.id).scalar()
            if max_year:
                target_year = max_year + 1
            else:
                target_year = 2024

        # Temporal isolation constraint with assessment cycle scoping
        context = HistoricalContext(course_id=course.id, cutoff_year=target_year, assessment_cycle=norm_cycle)
        repo = HistoricalRepository(db, context)
        
        hist_exams_orm = repo.get_historical_exams()
        scope = get_course_assessment_scope(course.id, norm_cycle, db=db)
        if not hist_exams_orm:
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
            return {
                "course_id": course.id,
                "subject": course.name,
                "target_year": target_year,
                "assessment_cycle": norm_cycle or "ALL",
                "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
                "assessment_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
                "evidence_status": scope.evidence_status,
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "assessment_scope": assessment_scope_payload,
                "predictions": [],
                "evidence": "Insufficient historical data",
                "data_quality": f"No historical exams found prior to the cutoff year for assessment cycle '{norm_cycle or 'ALL'}'."
            }

        hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(hist_exams_dicts)
        
        engine = ExamScopeCombinedModel(dna)
        all_topic_preds = engine.predict(PredictionTarget.TOPIC)
        family_preds = engine.predict(PredictionTarget.FAMILY)

        # Restrict topic predictions to assessment component scope if not ALL
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
        
        from datetime import datetime, timezone
        from backend.core.version import MODEL_VERSION, TAXONOMY_VERSION, ENGINE_VERSION

        observed_years = sorted(list({e.year for e in hist_exams_orm if e.year is not None}))

        predictions = []
        for p in topic_preds[:5]:
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
                    "status": "TOPIC_PRESENT" if y in topic_years else "TOPIC_ABSENT",
                }
                for y in observed_years
            ]
            p_dict["historical_years"] = sorted(list(topic_years))
            predictions.append(p_dict)

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
                    "status": "FAMILY_PRESENT" if y in fam_years else "FAMILY_ABSENT",
                }
                for y in observed_years
            ]
            p_dict["historical_years"] = sorted(list(fam_years))
            predictions.append(p_dict)

        all_span = list(range(observed_years[0], observed_years[-1] + 1)) if observed_years else []
        unobserved_years = [y for y in all_span if y not in observed_years]

        return {
            "course_id": course.id,
            "subject": course.name,
            "target_year": target_year,
            "assessment_cycle": norm_cycle or "ALL",
            "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "assessment_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "assessment_scope": assessment_scope_payload,
            "predictions": predictions,
            "observed_years": observed_years,
            "unobserved_years": unobserved_years,
            "gap_years": unobserved_years,
            "evidence": f"Analyzed {len(hist_exams_orm)} historical exams across {len(observed_years)} years.",
            "data_quality": "Complete multi-year evidence base from genuine academic archives.",
            "model_metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
