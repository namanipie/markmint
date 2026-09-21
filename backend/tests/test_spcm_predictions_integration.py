"""
Integration tests for SPCM (Course 13) intelligence snapshots, prediction engine, and study plans.
Verifies that mapped SPCM questions activate topic-mode prediction while preserving Calculus and Chemistry.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_spcm_exam_payloads_include_mapped_topics() -> None:
    """Verifies that _build_historical_exam_payloads extracts topic and unit for Course 13."""
    db = SessionLocal()
    try:
        hist_exams = db.query(Exam).filter(Exam.course_id == 13).all()
        assert len(hist_exams) > 0

        payloads = _build_historical_exam_payloads(hist_exams)
        assert len(payloads) == len(hist_exams)

        # Count questions with non-null topic
        total_questions = 0
        mapped_questions = 0
        for ep in payloads:
            for q in ep["questions"]:
                total_questions += 1
                if q["topic"] is not None:
                    mapped_questions += 1
                    assert q["unit"] is not None

        assert mapped_questions > 500, f"Expected >500 mapped questions, got {mapped_questions}/{total_questions}"
    finally:
        db.close()


def test_spcm_dna_analyzer_aggregates_topics() -> None:
    """Verifies that DNAAnalyzerService aggregates topics and produces valid sample size for SPCM."""
    db = SessionLocal()
    try:
        hist_exams = db.query(Exam).filter(Exam.course_id == 13).all()
        payloads = _build_historical_exam_payloads(hist_exams)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(payloads)

        assert dna.sample_size.papers == len(hist_exams)
        assert dna.sample_size.questions > 0
        assert len(dna.topics) >= 20, "Expected at least 20 distinct topics in DNA distribution"
    finally:
        db.close()


def test_spcm_combined_model_produces_topic_predictions() -> None:
    """Verifies that ExamScopeCombinedModel produces topic-level predictions for SPCM."""
    db = SessionLocal()
    try:
        hist_exams = db.query(Exam).filter(Exam.course_id == 13).all()
        payloads = _build_historical_exam_payloads(hist_exams)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(payloads)

        engine = ExamScopeCombinedModel(dna)
        topic_preds = engine.predict(PredictionTarget.TOPIC)
        family_preds = engine.predict(PredictionTarget.FAMILY)

        assert len(topic_preds) >= 20
        assert len(family_preds) > 0
        for p in topic_preds:
            assert getattr(p, "target", "topic") == "topic"
            assert len(p.name) > 0
    finally:
        db.close()


def test_spcm_intelligence_snapshot_reports_topic_mode(client: TestClient) -> None:
    """Verifies that GET /api/intelligence/13 reports prediction_mode='topic'."""
    res = client.get("/api/intelligence/13")
    assert res.status_code == 200
    data = res.json()

    assert data["prediction_mode"] == "topic"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 27
    assert data["topic_predictions_count"] >= 20
    assert len(data["predictions"]) > 0
    assert data["predictions"][0]["category"] == "topic"


def test_calculus_and_chemistry_intelligence_unaffected(client: TestClient) -> None:
    """Verifies that Calculus and Chemistry remain in topic mode and unaffected."""
    res_calc = client.get("/api/intelligence/1")
    assert res_calc.status_code == 200
    data_calc = res_calc.json()
    assert data_calc["prediction_mode"] == "topic"
    assert data_calc["taxonomy_topic_count"] == 19

    res_chem = client.get("/api/intelligence/2")
    assert res_chem.status_code == 200
    data_chem = res_chem.json()
    assert data_chem["prediction_mode"] == "topic"
    assert data_chem["taxonomy_topic_count"] == 45


def test_spcm_study_plan_topic_mode(client: TestClient) -> None:
    """Verifies that GET /api/study/plan/SEM1-SPCM returns topic-mode study priorities with questions."""
    res = client.get("/api/study/plan/SEM1-SPCM")
    assert res.status_code == 200
    data = res.json()

    assert data["course"] == "Semiconductor Physics and Computational Methods"
    assert data["has_topic_taxonomy"] is True
    priorities = data.get("priorities", [])
    assert len(priorities) > 0
    top_p = priorities[0]
    assert "topic" in top_p
    assert top_p["resources"][0]["question_count"] > 0
