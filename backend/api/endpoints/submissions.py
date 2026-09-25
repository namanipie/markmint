import os
import re
from pathlib import Path
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.submission import PaperSubmission, SubmissionStatus
from backend.services.submission_validator import (
    validate_pdf_content,
    compute_sha256,
    extract_preview_text,
    detect_metadata_from_text,
    evaluate_course_consistency,
    check_for_duplicates,
    MAX_SUBMISSION_SIZE_BYTES,
)
from backend.services.submission_approval import SubmissionApprovalService
from backend.core.security import require_admin_auth

router = APIRouter()

SUBMISSIONS_STORAGE_DIR = Path("data/submissions/pending")
SUBMISSIONS_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class SubmissionPreviewResponse(BaseModel):
    filename: str
    file_size: int
    file_hash: str
    page_count: int
    extracted_snippet: str
    detected_year: Optional[int] = None
    detected_assessment: Optional[str] = None
    detected_course_code: Optional[str] = None
    consistency_score: float
    consistency_status: str
    consistency_notes: Optional[str] = None
    is_duplicate: bool
    duplicate_message: str
    duplicate_of_document_id: Optional[int] = None
    duplicate_of_submission_id: Optional[int] = None


class PaperSubmissionResponse(BaseModel):
    id: int
    original_filename: str
    file_hash: str
    file_size: int
    branch_name: Optional[str] = None
    semester: Optional[int] = None
    subject_name: str
    course_id: Optional[int] = None
    track_id: Optional[int] = None
    declared_assessment: Optional[str] = None
    page_count: int
    detected_year: Optional[int] = None
    detected_assessment: Optional[str] = None
    detected_course_code: Optional[str] = None
    consistency_score: float
    consistency_status: str
    consistency_notes: Optional[str] = None
    is_duplicate: bool
    duplicate_of_document_id: Optional[int] = None
    duplicate_of_submission_id: Optional[int] = None
    status: str
    source: str
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    ingested_document_id: Optional[int] = None


class ApproveSubmissionRequest(BaseModel):
    reviewer: str = "admin"
    override_course_id: Optional[int] = None
    override_track_id: Optional[int] = None
    override_assessment: Optional[str] = None
    override_year: Optional[int] = None


class RejectSubmissionRequest(BaseModel):
    reason: str
    reviewer: str = "admin"


def _format_submission_response(sub: PaperSubmission) -> dict:
    return {
        "id": sub.id,
        "original_filename": sub.original_filename,
        "file_hash": sub.file_hash,
        "file_size": sub.file_size,
        "branch_name": sub.branch_name,
        "semester": sub.semester,
        "subject_name": sub.subject_name,
        "course_id": sub.course_id,
        "track_id": sub.track_id,
        "declared_assessment": sub.declared_assessment,
        "page_count": sub.page_count,
        "detected_year": sub.detected_year,
        "detected_assessment": sub.detected_assessment,
        "detected_course_code": sub.detected_course_code,
        "consistency_score": sub.consistency_score,
        "consistency_status": sub.consistency_status,
        "consistency_notes": sub.consistency_notes,
        "is_duplicate": sub.is_duplicate,
        "duplicate_of_document_id": sub.duplicate_of_document_id,
        "duplicate_of_submission_id": sub.duplicate_of_submission_id,
        "status": sub.status,
        "source": sub.source,
        "created_at": sub.created_at.isoformat() if sub.created_at else "",
        "reviewed_at": sub.reviewed_at.isoformat() if sub.reviewed_at else None,
        "reviewed_by": sub.reviewed_by,
        "rejection_reason": sub.rejection_reason,
        "ingested_document_id": sub.ingested_document_id,
    }


