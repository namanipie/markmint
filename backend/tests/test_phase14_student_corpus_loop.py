import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.core import (
    Course, CourseTrack, Document, Exam, Question, QuestionFamily, QuestionFamilyMembership,
    Topic, Unit, Syllabus
)
from backend.models.submission import PaperSubmission, SubmissionStatus
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository


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


@pytest.fixture
def test_course_setup(db_session: Session):
    """Sets up a test course with syllabus, units, and topics."""
    course = Course(name="Engineering Chemistry", code="21CHY101J")
    db_session.add(course)
    db_session.flush()

    track = CourseTrack(course_id=course.id, track_key="general", track_name="General Chemistry")
    db_session.add(track)
    db_session.flush()

    syl = Syllabus(course_id=course.id, version="v1")
    db_session.add(syl)
    db_session.commit()

    unit1 = Unit(syllabus_id=syl.id, number=1, name="Electrochemistry")
    unit2 = Unit(syllabus_id=syl.id, number=2, name="Corrosion and its Control")
    db_session.add_all([unit1, unit2])
    db_session.flush()

    t1 = Topic(id=101, unit_id=unit1.id, name="Nernst Equation and Batteries")
    t2 = Topic(id=102, unit_id=unit2.id, name="Corrosion Mechanisms")
    db_session.add_all([t1, t2])
    db_session.commit()

    return course, track, [t1, t2]


class TestPhase14StudentCorpusLoop:

    @pytest.fixture(autouse=True)
    def admin_auth_override(self):
        from backend.core.security import require_admin_auth
        from backend.main import app
        app.dependency_overrides[require_admin_auth] = lambda: "admin"
        yield
        app.dependency_overrides.pop(require_admin_auth, None)

    def test_full_student_corpus_loop_with_question_families(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Requirements:
        Student -> paper submission -> validation -> moderation -> approval -> Document ->
        Exam -> Question extraction -> assessment identification -> syllabus mapping ->
        paper-derived coverage -> QuestionFamily -> prediction corpus.
        """
        course, track, topics = test_course_setup
        pdf_stream = make_pdf_with_text([
            "SRM UNIVERSITY",
            "ENGINEERING CHEMISTRY",
            "1. Explain Nernst equation for galvanic cell. [10 marks]",
            "2. Describe dry corrosion mechanism with examples. [10 marks]",
        ])

        # 1. Submit paper
        res = client.post(
            "/api/submissions",
            files={"file": ("chem_exam_2023.pdf", pdf_stream, "application/pdf")},
            data={
                "subject_name": course.name,
                "course_id": course.id,
                "declared_assessment": "ENDSEM",
                "uploader_session_id": "student_session_abc123"
            },
        )
        assert res.status_code == 200
        sub_id = res.json()["id"]

        # 2. Approve submission
        app_res = client.post(
            f"/api/submissions/{sub_id}/approve",
            json={"reviewer": "academic_chair", "override_year": 2023},
        )
        assert app_res.status_code == 200
        result = app_res.json()["result"]
        doc_id = result["document_id"]
        exam_id = result["exam_id"]

        # Verify Document, Exam, Question records
        doc = db_session.query(Document).get(doc_id)
        assert doc is not None
        assert doc.source == "STUDENT_SUBMISSION"
        assert doc.year == 2023

        exam = db_session.query(Exam).get(exam_id)
        assert exam is not None
        assert exam.course_id == course.id
        assert exam.year == 2023

        questions = (
            db_session.query(Question)
            .join(Question.section)
            .filter(Exam.id == exam_id)
            .all()
        )
        assert len(questions) == 2

        # Verify QuestionFamily and QuestionFamilyMembership linkage
        families = db_session.query(QuestionFamily).filter(QuestionFamily.subject == course.name).all()
        assert len(families) >= 1
        for q in questions:
            assert q.family_id is not None
            assert len(q.memberships) >= 1
            assert q.memberships[0].family_id == q.family_id

        # Verify prediction repository incorporates these questions
        ctx = HistoricalContext(course_id=course.id, cutoff_year=2024)
        repo = HistoricalRepository(db_session, ctx)
        hist_exams = repo.get_historical_exams()
        assert len(hist_exams) == 1
        assert hist_exams[0].id == exam.id

        hist_fams = repo.get_historical_family_memberships()
        assert len(hist_fams) == 2

    def test_duplicate_submission_hash_deduplication(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Duplicate SHA-256 hash must never create a second production Document.
        """
        course, track, topics = test_course_setup
        pdf_stream1 = make_pdf_with_text([
            "SRM UNIVERSITY",
            "ENGINEERING CHEMISTRY",
            "1. Discuss differential aeration corrosion. [10 marks]",
        ])
        pdf_bytes = pdf_stream1.getvalue()

        # Submit and approve first paper
        res1 = client.post(
            "/api/submissions",
            files={"file": ("original_paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id, "declared_assessment": "ENDSEM"},
        )
        sub_id1 = res1.json()["id"]
        client.post(f"/api/submissions/{sub_id1}/approve", json={"override_year": 2023})
        doc_count_1 = db_session.query(Document).count()
        assert doc_count_1 == 1

        # Submit exact same file again from different student
        res2 = client.post(
            "/api/submissions",
            files={"file": ("duplicate_upload.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id, "declared_assessment": "ENDSEM"},
        )
        sub_id2 = res2.json()["id"]
        app2 = client.post(f"/api/submissions/{sub_id2}/approve", json={"override_year": 2023})
        assert app2.status_code == 200

        # Verify document count has NOT increased
        doc_count_2 = db_session.query(Document).count()
        assert doc_count_2 == 1, "Duplicate hash must never create a second production document!"

    def test_admin_review_summary_and_quality_metrics(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Verifies admin review summary fields and the privacy-safe quality metrics endpoint.
        """
        course, track, topics = test_course_setup
        pdf_stream = make_pdf_with_text([
            "SRM UNIVERSITY",
            "ENGINEERING CHEMISTRY",
            "1. Explain electrochemical cell potential. [10 marks]",
        ])

        res = client.post(
            "/api/submissions",
            files={"file": ("chem_summary_test.pdf", pdf_stream, "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id, "declared_assessment": "ENDSEM"},
        )
        sub_id = res.json()["id"]
        client.post(f"/api/submissions/{sub_id}/approve", json={"override_year": 2023})

        # Test Admin Review Summary contract
        r_sum = client.get(f"/api/submissions/{sub_id}/review-summary")
        assert r_sum.status_code == 200
        summary = r_sum.json()

        assert "document" in summary
        assert "course" in summary
        assert "track" in summary
        assert "assessment" in summary
        assert "detected_year" in summary
        assert "duplicate_state" in summary
        assert "question_count" in summary
        assert "mapping_rate" in summary
        assert "unresolved_question_count" in summary
        assert "provenance" in summary
        assert "approval_status" in summary

        # Test Quality Metrics Endpoint
        r_met = client.get("/api/submissions/quality-metrics")
        assert r_met.status_code == 200
        metrics = r_met.json()

        assert metrics["submissions"] >= 1
        assert metrics["approved"] >= 1
        assert "mapping_rate" in metrics
        assert "questions_added" in metrics
        assert "questions_unresolved" in metrics
        # Zero PII check
        metrics_str = str(metrics).lower()
        for pii in ["email", "password", "session_id", "secret"]:
            assert pii not in metrics_str
