import hashlib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.endpoints.predictions import get_prediction, resolve_course
from backend.core.database import SessionLocal, get_db
from backend.models.core import Course
from backend.services.student_uploads import StudentUploadService
from backend.services.study_intelligence import StudyIntelligenceService

router = APIRouter(prefix="/study", tags=["study"])


class ProgressRequest(BaseModel):
    user_id: str = "anonymous"
    topic_id: Optional[int] = None
    topic: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    viewed_resource: bool = False
    practice_attempted: bool = False
    practice_accuracy: Optional[float] = None


def _course(db: Session, course_name: str) -> Course:
    course = resolve_course(db, course_name)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _topic_predictions(course_name: str, target_year: Optional[int], assessment_cycle: Optional[str], db: Session):
    prediction_payload = get_prediction(course_name, target_year, assessment_cycle, db)
    return prediction_payload, prediction_payload.get("predictions", [])


@router.get("/priorities/{course_name}")
def get_study_priorities(
    course_name: str,
    target_year: Optional[int] = None,
    assessment_cycle: Optional[str] = None,
    user_id: str = "anonymous",
    db: Session = Depends(get_db),
):
    course = _course(db, course_name)
    payload, predictions = _topic_predictions(course.name, target_year, assessment_cycle, db)
    topic_predictions = [p for p in predictions if p.get("category") == "topic"]
    family_predictions = [p for p in predictions if p.get("category") == "family"]
    from backend.services.prediction.engine import PredictionResult
    from backend.models.core import Topic, Unit, Syllabus

    syl_ids = [s.id for s in course.syllabuses] if course.syllabuses else []
    taxonomy_topic_count = (
        db.query(Topic)
        .join(Unit, Topic.unit_id == Unit.id)
        .filter(Unit.syllabus_id.in_(syl_ids))
        .count()
        if syl_ids else 0
    )
    has_topic_taxonomy = taxonomy_topic_count > 0

    if has_topic_taxonomy and topic_predictions:
        plan_mode = "topic"
    elif family_predictions:
        plan_mode = "family"
    else:
        plan_mode = "insufficient"
    plan = []

    if topic_predictions:
        model_predictions = [
            PredictionResult(
                target=item.get("category", "topic"),
                name=item["name"],
                rank=item.get("rank", index),
                score=float(item.get("score", 0.0)),
                confidence=item.get("confidence", "LOW"),
                evidence=item.get("evidence_details", {}),
            )
            for index, item in enumerate(topic_predictions, start=1)
        ]
        plan = StudyIntelligenceService(db).generate_study_plan(
            model_predictions, course.id, user_id
        )
    elif family_predictions:
        for index, item in enumerate(family_predictions, start=1):
            fam_id = item.get("family_id")
            score = float(item.get("score", 0.0))
            p_cnt = item.get("distinct_paper_count") or item.get("papers_with_topic") or 1
            occ = item.get("historical_occurrences") or item.get("historyCount") or 1
            years = item.get("observed_years") or []
            years_str = f" ({', '.join(map(str, sorted(years)))})" if years else ""
            rep_type = item.get("repetition_type", "family_repeat")
            rep_label = "Exact verbatim repeat" if rep_type == "exact_repeat" else "Recurring question family"

            priority_band = "HIGH" if score >= 0.5 or occ >= 3 else "MEDIUM"
            plan.append({
                "topic": item["name"],
                "name": item["name"],
                "category": "family",
                "family_id": fam_id,
                "prediction_score": round(score, 4),
                "probability": round(float(item.get("probability", score)), 4),
                "confidence": item.get("confidence", "MEDIUM"),
                "priority": priority_band,
                "repetition_type": rep_type,
                "distinct_paper_count": p_cnt,
                "historical_occurrences": occ,
                "observed_years": years,
                "reason": f"{rep_label}: appeared across {p_cnt} past examination papers{years_str} with {occ} total occurrences.",
                "reasons": [
                    f"{rep_label} observed across {p_cnt} examination papers{years_str}.",
                    f"Verified historical frequency: {occ} questions examined.",
                ],
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
                "student_status": "NOT_STARTED",
            })

    return {
        "course": course.name,
        "target_year": payload["target_year"],
        "plan_mode": plan_mode,
        "priorities": plan,
        "topics": plan,
        "assessment_cycle": payload.get("assessment_cycle", "ALL"),
        "assessment_component": payload.get("assessment_component"),
        "assessment_label": payload.get("assessment_label"),
        "assessment_scope": payload.get("assessment_scope"),
        "has_topic_taxonomy": has_topic_taxonomy,
        "taxonomy_topic_count": taxonomy_topic_count,
        "topic_predictions_count": len(topic_predictions),
        "family_predictions_count": len(family_predictions),
        "prediction_evidence": payload.get("evidence"),
        "data_quality": payload.get("data_quality"),
    }


@router.get("/plan/{course_name}")
def get_study_plan(
    course_name: str,
    target_year: Optional[int] = None,
    assessment_cycle: Optional[str] = None,
    user_id: str = "anonymous",
    db: Session = Depends(get_db),
):
    return get_study_priorities(course_name, target_year, assessment_cycle, user_id, db)


@router.get("/resources/{course_name}/{topic_name}")
def get_topic_resources(
    course_name: str,
    topic_name: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    course = _course(db, course_name)
    resources = StudyIntelligenceService(db).get_topic_resources(topic_name, course.id)
    return {"course": course.name, "topic": topic_name, "resources": resources[:limit]}


MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


@router.post("/uploads")
def upload_study_resource(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    user_id: str = Form("anonymous"),
    resource_type: str = Form("student_notes"),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF study resources are supported")

    content = file.file.read()
    if len(content) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds the 20MB limit.")

    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file format: missing '%PDF-' header signature.")

    import re
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(file.filename).name)
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{hashlib.sha256(content).hexdigest()}_{safe_name}"
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)

    upload_svc = StudentUploadService(db)
    try:
        doc = upload_svc.process_student_upload(
            str(file_path), safe_name, course_id, user_id, resource_type=resource_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "document_id": doc.id,
        "filename": doc.title,
        "owner_id": doc.owner_id,
        "resource_type": doc.resource_type,
        "status": doc.processing_status,
    }


@router.post("/progress/{course_id}")
def update_progress(course_id: int, req: ProgressRequest, db: Session = Depends(get_db)):
    service = StudyIntelligenceService(db)
    topic_id = req.topic_id
    if topic_id is None and req.topic:
        topic_obj = service._course_topic(req.topic, course_id)
        if topic_obj:
            topic_id = topic_obj.id
        else:
            raise HTTPException(status_code=404, detail=f"Topic '{req.topic}' not found in course {course_id}")
    elif topic_id is None:
        raise HTTPException(status_code=400, detail="Either 'topic_id' or 'topic' name must be provided")

    status = req.status
    if req.action == "complete_topic":
        status = "COMPLETED"
    elif req.action == "reset_topic":
        status = "NOT_STARTED"

    viewed_resource = req.viewed_resource or (req.action == "view_resource")

    try:
        progress = service.record_progress(
            student_id=req.user_id,
            course_id=course_id,
            topic_id=topic_id,
            status=status,
            viewed_resource=viewed_resource,
            practice_attempted=req.practice_attempted,
            practice_accuracy=req.practice_accuracy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "success": True,
        "status": progress.status,
        "last_studied": progress.last_studied_at,
    }
