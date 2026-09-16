import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.core.database import Base
from backend.models.core import Course, Document, Exam, Section, Question
from backend.services.document import DocumentService

client = TestClient(app)


def test_404_nonexistent_course():
    """Verify clean 404 behavior for unknown course IDs and names on endpoints requiring existing course."""
    res = client.get("/api/intelligence/9999999/questions")
    assert res.status_code == 404
    assert "detail" in res.json()

    res_pred = client.get("/api/predictions/CompletelyFakeCourseNameXYZ")
    assert res_pred.status_code == 404

    res_res = client.get("/api/study/resources/NonExistentCourse/NonExistentTopic")
    assert res_res.status_code == 404


def test_422_invalid_request_parameters():
    """Verify 422 status on unprocessable payload formats."""
    # Malformed search payload
    res = client.post("/api/search/", json={"raw_query": 12345, "limit": "invalid_number"})
    assert res.status_code == 422


def test_unmatched_and_ambiguous_course_graceful_recovery():
    """
    Verify graceful return of UNMATCHED and AMBIGUOUS status without crashing or fabricating predictions.
    """
    # Unmatched course
    res_unmatched = client.get("/api/intelligence/aeros-1-2")
    assert res_unmatched.status_code == 200
    data_unmatched = res_unmatched.json()
    assert data_unmatched["data_availability_status"] == "UNMATCHED"
    assert len(data_unmatched["predictions"]) == 0
    assert data_unmatched["course"] is None

    # Ambiguous course
    res_ambiguous = client.get("/api/intelligence/aeros-2-3")
    assert res_ambiguous.status_code == 200
    data_ambiguous = res_ambiguous.json()
    assert data_ambiguous["data_availability_status"] == "AMBIGUOUS"
    assert len(data_ambiguous["predictions"]) == 0
    assert data_ambiguous["course"] is None
    assert "Biology" in data_ambiguous["curriculum"]["subject_name"]


def test_oversized_pdf_rejection():
    """Verify that PDFs exceeding 20MB are rejected with HTTP 413."""
    # 21MB payload
    oversized_data = b"%PDF-1.4 " + b"0" * (21 * 1024 * 1024)
    file_payload = {"file": ("huge_exam.pdf", io.BytesIO(oversized_data), "application/pdf")}

    res = client.post("/api/papers/upload", files=file_payload)
    assert res.status_code == 413
    assert "20MB" in res.json()["detail"]


def test_invalid_magic_bytes_pdf_rejection():
    """Verify that files named .pdf but lacking '%PDF-' magic bytes are rejected with HTTP 400."""
    fake_pdf_data = b"NOT_A_REAL_PDF_HEADER_JUST_RANDOM_TEXT"
    file_payload = {"file": ("spoofed.pdf", io.BytesIO(fake_pdf_data), "application/pdf")}

    res = client.post("/api/papers/upload", files=file_payload)
    assert res.status_code == 400
    assert "header signature" in res.json()["detail"].lower() or "%pdf-" in res.json()["detail"].lower()


def test_non_pdf_file_rejection():
    """Verify that non-PDF files (.exe, .docx, .sh) are rejected with HTTP 400."""
    file_payload = {"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00"), "application/x-msdownload")}
    res = client.post("/api/papers/upload", files=file_payload)
    assert res.status_code == 400
    assert "Only PDF" in res.json()["detail"]


def test_ingestion_idempotency_and_no_orphaned_state():
    """
    Section 16: Ingestion Failure Recovery
    Simulates duplicate ingestion, partial crash, and recovery.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        course = Course(name="Recovery Test Course", code="REC101")
        db.add(course)
        db.commit()

        svc = DocumentService(db)
        doc = svc.get_or_create_document(document_hash="rec_hash_001")

        extraction = {
            "sections": [
                {"name": "Part A", "questions": [{"marks": 2.0}, {"marks": 2.0}]},
                {"name": "Part B", "questions": [{"marks": 10.0}]}
            ]
        }

        # 1. Ingest successfully
        svc.import_exam_extraction(doc.id, course.id, 2024, "Odd", extraction)
        assert db.query(Exam).count() == 1
        assert db.query(Section).count() == 2
        assert db.query(Question).count() == 3

        # 2. Re-ingest duplicate document: must be completely idempotent (no duplicates)
        svc.import_exam_extraction(doc.id, course.id, 2024, "Odd", extraction)
        assert db.query(Exam).count() == 1
        assert db.query(Section).count() == 2
        assert db.query(Question).count() == 3

    finally:
        db.close()
