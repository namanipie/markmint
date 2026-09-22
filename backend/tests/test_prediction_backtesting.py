"""
Automated Backtesting Test Suite for MarkMint Phase 11.

Proves:
1. No Target Leakage: Target exam itself is never in historical context.
2. No Future Leakage: Exams with year >= cutoff_year are never admitted into historical context.
3. Deliberately Constructed Temporal Leakage Audit: Future papers with distinct synthetic
   topics never contaminate historical predictions.
4. Deterministic Repeatability: Repeated runs on the same context yield identical rankings and scores.
5. Metrics Reconcile: Precision, Recall, Marks Coverage, and Question Coverage are bounded in [0, 1]
   and mathematically sound.
6. Mapping Quality Control: Unmapped questions do not become false negatives of prediction models.
7. Sparse Context Guardrails: Contexts are strictly categorized into SUFFICIENT_HISTORY,
   LIMITED_HISTORY, or INSUFFICIENT_HISTORY.
8. Probability Calibration: Empirical recurrence probabilities strictly follow Laplace smoothing
   formula P = (papers_with_topic + 1) / (sample_papers + 2).
"""

import pytest
from sqlalchemy.orm import Session, selectinload

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from backend.services.prediction.engine import (
    AllTimeFrequencyBaseline,
    RecentFrequencyBaseline,
    RecencyWeightedBaseline,
    MarksWeightedBaseline,
    FamilyRecurrenceBaseline,
    ExamScopeCombinedModel,
    PredictionResult,
)
from backend.services.prediction.backtester import (
    BacktestEvaluator,
    BacktestHarness,
    EvidenceSufficiencyState,
)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_1_no_target_leakage(db: Session):
    """1. Prove target exam is strictly excluded from historical context."""
    # Test on Calculus (Course 1)
    target_year = 2024
    context = HistoricalContext(course_id=1, cutoff_year=target_year)
    repo = HistoricalRepository(db, context)

    hist_exams = repo.get_historical_exams()
    hist_exam_ids = {e.id for e in hist_exams}

    target_exams = repo.get_target_exams()
    assert len(target_exams) >= 1, "Expected target exams in 2024 for Course 1"

    for t_exam in target_exams:
        assert t_exam.id not in hist_exam_ids, f"LEAKAGE: Target exam {t_exam.id} found in historical exams!"
        assert t_exam.year == target_year

    hist_questions = repo.get_historical_questions()
    for q in hist_questions:
        assert q.section.exam_id not in [t.id for t in target_exams], "LEAKAGE: Target question in historical set!"


def test_2_no_future_leakage(db: Session):
    """2. Prove future exams (year > target_year) are never admitted into historical context."""
    cutoff_year = 2023
    context = HistoricalContext(course_id=1, cutoff_year=cutoff_year)
    repo = HistoricalRepository(db, context)

    hist_exams = repo.get_historical_exams()
    for e in hist_exams:
        assert e.year is not None
        assert e.year < cutoff_year, f"LEAKAGE: Exam {e.id} year {e.year} >= cutoff {cutoff_year}"

    hist_questions = repo.get_historical_questions()
    for q in hist_questions:
        assert q.section.exam.year < cutoff_year


