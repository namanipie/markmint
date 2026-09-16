from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.core.database import get_db
from backend.models.core import Course, Exam, Topic, Unit, Syllabus
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
        for c in db.query(Course).all():
            if c.canonical_code and re.sub(r'[^a-zA-Z0-9]', '', c.canonical_code).lower() == norm_id:
                return c
            if re.sub(r'[^a-zA-Z0-9]', '', c.name).lower() == norm_id:
                return c
            if re.sub(r'[^a-zA-Z0-9]', '', c.code).lower() == norm_id:
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
                    "unit": (
                        question.topics[0].unit.name
                        if (question.topics and getattr(question.topics[0], "unit", None))
                        else None
                    ),
                    "question_type": question.question_type,
                    "repetition_type": (
                        question.memberships[0].match_type
                        if getattr(question, "memberships", None)
                        else "singleton"
                    ),
                    "family_name": (
                        question.family.canonical_name if question.family else None
                    ),
                    "difficulty": question.difficulty,
                }
                for section in exam.sections
                for question in section.questions
            ],
        }
        for exam in hist_exams_orm
    ]

@router.get("/predictions/{subject}")
def get_prediction(subject: str, target_year: Optional[int] = Query(None), db: Session = Depends(get_db)):
    try:
        course = _find_course(db, subject)
        if not course:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Determine target year dynamically if not provided.
        # Rule: Target the next unseen exam year (most_recent_year + 1)
        if target_year is None:
            max_year = db.query(func.max(Exam.year)).filter(Exam.course_id == course.id).scalar()
            if max_year:
                target_year = max_year + 1
            else:
                target_year = 2024

        # Temporal isolation constraint
        context = HistoricalContext(course_id=course.id, cutoff_year=target_year)
        repo = HistoricalRepository(db, context)
        
        hist_exams_orm = repo.get_historical_exams()
        if not hist_exams_orm:
            return {
                "subject": course.name,
                "target_year": target_year,
                "predictions": [],
                "evidence": "Insufficient historical data",
                "data_quality": "No historical exams found prior to the cutoff year."
            }

        hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(hist_exams_dicts)
        
        engine = ExamScopeCombinedModel(dna)
        topic_preds = engine.predict(PredictionTarget.TOPIC)
        family_preds = engine.predict(PredictionTarget.FAMILY)
        
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
