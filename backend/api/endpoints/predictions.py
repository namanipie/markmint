from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.core.database import get_db
from backend.models.core import Course, Exam
import re
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

router = APIRouter()


def _find_course(db: Session, identifier: str) -> Optional[Course]:
    """Generically resolve a course by exact name, case-insensitive name, code, ID, or alphanumeric string."""
    # 1. Exact or case-insensitive name match
    course = db.query(Course).filter(func.lower(Course.name) == identifier.lower()).first()
    if course:
        return course

    # 2. Case-insensitive code match (e.g. SEM1-CALC)
    course = db.query(Course).filter(func.lower(Course.code) == identifier.lower()).first()
    if course:
        return course

    # 3. Numeric ID match
    if identifier.isdigit():
        course = db.query(Course).filter(Course.id == int(identifier)).first()
        if course:
            return course

    # 4. Normalized alphanumeric match (ignores spaces, punctuation, case)
    norm_id = re.sub(r'[^a-zA-Z0-9]', '', identifier).lower()
    if norm_id:
        for c in db.query(Course).all():
            if re.sub(r'[^a-zA-Z0-9]', '', c.name).lower() == norm_id:
                return c
            if re.sub(r'[^a-zA-Z0-9]', '', c.code).lower() == norm_id:
                return c

    return None


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
                    "unit": None,
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
                # Fallback if absolutely no exams exist (handled below by repo returning empty)
                target_year = 2024

        # Temporal isolation constraint
        # Cutoff year = target_year means ONLY data < target_year is loaded.
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
        
        from datetime import datetime
        from backend.core.version import MODEL_VERSION, TAXONOMY_VERSION, ENGINE_VERSION

        predictions = []
        for p in topic_preds[:5]:
            predictions.append(p.to_dict())

        for p in family_preds[:5]:
            predictions.append(p.to_dict())

        return {
            "course_id": course.id,
            "subject": course.name,
            "target_year": target_year,
            "predictions": predictions,
            "evidence": f"Analyzed {len(hist_exams_orm)} historical exams.",
            "data_quality": "Marks unavailable for many questions. Analysis primarily uses occurrence frequency.",
            "model_metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