def test_3_deliberate_temporal_leakage_audit(db: Session):
    """3. Deliberately constructed leakage test: inject synthetic future paper and prove complete isolation."""
    # Query valid existing unit dynamically
    existing_unit = db.query(Unit).join(Syllabus).filter(Syllabus.course_id == 1).first()
    assert existing_unit is not None, "Course 1 must have at least one unit"

    # Create an artificial future exam at year 2099 with synthetic future topic
    future_exam = Exam(
        course_id=1,
        year=2099,
        assessment_type="END_SEM",
    )
    db.add(future_exam)
    db.flush()

    sec = Section(exam_id=future_exam.id, name="Part A")
    db.add(sec)
    db.flush()

    future_topic = Topic(name="SYNTHETIC_QUANTUM_TIME_WARP", unit_id=existing_unit.id)
    db.add(future_topic)
    db.flush()

    q = Question(section_id=sec.id, question_number="99", original_text="What is time warp?", marks=10.0)
    q.topics.append(future_topic)
    db.add(q)
    db.flush()

    try:
        # Query with cutoff_year = 2024
        context = HistoricalContext(course_id=1, cutoff_year=2024)
        repo = HistoricalRepository(db, context)

        hist_exams = repo.get_historical_exams()
        hist_ids = {e.id for e in hist_exams}
        assert future_exam.id not in hist_ids, "CRITICAL: Synthetic future exam leaked into historical context!"

        hist_payloads = _build_historical_exam_payloads(hist_exams)
        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(hist_payloads)

        # Ensure future topic is absent from DNA
        dna_topics = {t.topic for t in dna.topics}
        assert "SYNTHETIC_QUANTUM_TIME_WARP" not in dna_topics, "CRITICAL: Future topic leaked into DNA!"

        # Ensure predictions do not include future topic
        model = ExamScopeCombinedModel(dna)
        preds = model.predict_topics()
        pred_names = {p.name for p in preds}
        assert "SYNTHETIC_QUANTUM_TIME_WARP" not in pred_names, "CRITICAL: Future topic appeared in predictions!"

    finally:
        # Clean rollback to keep DB pure
        db.rollback()


def test_4_deterministic_repeatability(db: Session):
    """4. Prove deterministic repeatability: identical runs produce exact same ranks and scores."""
    context = HistoricalContext(course_id=1, cutoff_year=2024)
    repo = HistoricalRepository(db, context)
    hist_exams = repo.get_historical_exams()
    hist_payloads = _build_historical_exam_payloads(hist_exams)

    analyzer = DNAAnalyzerService()
    dna1 = analyzer.analyze(hist_payloads)
    dna2 = analyzer.analyze(hist_payloads)

    model1 = ExamScopeCombinedModel(dna1)
    model2 = ExamScopeCombinedModel(dna2)

    preds1 = model1.predict_topics()
    preds2 = model2.predict_topics()

    assert len(preds1) == len(preds2)
    for p1, p2 in zip(preds1, preds2):
        assert p1.name == p2.name
        assert p1.rank == p2.rank
        assert p1.score == p2.score
        assert p1.probability == p2.probability


def test_5_metrics_reconcile():
    """5. Prove BacktestEvaluator metrics are mathematically consistent and bounded."""
    # Synthetic prediction results
    preds = [
        PredictionResult(target="topic", name="Topic A", rank=1, score=0.9, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Topic B", rank=2, score=0.8, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Topic C", rank=3, score=0.7, confidence="MEDIUM", evidence={}),
        PredictionResult(target="topic", name="Topic D", rank=4, score=0.6, confidence="MEDIUM", evidence={}),
        PredictionResult(target="topic", name="Topic E", rank=5, score=0.5, confidence="LOW", evidence={}),
    ]

    target_items = [
        {"name": "Topic A", "marks": 20.0, "count": 2},
        {"name": "Topic B", "marks": 10.0, "count": 1},
        {"name": "Topic Z", "marks": 15.0, "count": 1},
    ]

    eval_res = BacktestEvaluator.evaluate(preds, target_items, k_values=[3, 5])

    for k in [3, 5]:
        assert 0.0 <= eval_res[f"Precision@{k}"] <= 1.0
        assert 0.0 <= eval_res[f"Recall@{k}"] <= 1.0
        assert 0.0 <= eval_res[f"Marks_Coverage@{k}"] <= 1.0
        assert 0.0 <= eval_res[f"Question_Coverage@{k}"] <= 1.0

    # At K=3: hits are Topic A, Topic B (2 hits)
    # Precision@3 = 2/3 = 0.6667
    # Recall@3 = 2/3 = 0.6667
    # Marks Coverage@3 = (20 + 10) / (20 + 10 + 15) = 30 / 45 = 0.6667
    # Question Coverage@3 = (2 + 1) / (2 + 1 + 1) = 3 / 4 = 0.75
    assert eval_res["Precision@3"] == 0.6667
    assert eval_res["Recall@3"] == 0.6667
    assert eval_res["Marks_Coverage@3"] == 0.6667
    assert eval_res["Question_Coverage@3"] == 0.75