@router.post("/validate-preview", response_model=SubmissionPreviewResponse)
async def validate_submission_preview(
    file: UploadFile = File(...),
    course_id: Optional[int] = Form(None),
    declared_assessment: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> Any:
    """
    Validates uploaded PDF and returns lightweight extraction preview, heuristic signals,
    and duplicate status. DOES NOT save record to database.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    is_valid, error = validate_pdf_content(content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    file_hash = compute_sha256(content)
    is_dup, dup_doc_id, dup_sub_id, dup_msg = check_for_duplicates(db, file_hash)

    extracted_text, total_pages = extract_preview_text(content, max_pages=3)
    detected = detect_metadata_from_text(extracted_text)

    score, status, notes = evaluate_course_consistency(
        db=db,
        course_id=course_id,
        extracted_text=extracted_text,
        detected_course_code=detected.get("course_code"),
    )

    # Take first 1200 characters for preview snippet
    snippet = (extracted_text[:1200] + "...") if len(extracted_text) > 1200 else extracted_text

    return SubmissionPreviewResponse(
        filename=file.filename,
        file_size=len(content),
        file_hash=file_hash,
        page_count=total_pages,
        extracted_snippet=snippet,
        detected_year=detected.get("year"),
        detected_assessment=detected.get("assessment"),
        detected_course_code=detected.get("course_code"),
        consistency_score=score,
        consistency_status=status,
        consistency_notes=notes,
        is_duplicate=is_dup,
        duplicate_message=dup_msg,
        duplicate_of_document_id=dup_doc_id,
        duplicate_of_submission_id=dup_sub_id,
    )


@router.post("", response_model=PaperSubmissionResponse)
async def create_submission(
    file: UploadFile = File(...),
    subject_name: str = Form(...),
    branch_name: Optional[str] = Form(None),
    semester: Optional[int] = Form(None),
    course_id: Optional[int] = Form(None),
    track_id: Optional[int] = Form(None),
    declared_assessment: Optional[str] = Form(None),
    uploader_session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> Any:
    """
    Saves a student examination paper submission into the quarantined moderation table.
    Guarantees that unreviewed submissions NEVER enter the production corpus.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    is_valid, error = validate_pdf_content(content)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    file_hash = compute_sha256(content)

    # Check for duplicate submission
    is_dup, dup_doc_id, dup_sub_id, dup_msg = check_for_duplicates(db, file_hash)
    if dup_sub_id:
        existing_sub = db.query(PaperSubmission).get(dup_sub_id)
        if existing_sub:
            return _format_submission_response(existing_sub)

    # Deterministic preview text and heuristics
    extracted_text, total_pages = extract_preview_text(content, max_pages=5)
    detected = detect_metadata_from_text(extracted_text)

    score, status, notes = evaluate_course_consistency(
        db=db,
        course_id=course_id,
        extracted_text=extracted_text,
        detected_course_code=detected.get("course_code"),
    )

    # Save raw file securely to disk
    safe_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(file.filename).name)
    saved_filename = f"{file_hash[:16]}_{safe_filename}"
    saved_path = SUBMISSIONS_STORAGE_DIR / saved_filename
    with open(saved_path, "wb") as f:
        f.write(content)

    # Anonymize session token if provided (no student PII stored)
    clean_session_id = uploader_session_id.strip()[:64] if uploader_session_id else None

    # Create submission record
    submission = PaperSubmission(
        file_hash=file_hash,
        original_filename=file.filename,
        file_path=str(saved_path),
        file_size=len(content),
        mime_type="application/pdf",
        branch_name=branch_name,
        semester=semester,
        subject_name=subject_name,
        course_id=course_id,
        track_id=track_id,
        declared_assessment=declared_assessment,
        extracted_text=extracted_text,
        page_count=total_pages,
        detected_year=detected.get("year"),
        detected_assessment=detected.get("assessment"),
        detected_course_code=detected.get("course_code"),
        consistency_score=score,
        consistency_status=status,
        consistency_notes=notes,
        is_duplicate=is_dup,
        duplicate_of_document_id=dup_doc_id,
        duplicate_of_submission_id=dup_sub_id,
        source="STUDENT_SUBMISSION",
        uploader_session_id=clean_session_id,
        status=SubmissionStatus.PENDING.value,
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return _format_submission_response(submission)


@router.get("", response_model=List[PaperSubmissionResponse])
def list_submissions(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, REVIEW, APPROVED, REJECTED"),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Any:
    """List submissions for administrative moderation and auditing."""
    query = db.query(PaperSubmission)
    if status:
        query = query.filter(PaperSubmission.status == status.upper())
    if course_id:
        query = query.filter(PaperSubmission.course_id == course_id)

    submissions = query.order_by(PaperSubmission.created_at.desc()).offset(offset).limit(limit).all()
    return [_format_submission_response(s) for s in submissions]


@router.get("/quality-metrics")
def get_submission_quality_metrics_endpoint(
    db: Session = Depends(get_db),
) -> Any:
    """
    Publicly safe quality metrics tracking submission health:
    - submissions
    - approved
    - rejected
    - duplicate
    - mapping rate
    - questions added
    - questions unresolved
    Does not expose PII, internal reviewer identities, or moderation audit comments.
    """
    return SubmissionApprovalService.get_submission_quality_metrics(db)


@router.get("/{submission_id}", response_model=PaperSubmissionResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)) -> Any:
    """Retrieve details of a single submission for moderation."""
    sub = db.query(PaperSubmission).get(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return _format_submission_response(sub)


@router.post("/{submission_id}/approve")
def approve_submission(
    submission_id: int,
    payload: Optional[ApproveSubmissionRequest] = None,
    admin: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> Any:
    """
    Moderation endpoint: Approves paper submission and ingests it into production
    documents, exams, sections, and questions. Requires administrative authorization.
    """
    req = payload or ApproveSubmissionRequest()
    reviewer_name = req.reviewer if (req.reviewer and req.reviewer != "admin") else admin
    svc = SubmissionApprovalService(db)
    try:
        result = svc.approve_submission(
            submission_id=submission_id,
            reviewer=reviewer_name,
            override_course_id=req.override_course_id,
            override_track_id=req.override_track_id,
            override_assessment=req.override_assessment,
            override_year=req.override_year,
        )
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval pipeline failed: {str(e)}")


@router.get("/{submission_id}/review-summary")
def get_submission_review_summary(
    submission_id: int,
    admin: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> Any:
    """
    Admin Review Summary endpoint showing:
    - Course & track (if applicable)
    - Assessment & year
    - Duplicate state
    - Question count (total, mapped, unmapped)
    - Mapping rate
    - Provenance
    - Approval state
    Requires administrative authorization.
    """
    svc = SubmissionApprovalService(db)
    try:
        summary = svc.get_admin_review_summary(submission_id)
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate review summary: {str(e)}")


@router.get("/{submission_id}/feedback")
def get_submission_feedback(
    submission_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Submitter Feedback endpoint: Returns friendly, actionable status notifications
    for the student without exposing internal reviewer identities or moderation heuristics.
    """
    svc = SubmissionApprovalService(db)
    try:
        feedback = svc.get_submitter_feedback(submission_id)
        return feedback
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feedback: {str(e)}")


@router.get("/tracking/{tracking_id}")
def get_submission_by_tracking(
    tracking_id: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Lookup submitter feedback using tracking code (e.g. '#SUB-12' or '12').
    """
    clean_id_str = tracking_id.replace("#SUB-", "").replace("SUB-", "").strip()
    try:
        numeric_id = int(clean_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tracking ID format. Use format #SUB-123.")

    svc = SubmissionApprovalService(db)
    try:
        return svc.get_submitter_feedback(numeric_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.post("/{submission_id}/reject")
def reject_submission(
    submission_id: int,
    payload: RejectSubmissionRequest,
    admin: str = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> Any:
    """
    Moderation endpoint: Rejects paper submission with reason.
    Guarantees no records are created in production documents or exams.
    Requires administrative authorization.
    """
    reviewer_name = payload.reviewer if (payload.reviewer and payload.reviewer != "admin") else admin
    svc = SubmissionApprovalService(db)
    try:
        result = svc.reject_submission(
            submission_id=submission_id,
            reason=payload.reason,
            reviewer=reviewer_name,
        )
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")
