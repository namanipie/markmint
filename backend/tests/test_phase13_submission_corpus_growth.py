import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.core import Course, CourseTrack, Document, Exam, Question, DocumentProvenance, Topic, Unit, Syllabus
from backend.models.submission import PaperSubmission, SubmissionStatus
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.prediction.engine import AllTimeFrequencyBaseline
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.predictions import _build_historical_exam_payloads


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

    # Debug statements removed

    unit1 = Unit(syllabus_id=syl.id, number=1, name="Electrochemistry")
    unit2 = Unit(syllabus_id=syl.id, number=2, name="Corrosion and its Control")
    db_session.add_all([unit1, unit2])
    db_session.flush()

    # Topics corresponding to chemistry rules (e.g. topic IDs 101, 102)
    t1 = Topic(id=101, unit_id=unit1.id, name="Nernst Equation and Batteries")
    t2 = Topic(id=102, unit_id=unit2.id, name="Corrosion Mechanisms")
    db_session.add_all([t1, t2])
    db_session.commit()

    return course, track, [t1, t2]


class TestPhase13SubmissionCorpusGrowth:

    @pytest.fixture(autouse=True)
    def admin_auth_override(self):
        from backend.core.security import require_admin_auth
        from backend.main import app
        app.dependency_overrides[require_admin_auth] = lambda: "admin"
        yield
        app.dependency_overrides.pop(require_admin_auth, None)

    def test_pending_and_rejected_isolation_from_prediction(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Requirements 6 & 8:
        Pending, under-review, and rejected submissions must NOT create production documents,
        exams, or questions, and must NOT affect prediction evidence.
        """
        course, track, topics = test_course_setup
        pdf_stream = make_pdf_with_text([
            "SRM UNIVERSITY",
            "ENGINEERING CHEMISTRY",
            "1. Explain Nernst equation for galvanic cell. [10 marks]",
        ])

        # 1. Submit paper
        res = client.post(
            "/api/submissions",
            files={"file": ("chem_test.pdf", pdf_stream, "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id, "declared_assessment": "ENDSEM"},
        )
        assert res.status_code == 200
        sub_id = res.json()["id"]

        # Ensure 0 production records
        assert db_session.query(Document).count() == 0
        assert db_session.query(Exam).count() == 0
        assert db_session.query(Question).count() == 0

        # Ensure Prediction repository does not see this submission
        ctx = HistoricalContext(course_id=course.id, cutoff_year=2025)
        repo = HistoricalRepository(db_session, ctx)
        hist_exams = repo.get_historical_exams()
        assert len(hist_exams) == 0

        # 2. Reject submission
        rej_res = client.post(
            f"/api/submissions/{sub_id}/reject",
            json={"reason": "Scanned page is incomplete", "reviewer": "moderator_lead"},
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["result"]["status"] == "REJECTED"

        # Rejection creates strictly 0 prediction evidence
        assert db_session.query(Document).count() == 0
        assert db_session.query(Exam).count() == 0
        hist_exams_post_reject = repo.get_historical_exams()
        assert len(hist_exams_post_reject) == 0

    def test_approved_submission_feeds_ingestion_and_predictions(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Full Loop:
        submission → approval → ingestion → mapping → observed coverage → prediction visibility
        """
        course, track, topics = test_course_setup

        pdf_stream = make_pdf_with_text([
            "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY",
            "END SEMESTER EXAMINATION - MAY 2024",
            "21CHY101J ENGINEERING CHEMISTRY",
            "PART A",
            "1. Derive Nernst equation for single electrode potential. [10 marks]",
            "2. Explain mechanism of electrochemical corrosion. [10 marks]",
            "PART B",
            "3. What is an arbitrary unmapped topic question? [10 marks]",
        ])

        # 1. Submit paper
        sub_res = client.post(
            "/api/submissions",
            files={"file": ("chem_endsem_2024.pdf", pdf_stream, "application/pdf")},
            data={
                "subject_name": course.name,
                "course_id": course.id,
                "track_id": track.id,
                "declared_assessment": "ENDSEM",
                "uploader_session_id": "anon_session_abc123",
            },
        )
        assert sub_res.status_code == 200
        sub_id = sub_res.json()["id"]

        # 2. Approve paper
        app_res = client.post(
            f"/api/submissions/{sub_id}/approve",
            json={
                "reviewer": "academic_chair",
                "override_year": 2024,
                "override_assessment": "ENDSEM",
                "override_track_id": track.id,
            },
        )
        assert app_res.status_code == 200
        res_data = app_res.json()["result"]
        assert res_data["status"] == "APPROVED"
        assert res_data["questions_ingested"] >= 3

        # 3. Verify production Document
        doc = db_session.query(Document).filter(Document.id == res_data["document_id"]).first()
        assert doc is not None
        assert doc.source == "STUDENT_SUBMISSION"
        assert doc.title == "chem_endsem_2024.pdf"  # Raw filename survived
        assert doc.exam_type == "ENDSEM"

        # 4. Verify DocumentProvenance survived
        prov = db_session.query(DocumentProvenance).filter(DocumentProvenance.document_id == doc.id).first()
        assert prov is not None
        assert prov.source_site == "STUDENT_SUBMISSION"
        assert f"student_submission:{sub_id}" in prov.source_url

        # 5. Verify Exam and track
        exam = db_session.query(Exam).filter(Exam.document_id == doc.id).first()
        assert exam is not None
        assert exam.course_id == course.id
        assert exam.track_id == track.id
        assert exam.year == 2024
        assert exam.assessment_type == "ENDSEM"

        # 6. Verify Mapping: failures must remain explicitly unresolved
        questions = db_session.query(Question).all()
        assert len(questions) >= 3
        # Review summary should reflect total and mapped questions
        summary = res_data["review_summary"]
        assert summary["question_count"]["total"] >= 3
        assert "mapping_rate" in summary
        assert summary["mapping_rate"] >= 0.0

        # 7. Verify Paper-Derived Observed Coverage
        assert summary["observed_coverage"] is not None
        assert summary["observed_coverage"]["assessment_cycle"] == "ENDSEM"

        # 8. Verify Prediction Corpus Visibility
        # Predictions for 2025 cutoff should now INCLUDE the 2024 paper!
        ctx = HistoricalContext(course_id=course.id, cutoff_year=2025)
        repo = HistoricalRepository(db_session, ctx)
        hist_exams = repo.get_historical_exams()
        assert len(hist_exams) == 1
        assert hist_exams[0].year == 2024
        assert hist_exams[0].document.source == "STUDENT_SUBMISSION"

        # Convert to payload and verify prediction baseline model executes
        dna_payloads = _build_historical_exam_payloads(hist_exams)
        dna = DNAAnalyzerService.analyze(dna_payloads)
        model = AllTimeFrequencyBaseline(dna)
        preds = model.predict(PredictionTarget.TOPIC)
        assert isinstance(preds, list)

    def test_approval_idempotency(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Requirement 1: Approved submissions must be idempotent.
        Calling approve multiple times returns success without duplicating Document, Exam, or Question records.
        """
        course, track, topics = test_course_setup
        pdf_stream = make_pdf_with_text([
            "SRM UNIVERSITY",
            "CYCLE TEST 1 - 2023",
            "1. Define Corrosion. [5 marks]",
        ])

        res = client.post(
            "/api/submissions",
            files={"file": ("test_idempotent.pdf", pdf_stream, "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id, "declared_assessment": "CT1"},
        )
        sub_id = res.json()["id"]

        # First approval
        app1 = client.post(f"/api/submissions/{sub_id}/approve", json={"override_year": 2023})
        assert app1.status_code == 200
        assert app1.json()["result"]["status"] == "APPROVED"
        doc_count_1 = db_session.query(Document).count()
        exam_count_1 = db_session.query(Exam).count()
        q_count_1 = db_session.query(Question).count()

        # Second approval (idempotency check)
        app2 = client.post(f"/api/submissions/{sub_id}/approve", json={"override_year": 2023})
        assert app2.status_code == 200
        result2 = app2.json()["result"]
        assert result2["status"] == "APPROVED"
        assert result2.get("is_idempotent_replay") is True

        # Document, Exam, and Question counts must remain strictly identical
        assert db_session.query(Document).count() == doc_count_1
        assert db_session.query(Exam).count() == exam_count_1
        assert db_session.query(Question).count() == q_count_1

    def test_duplicate_hash_never_creates_second_production_document(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Requirement 2: Duplicate hash must never create a second production document.
        Scenario: A document with hash H was already ingested into production.
        A student submits a paper with hash H.
        When approved, the pipeline MUST reuse the existing document, record duplicate provenance,
        and strictly guarantee that NO second Document is created.
        """
        course, track, topics = test_course_setup
        pdf_bytes = make_pdf_with_text(["EXISTING PRODUCTION DOCUMENT", "1. Question 1. [10 marks]"]).getvalue()
        import hashlib
        file_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # 1. Existing production document and exam already in database
        prod_doc = Document(
            document_hash=file_hash,
            source="ARCHIVE_IMPORT",
            title="existing_exam_paper.pdf",
            subject=course.name,
            year=2021,
            exam_type="ENDSEM",
        )
        db_session.add(prod_doc)
        db_session.flush()

        prod_exam = Exam(
            course_id=course.id,
            document_id=prod_doc.id,
            year=2021,
            assessment_type="ENDSEM",
        )
        db_session.add(prod_exam)
        db_session.commit()

        initial_doc_count = db_session.query(Document).count()
        assert initial_doc_count == 1

        # 2. Student submits identical file
        sub = client.post(
            "/api/submissions",
            files={"file": ("student_upload.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id, "uploader_session_id": "session_user_B"},
        ).json()
        assert sub["is_duplicate"] is True
        assert sub["duplicate_of_document_id"] == prod_doc.id

        # 3. Approve student submission
        app = client.post(f"/api/submissions/{sub['id']}/approve", json={"override_year": 2021})
        assert app.status_code == 200

        # Crucial invariant: Document count MUST STILL BE 1! Never a second document!
        assert db_session.query(Document).count() == initial_doc_count
        assert db_session.query(Exam).count() == 1

        # Check duplicate state in review summary
        summary = app.json()["result"]["review_summary"]
        assert summary["duplicate_state"]["status"] == "DUPLICATE_DOCUMENT"
        assert summary["duplicate_state"]["is_duplicate"] is True

        # Check provenance was added to existing document
        provs = db_session.query(DocumentProvenance).filter(DocumentProvenance.document_id == prod_doc.id).all()
        assert len(provs) >= 1
        assert any(p.source_priority == "DUPLICATE_SOURCE" for p in provs)

    def test_failed_ingestion_atomic_rollback(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Requirement 7: Failed ingestion must not partially mutate production data.
        """
        course, track, topics = test_course_setup
        pdf_stream = make_pdf_with_text(["VALID INITIAL TEXT", "1. Question. [5 marks]"])
        sub = client.post(
            "/api/submissions",
            files={"file": ("will_fail.pdf", pdf_stream, "application/pdf")},
            data={"subject_name": course.name, "course_id": course.id},
        ).json()

        # Sabotage the saved file on disk to trigger an extraction error during approval
        sub_record = db_session.query(PaperSubmission).get(sub["id"])
        sub_record.file_path = "non_existent_file_to_force_failure.pdf"
        db_session.commit()

        # Approval should fail with 404 or 500
        app_res = client.post(f"/api/submissions/{sub['id']}/approve", json={})
        assert app_res.status_code in (404, 500)

        # Production database must remain completely pristine (0 documents, 0 exams)
        assert db_session.query(Document).count() == 0
        assert db_session.query(Exam).count() == 0
        assert db_session.query(Question).count() == 0

    def test_admin_review_summary_and_submitter_feedback_endpoints(self, client: TestClient, db_session: Session, test_course_setup):
        """
        Tests the 9 required admin review summary fields and verified submitter feedback privacy.
        """
        course, track, topics = test_course_setup
        pdf_stream = make_pdf_with_text([
            "SRM UNIVERSITY - 2024",
            "ENGINEERING CHEMISTRY",
            "1. What is Corrosion? [10 marks]",
        ])
        sub = client.post(
            "/api/submissions",
            files={"file": ("feedback_test.pdf", pdf_stream, "application/pdf")},
            data={
                "subject_name": course.name,
                "course_id": course.id,
                "track_id": track.id,
                "declared_assessment": "ENDSEM",
                "uploader_session_id": "session_student_xyz",
            },
        ).json()

        # 1. Submitter Feedback (PENDING state)
        feed_res = client.get(f"/api/submissions/{sub['id']}/feedback")
        assert feed_res.status_code == 200
        feed = feed_res.json()
        assert feed["tracking_id"] == f"#SUB-{sub['id']}"
        assert feed["status"] == "PENDING"
        assert feed["status_badge"] == "Queued for Moderation"
        assert "queued" in feed["status_message"].lower()
        assert feed["is_contributed_to_corpus"] is False
        # Guarantee privacy: NO internal admin usernames or consistency scores
        assert "reviewed_by" not in feed
        assert "consistency_score" not in feed
        assert "ingested_document_id" not in feed

        # Also test tracking lookup by tracking code
        track_lookup = client.get(f"/api/submissions/tracking/%23SUB-{sub['id']}")
        assert track_lookup.status_code == 200
        assert track_lookup.json()["tracking_id"] == f"#SUB-{sub['id']}"

        # 2. Approve submission
        client.post(f"/api/submissions/{sub['id']}/approve", json={"reviewer": "chief_examiner"})

        # 3. Submitter Feedback (APPROVED state)
        feed_approved = client.get(f"/api/submissions/{sub['id']}/feedback").json()
        assert feed_approved["status"] == "APPROVED"
        assert feed_approved["is_contributed_to_corpus"] is True
        assert "markmint intelligence corpus" in feed_approved["status_message"].lower()

        # 4. Admin Review Summary (Must have all 9 required fields)
        summary_res = client.get(f"/api/submissions/{sub['id']}/review-summary")
        assert summary_res.status_code == 200
        summary = summary_res.json()

        # Field 1: course
        assert summary["course"]["id"] == course.id
        assert summary["course"]["code"] == course.code
        # Field 2: track if applicable
        assert summary["track"]["id"] == track.id
        assert summary["track"]["name"] == track.track_name
        # Field 3: assessment
        assert summary["assessment"] is not None
        # Field 4: year
        assert summary["year"] is not None
        # Field 5: duplicate state
        assert "status" in summary["duplicate_state"]
        assert summary["duplicate_state"]["status"] == "UNIQUE"
        # Field 6: question count
        assert summary["question_count"]["total"] >= 1
        # Field 7: mapping rate
        assert "mapping_rate" in summary
        assert "mapping_rate_formatted" in summary
        # Field 8: provenance
        assert summary["provenance"]["original_filename"] == "feedback_test.pdf"
        assert summary["provenance"]["source"] == "STUDENT_SUBMISSION"
        # Field 9: approval state
        assert summary["approval_state"]["status"] == "APPROVED"
        assert summary["approval_state"]["reviewed_by"] == "chief_examiner"
        assert summary["approval_state"]["ingested_document_id"] is not None
