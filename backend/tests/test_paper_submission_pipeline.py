import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.core import Course, Document, Exam, Question, DocumentProvenance
from backend.models.submission import PaperSubmission, SubmissionStatus, ConsistencyStatus


def make_pdf_with_text(lines: list[str]) -> io.BytesIO:
    """Generates a standard compliant single-page PDF with lines of text."""
    escaped_lines = [l.replace("(", "\\(").replace(")", "\\)") for l in lines]
    stream_text = " ".join(f"({line}) Tj T*" for line in escaped_lines)
    content = f"BT /F1 12 Tf 72 720 Td 15 TL {stream_text} ET"
    pdf_str = f"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length {len(content)} >>
stream
{content}
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000111 00000 n 
0000000224 00000 n 
0000000280 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
350
%%EOF"""
    return io.BytesIO(pdf_str.encode("latin1"))


def test_invalid_pdf_rejections(client: TestClient):
    # 1. Non-pdf extension
    res = client.post(
        "/api/submissions/validate-preview",
        files={"file": ("exam.docx", b"dummy content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 400
    assert "Only PDF files are supported" in res.json()["detail"]

    # 2. Corrupt content missing %PDF- header
    res = client.post(
        "/api/submissions/validate-preview",
        files={"file": ("bad_paper.pdf", b"NOT_A_PDF_STREAM", "application/pdf")},
    )
    assert res.status_code == 400
    assert "%PDF-" in res.json()["detail"]


def test_validate_preview_extraction_and_heuristics(client: TestClient, db_session: Session):
    # Add target course
    course = Course(name="Data Structures and Algorithms", code="21CSC201J")
    db_session.add(course)
    db_session.commit()

    pdf_stream = make_pdf_with_text([
        "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY",
        "CYCLE TEST 1 - MAY 2024",
        "COURSE CODE: 21CSC201J",
        "DATA STRUCTURES AND ALGORITHMS",
        "PART A",
        "1. Define AVL Tree with balance factor. [5 marks]",
        "2. What is time complexity of QuickSort? [5 marks]",
        "PART B",
        "3. Explain Dijkstra's algorithm with graph example. [15 marks]",
    ])

    res = client.post(
        "/api/submissions/validate-preview",
        files={"file": ("dsa_ct1_2024.pdf", pdf_stream, "application/pdf")},
        data={"course_id": course.id, "declared_assessment": "Cycle Test 1"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["detected_year"] == 2024
    assert data["detected_assessment"] == "Cycle Test 1"
    assert data["detected_course_code"] == "21CSC201J"
    assert data["consistency_status"] == ConsistencyStatus.CONSISTENT.value
    assert data["consistency_score"] == 1.0
    assert data["is_duplicate"] is False
    assert "Define AVL Tree" in data["extracted_snippet"]

    # Guarantee preview DOES NOT create any records
    assert db_session.query(PaperSubmission).count() == 0
    assert db_session.query(Document).count() == 0
    assert db_session.query(Exam).count() == 0


def test_course_mismatch_detection(client: TestClient, db_session: Session):
    course_math = Course(name="Calculus and Linear Algebra", code="21MTH101T")
    course_physics = Course(name="Physics: Electromagnetic Theory", code="21PHY101J")
    db_session.add_all([course_math, course_physics])
    db_session.commit()

    # Upload physics paper while declaring calculus
    physics_pdf = make_pdf_with_text([
        "SEMESTER EXAMINATION - DECEMBER 2023",
        "COURSE CODE: 21PHY101J",
        "PHYSICS: ELECTROMAGNETIC THEORY",
        "PART A",
        "1. State Gauss Law in electrostatics. [5 marks]",
    ])

    res = client.post(
        "/api/submissions/validate-preview",
        files={"file": ("physics.pdf", physics_pdf, "application/pdf")},
        data={"course_id": course_math.id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["detected_course_code"] == "21PHY101J"
    assert data["consistency_status"] == ConsistencyStatus.MISMATCH.value
    assert "conflicts with declared" in data["consistency_notes"]


def test_pending_submission_isolation_from_production(client: TestClient, db_session: Session):
    course = Course(name="Operating Systems", code="21CSC202J")
    db_session.add(course)
    db_session.commit()

    pdf_stream = make_pdf_with_text([
        "SRM UNIVERSITY",
        "CYCLE TEST 2 - NOVEMBER 2023",
        "21CSC202J OPERATING SYSTEMS",
        "SECTION A",
        "1. Explain Round Robin Scheduling with Gantt chart. [10 marks]",
        "2. Define Banker's Algorithm for deadlock avoidance. [10 marks]",
    ])

    res = client.post(
        "/api/submissions",
        files={"file": ("os_ct2.pdf", pdf_stream, "application/pdf")},
        data={
            "subject_name": "Operating Systems",
            "branch_name": "Computer Science and Engineering",
            "semester": 3,
            "course_id": course.id,
            "declared_assessment": "Cycle Test 2",
            "uploader_session_id": "anon-session-xyz-123",
        },
    )
    assert res.status_code == 200
    sub_data = res.json()
    assert sub_data["status"] == "PENDING"
    assert sub_data["detected_year"] == 2023
    assert sub_data["detected_assessment"] == "Cycle Test 2"
    assert sub_data["detected_course_code"] == "21CSC202J"

    # STRICT ISOLATION ASSERTION: Production tables must remain untouched
    assert db_session.query(PaperSubmission).count() == 1
    assert db_session.query(Document).count() == 0
    assert db_session.query(Exam).count() == 0
    assert db_session.query(Question).count() == 0


def test_duplicate_detection_against_submissions_and_production(client: TestClient, db_session: Session):
    pdf_stream = make_pdf_with_text([
        "TEST EXAM 2022",
        "1. What is polymorphism? [5 marks]",
    ])
    raw_bytes = pdf_stream.getvalue()

    # 1. First submission succeeds
    res1 = client.post(
        "/api/submissions",
        files={"file": ("poly.pdf", io.BytesIO(raw_bytes), "application/pdf")},
        data={"subject_name": "Object Oriented Programming"},
    )
    assert res1.status_code == 200
    sub1_id = res1.json()["id"]

    # 2. Previewing same file indicates duplicate submission
    res_preview = client.post(
        "/api/submissions/validate-preview",
        files={"file": ("poly.pdf", io.BytesIO(raw_bytes), "application/pdf")},
    )
    assert res_preview.status_code == 200
    prev_data = res_preview.json()
    assert prev_data["is_duplicate"] is True
    assert prev_data["duplicate_of_submission_id"] == sub1_id

    # 3. Simulate production document with matching hash
    prod_bytes = make_pdf_with_text(["PROD UNIQUE DOC"]).getvalue()
    prod_hash = "abc123uniquehash"
    prod_doc = Document(document_hash=prod_hash, title="Existing Production Paper")
    db_session.add(prod_doc)
    db_session.commit()

    from backend.services.submission_validator import check_for_duplicates
    is_dup, doc_id, sub_id, _ = check_for_duplicates(db_session, prod_hash)
    assert is_dup is True
    assert doc_id == prod_doc.id


def test_rejection_workflow(client: TestClient, db_session: Session):
    pdf_stream = make_pdf_with_text(["SAMPLE PAPER"])
    res = client.post(
        "/api/submissions",
        files={"file": ("junk.pdf", pdf_stream, "application/pdf")},
        data={"subject_name": "Unknown Subject"},
    )
    sub_id = res.json()["id"]

    # Reject submission
    rej_res = client.post(
        f"/api/submissions/{sub_id}/reject",
        json={"reason": "Scanned document is illegible and missing page 2.", "reviewer": "moderator_1"},
    )
    assert rej_res.status_code == 200
    rej_data = rej_res.json()["result"]
    assert rej_data["status"] == "REJECTED"
    assert "illegible" in rej_data["rejection_reason"]
    assert rej_data["reviewed_by"] == "moderator_1"

    # Strictly 0 production documents or exams created
    assert db_session.query(Document).count() == 0
    assert db_session.query(Exam).count() == 0


def test_approval_workflow_promotes_to_production(client: TestClient, db_session: Session):
    course = Course(name="Computer Networks", code="21CSC205J")
    db_session.add(course)
    db_session.commit()

    pdf_stream = make_pdf_with_text([
        "END SEMESTER EXAMINATION - MAY 2024",
        "COURSE: 21CSC205J COMPUTER NETWORKS",
        "SECTION A",
        "1. Explain OSI 7-Layer reference model in detail. [10 marks]",
        "2. What is CSMA/CD protocol? [5 marks]",
        "SECTION B",
        "3. Derive Hamming Code error correction for 7-bit string. [15 marks]",
    ])

    res = client.post(
        "/api/submissions",
        files={"file": ("cn_endsem_2024.pdf", pdf_stream, "application/pdf")},
        data={
            "subject_name": "Computer Networks",
            "course_id": course.id,
            "declared_assessment": "End Semester",
            "uploader_session_id": "student_session_789",
        },
    )
    assert res.status_code == 200
    sub_id = res.json()["id"]

    # Pre-approval check
    assert db_session.query(Document).count() == 0
    assert db_session.query(Exam).count() == 0
    assert db_session.query(Question).count() == 0

    # Approve paper
    app_res = client.post(
        f"/api/submissions/{sub_id}/approve",
        json={"reviewer": "lead_moderator", "override_year": 2024},
    )
    assert app_res.status_code == 200
    result = app_res.json()["result"]
    assert result["status"] == "APPROVED"
    assert result["questions_ingested"] >= 3
    assert result["course_id"] == course.id

    # Post-approval check: Verify production corpus entities
    doc = db_session.query(Document).filter(Document.id == result["document_id"]).first()
    assert doc is not None
    assert doc.source == "STUDENT_SUBMISSION"
    assert doc.exam_type == "End Semester"
    assert doc.year == 2024

    # Verify provenance
    prov = db_session.query(DocumentProvenance).filter(DocumentProvenance.document_id == doc.id).first()
    assert prov is not None
    assert prov.source_site == "STUDENT_SUBMISSION"
    assert "student_session_789" in prov.source_url

    # Verify Exam and Questions
    exam = db_session.query(Exam).filter(Exam.document_id == doc.id).first()
    assert exam is not None
    assert exam.course_id == course.id
    assert exam.year == 2024

    questions = db_session.query(Question).all()
    assert len(questions) >= 3
    question_texts = " ".join([q.original_text for q in questions])
    assert "OSI 7-Layer" in question_texts

    # Attempting to approve again should be idempotent (Phase 13)
    dup_app = client.post(
        f"/api/submissions/{sub_id}/approve",
        json={"reviewer": "lead_moderator"},
    )
    assert dup_app.status_code == 200
    assert dup_app.json()["result"]["status"] == "APPROVED"
    assert dup_app.json()["result"]["is_idempotent_replay"] is True
    # Verify no duplicate documents or exams were created
    assert db_session.query(Document).count() == 1
    assert db_session.query(Exam).count() == 1