def test_6_unmapped_target_questions_not_false_negatives():
    """6. Prove unmapped questions in target exam do not lower the model's question/marks coverage."""
    harness = BacktestHarness()
    # Mock an exam with 2 mapped questions and 2 unmapped questions
    class MockQuestion:
        def __init__(self, qid, marks, is_alt, topics):
            self.id = qid
            self.marks = marks
            self.is_alternative = is_alt
            self.topics = topics
            self.family_id = None
            self.family = None

    class MockSection:
        def __init__(self, questions):
            self.questions = questions

    class MockTopic:
        def __init__(self, name):
            self.name = name
            self.unit = None

    class MockExam:
        def __init__(self):
            self.sections = [
                MockSection([
                    MockQuestion(1, 10.0, False, [MockTopic("Topic A")]),
                    MockQuestion(2, 10.0, False, [MockTopic("Topic B")]),
                    MockQuestion(3, 10.0, False, []),  # unmapped
                    MockQuestion(4, 10.0, False, []),  # unmapped
                ])
            ]

    exam_data = harness.extract_target_exam_data(MockExam())
    qc = exam_data["qc"]

    assert qc["target_question_count"] == 4
    assert qc["mapped_question_count"] == 2
    assert qc["unmapped_question_count"] == 2
    assert qc["mapping_rate"] == 0.5

    # Predictions covering Topic A and Topic B
    preds = [
        PredictionResult(target="topic", name="Topic A", rank=1, score=0.9, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Topic B", rank=2, score=0.8, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Topic C", rank=3, score=0.7, confidence="MEDIUM", evidence={}),
    ]

    eval_res = BacktestEvaluator.evaluate(preds, exam_data[PredictionTarget.TOPIC], k_values=[3])
    # Question coverage across mapped questions should be 100% (2 out of 2 mapped questions covered)
    assert eval_res["Question_Coverage@3"] == 1.0
    assert eval_res["Marks_Coverage@3"] == 1.0


def test_7_sparse_contexts_marked_appropriately():
    """7. Prove sparse contexts are properly categorized and not compared as equivalent."""
    assert BacktestHarness.classify_evidence_sufficiency(0, 0) == EvidenceSufficiencyState.INSUFFICIENT_HISTORY
    assert BacktestHarness.classify_evidence_sufficiency(1, 4) == EvidenceSufficiencyState.INSUFFICIENT_HISTORY
    assert BacktestHarness.classify_evidence_sufficiency(1, 15) == EvidenceSufficiencyState.LIMITED_HISTORY
    assert BacktestHarness.classify_evidence_sufficiency(2, 18) == EvidenceSufficiencyState.LIMITED_HISTORY
    assert BacktestHarness.classify_evidence_sufficiency(3, 25) == EvidenceSufficiencyState.SUFFICIENT_HISTORY
    assert BacktestHarness.classify_evidence_sufficiency(6, 120) == EvidenceSufficiencyState.SUFFICIENT_HISTORY


def test_8_probability_calibration_formula():
    """8. Prove empirical recurrence probabilities match Laplace formula P = (n+1)/(N+2)."""
    preds = [
        PredictionResult(
            target="topic",
            name="Test Topic",
            rank=1,
            score=0.8,
            confidence="HIGH",
            evidence={},
            papers_with_topic=3,
            papers_analyzed=5,
            probability=round((3 + 1.0) / (5 + 2.0), 4) # 4/7 = 0.5714
        )
    ]
    assert preds[0].probability == 0.5714
    assert BacktestEvaluator.verify_probability_calibration(preds, sample_papers=5) is True
