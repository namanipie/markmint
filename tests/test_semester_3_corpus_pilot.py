"""
Semester 3 CS Core Verified Corpus Ingestion Pilot Test Suite.
Validates the complete end-to-end pipeline:
source -> document -> extraction -> canonical representation -> question -> topic classification -> Question Family -> health -> prediction -> backtest.

Courses evaluated:
- Course 24: Data Structures and Algorithms (21CSC201J, SEM3-DSA)
- Course 25: Operating Systems (21CSC202J, SEM3-OS)
- Course 26: Computer Organization and Architecture (21CSS201T, SEM3-COA)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Exam, Section, Question, Document,
    QuestionFamily, QuestionFamilyMembership, question_topic
)
from backend.services.corpus_health import CorpusHealthService
from backend.services.prediction.backtester import BacktestHarness, EvidenceSufficiencyState
from backend.services.taxonomy_registry import get_taxonomy_registry


SEM3_COURSES = [
    {
        "id": 24,
        "name": "Data Structures and Algorithms",
        "canonical_code": "21CSC201J",
        "code": "SEM3-DSA",
        "expected_exams": 7,
        "expected_questions": 220,
        "expected_topics": 27,
        "years": [2023, 2024, 2025],
    },
    {
        "id": 25,
        "name": "Operating Systems",
        "canonical_code": "21CSC202J",
        "code": "SEM3-OS",
        "expected_exams": 6,
        "expected_questions": 198,
        "expected_topics": 27,
        "years": [2023, 2024],
    },
    {
        "id": 26,
        "name": "Computer Organization and Architecture",
        "canonical_code": "21CSS201T",
        "code": "SEM3-COA",
        "expected_exams": 4,
        "expected_questions": 128,
        "expected_topics": 25,
        "years": [2023, 2024],
    },
]


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_sem3_taxonomy_and_syllabus_authoritative():
    """1. Verify Semester 3 course definitions and canonical syllabuses in taxonomy registry."""
    registry = get_taxonomy_registry()
    for c_info in SEM3_COURSES:
        cid = c_info["id"]
        assert registry.has_course(cid), f"Course {cid} missing from TaxonomyRegistry"
        entry = registry.get_course(cid)
        assert entry.course.canonical_code == c_info["canonical_code"]
        assert len(entry.units) == 5
        rules = registry.get_topic_rules(cid)
        assert len(rules) == c_info["expected_topics"]


def test_sem3_document_and_exam_provenance(db: Session):
    """2. Verify documents and exams have full provenance, SHA-256 deduplication, and valid years."""
    for c_info in SEM3_COURSES:
        cid = c_info["id"]
        exams = db.query(Exam).filter(Exam.course_id == cid).all()
        assert len(exams) == c_info["expected_exams"]

        doc_hashes = set()
        for ex in exams:
            assert ex.track_id is None, "Semester 3 CS core must be single-track"
            assert ex.assessment_type == "END_SEM"
            assert ex.year in c_info["years"]
            assert ex.document is not None
            assert ex.document.source == "STUDIQUE"
            assert ex.document.resource_type == "QUESTION_PAPER"
            assert ex.document.extraction_status == "completed"
            assert ex.document.document_hash is not None
            assert ex.document.document_hash not in doc_hashes, "Duplicate document hash detected"
            doc_hashes.add(ex.document.document_hash)


def test_sem3_question_extraction_and_classification(db: Session):
    """3. Verify question extraction counts, vision extraction method, and topic mapping lineage."""
    for c_info in SEM3_COURSES:
        cid = c_info["id"]
        questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .all()
        )
        assert len(questions) == c_info["expected_questions"]

        for q in questions:
            assert q.extraction_method == "VISION_GEMINI"
            assert q.original_text and len(q.original_text.strip()) > 0

        # Topic lineage for mapped questions
        mapped_rows = (
            db.query(Question.id, Topic.id, Topic.name, Unit.number, Syllabus.course_id)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .all()
        )
        assert len(mapped_rows) > 0, f"Course {cid} must have mapped questions"
        for _, _, _, unit_num, syl_cid in mapped_rows:
            assert syl_cid == cid, f"Course {cid} question mapped to Syllabus of Course {syl_cid}"
            assert 1 <= unit_num <= 5, f"Unit number {unit_num} out of bounds"


def test_sem3_question_family_assignment_integrity(db: Session):
    """4. Verify 100% question family assignment, recurring vs singleton distribution, and memberships."""
    for c_info in SEM3_COURSES:
        cid = c_info["id"]
        c_name = c_info["name"]

        unassigned = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .filter(Question.family_id == None)
            .count()
        )
        assert unassigned == 0, f"Course {cid} has {unassigned} unassigned questions"

        families = db.query(QuestionFamily).filter(QuestionFamily.subject == c_name).all()
        assert len(families) > 0, f"Course {cid} has 0 Question Families"

        recurring = [f for f in families if f.repetition_type != "singleton"]
        singletons = [f for f in families if f.repetition_type == "singleton"]
        assert len(recurring) >= 5, f"Course {cid} expected at least 5 recurring families, got {len(recurring)}"
        assert len(singletons) >= 50, f"Course {cid} expected at least 50 singleton families, got {len(singletons)}"

        # Verify memberships
        for fam in families:
            mems = db.query(QuestionFamilyMembership).filter(QuestionFamilyMembership.family_id == fam.id).all()
            assert len(mems) >= 1, f"Family {fam.id} has no memberships"


def test_sem3_corpus_health_service(db: Session):
    """5. Verify CorpusHealthService returns accurate, untruncated factual health metrics for Semester 3."""
    for c_info in SEM3_COURSES:
        cid = c_info["id"]
        course = db.get(Course, cid)
        health = CorpusHealthService.get_course_health(db, course)

        # Scope
        assert health["scope"]["course_id"] == cid
        assert health["scope"]["track"] is None

        # Exams
        assert health["exams"]["total_exams"] == c_info["expected_exams"]
        assert health["exams"]["unknown_year_exams"] == 0
        assert health["exams"]["missing_years"] == []
        assert health["exams"]["years_observed"] == c_info["years"]

        # Questions
        assert health["questions"]["total_extracted"] == c_info["expected_questions"]
        assert health["questions"]["classified_with_family"] == c_info["expected_questions"]
        assert health["questions"]["unresolved_questions"] > 0, "Factual unresolved count preserved"

        # Families
        assert health["question_families"]["total_families"] > 0
        assert health["question_families"]["recurring_families"] > 0
        assert health["question_families"]["unassigned_questions"] == 0

        # Ingestion failures
        assert health["ingestion_and_extraction"]["documents_failed"] == 0


def test_sem3_prediction_generation(client: TestClient):
    """6. Verify /api/intelligence/{course_id} generates READY status and top-10 predictions."""
    for c_info in SEM3_COURSES:
        cid = c_info["id"]
        resp = client.get(f"/api/intelligence/{cid}")
        assert resp.status_code == 200, f"Intelligence endpoint failed for Course {cid}: {resp.text}"

        data = resp.json()
        assert data.get("data_availability_status") == "READY"
        predictions = data.get("predictions", [])
        assert len(predictions) == 10, f"Course {cid} expected 10 predictions, got {len(predictions)}"

        for p in predictions:
            assert "name" in p and len(p["name"]) > 0
            assert "prediction_score" in p and p["prediction_score"] >= 0.0
            assert "probability" in p and 0.0 <= p["probability"] <= 1.0
            assert p["confidence"] in ["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]
            assert "evidence_breakdown" in p


def test_sem3_historical_backtesting(db: Session):
    """7. Verify BacktestHarness executes with strict temporal isolation on Semester 3 courses."""
    harness = BacktestHarness(db)

    # Course 24 backtest against target year 2025
    res_24 = harness.backtest_target_year(course_id=24, target_year=2025)
    assert res_24["status"] == "COMPLETED"
    assert res_24["evidence_sufficiency"] == EvidenceSufficiencyState.SUFFICIENT_HISTORY
    assert res_24["historical_papers_used"] == 5  # 2023 (3) + 2024 (2)
    assert res_24["target_exams_evaluated"] == 2  # 2025 (2)
    assert len(res_24["evaluations"]) > 0

    eval_0 = res_24["evaluations"][0]
    assert eval_0["probability_calibration_verified"] is True
    metrics = eval_0["metrics"]
    assert "Recall@3" in metrics or "R@3" in metrics
    assert "Precision@5" in metrics or "P@5" in metrics

    # Course 25 backtest against target year 2024 (2 historical papers -> LIMITED_HISTORY)
    res_25 = harness.backtest_target_year(course_id=25, target_year=2024)
    assert res_25["status"] == "COMPLETED"
    assert res_25["evidence_sufficiency"] == EvidenceSufficiencyState.LIMITED_HISTORY
    assert res_25["historical_papers_used"] == 2
    assert res_25["target_exams_evaluated"] == 4
