"""
Integration tests for Chemistry topic prediction pipeline.
Verifies that mapped questions feed through DNA analyzer and ExamScopeCombinedModel
without altering underlying formulas or family predictions.
"""
from backend.core.database import SessionLocal
from backend.models.core import Course
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel


def test_chem_exam_payloads_include_mapped_topics() -> None:
    """Verifies that _build_historical_exam_payloads extracts topic and unit for Chemistry."""
    db = SessionLocal()
    try:
        context = HistoricalContext(course_id=2, cutoff_year=2026)
        repo = HistoricalRepository(db, context)
        hist_exams = repo.get_historical_exams()
        assert len(hist_exams) > 0

        payloads = _build_historical_exam_payloads(hist_exams)
        assert len(payloads) == len(hist_exams)

        # Collect all questions across exams
        all_qs = [q for ex in payloads for q in ex["questions"]]
        mapped_qs = [q for q in all_qs if q["topic"] is not None]

        assert len(mapped_qs) > 0, "Mapped Chemistry questions must have non-null 'topic'"
        assert any(q["unit"] is not None for q in mapped_qs), "Mapped questions must have non-null 'unit'"
        sample = mapped_qs[0]
        assert isinstance(sample["topic"], str)
        assert len(sample["topic"]) > 0
    finally:
        db.close()


def test_chem_dna_analyzer_aggregates_topics() -> None:
    """Verifies DNA analyzer computes topic distributions for Chemistry without error."""
    db = SessionLocal()
    try:
        context = HistoricalContext(course_id=2, cutoff_year=2026)
        repo = HistoricalRepository(db, context)
        hist_exams = repo.get_historical_exams()
        payloads = _build_historical_exam_payloads(hist_exams)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(payloads)

        assert dna is not None
        assert dna.sample_size.papers == len(hist_exams)
        assert len(dna.topics) > 0, "DNA must contain topic distributions for Chemistry"
    finally:
        db.close()


def test_chem_combined_model_produces_both_topic_and_family_predictions() -> None:
    """Verifies ExamScopeCombinedModel produces topic predictions and preserves family predictions."""
    db = SessionLocal()
    try:
        context = HistoricalContext(course_id=2, cutoff_year=2026)
        repo = HistoricalRepository(db, context)
        hist_exams = repo.get_historical_exams()
        payloads = _build_historical_exam_payloads(hist_exams)

        dna = DNAAnalyzerService.analyze(payloads)
        engine = ExamScopeCombinedModel(dna)

        topic_preds = engine.predict(PredictionTarget.TOPIC)
        family_preds = engine.predict(PredictionTarget.FAMILY)

        assert len(topic_preds) > 0, "Chemistry must produce topic predictions"
        assert len(family_preds) > 0, "Chemistry must preserve family predictions"

        # Check topic prediction structure
        top_topic = topic_preds[0]
        assert top_topic.target == "topic"
        assert top_topic.score > 0
        assert top_topic.confidence in ["HIGH", "MEDIUM", "LOW"]

        # Check family prediction structure
        top_fam = family_preds[0]
        assert top_fam.target == "family"
        assert top_fam.score > 0
    finally:
        db.close()
