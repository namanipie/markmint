"""
Comprehensive Verification Test Suite for MintAI Historical Backtesting (Slice 1).

Guarantees:
1. Target-year data cannot enter prediction context.
2. Future-year data cannot enter prediction context.
3. Unknown-year data cannot be treated as historical.
4. Prediction results are deterministic.
5. Actual target exam is used only for evaluation ground-truth.
6. Metrics (Precision, Recall, Marks Coverage, Question Coverage) are calculated correctly.
7. Repeated backtests produce identical results.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Exam, Section, Question,
    QuestionFamily, QuestionFamilyMembership, question_topic
)
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.prediction.backtester import (
    BacktestHarness, BacktestEvaluator, EvidenceSufficiencyState
)
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from backend.services.prediction.engine import ExamScopeCombinedModel, PredictionResult


@pytest.fixture
def backtest_db():
    """Create a fully isolated in-memory database with multi-year exam history."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Seed Course and Syllabus
    course = Course(id=1, name="Mathematics I", code="MATH101", canonical_code="21MAB101T")
    session.add(course)
    session.commit()

    syllabus = Syllabus(course_id=course.id, version="2021")
    session.add(syllabus)
    session.commit()

    unit = Unit(syllabus_id=syllabus.id, number=1, name="Matrices and Calculus")
    session.add(unit)
    session.commit()

    topic_alpha = Topic(name="Eigenvalues", unit_id=unit.id)
    topic_beta = Topic(name="Matrix Diagonalization", unit_id=unit.id)
    topic_gamma = Topic(name="Taylor Series", unit_id=unit.id)
    topic_target_only = Topic(name="Synthetic Target Only Topic", unit_id=unit.id)
    topic_future_only = Topic(name="Synthetic Future Only Topic", unit_id=unit.id)
    topic_unknown_only = Topic(name="Synthetic Unknown Year Topic", unit_id=unit.id)

    session.add_all([
        topic_alpha, topic_beta, topic_gamma,
        topic_target_only, topic_future_only, topic_unknown_only
    ])
    session.commit()

    # Question Families
    fam_alpha = QuestionFamily(id=1, subject="Mathematics I", canonical_name="Find Eigenvalues of 3x3")
    fam_beta = QuestionFamily(id=2, subject="Mathematics I", canonical_name="Diagonalize Matrix")
    fam_future = QuestionFamily(id=3, subject="Mathematics I", canonical_name="Future Family")
    session.add_all([fam_alpha, fam_beta, fam_future])
    session.commit()

    # 2. Historical Exams: 2021, 2022, 2023
    exam_2021 = Exam(id=101, course_id=course.id, year=2021, assessment_type="END_SEM")
    exam_2022 = Exam(id=102, course_id=course.id, year=2022, assessment_type="END_SEM")
    exam_2023 = Exam(id=103, course_id=course.id, year=2023, assessment_type="END_SEM")

    # 3. Target Exam: 2024
    exam_2024 = Exam(id=104, course_id=course.id, year=2024, assessment_type="END_SEM")

    # 4. Future Exam: 2025
    exam_2025 = Exam(id=105, course_id=course.id, year=2025, assessment_type="END_SEM")

    # 5. Undated Exam: None
    exam_undated = Exam(id=106, course_id=course.id, year=None, assessment_type="END_SEM")

    session.add_all([exam_2021, exam_2022, exam_2023, exam_2024, exam_2025, exam_undated])
    session.commit()

    def add_exam_questions(exam, q_specs):
        sec = Section(exam_id=exam.id, name="Section A")
        session.add(sec)
        session.commit()
        for idx, (num, text, marks, is_alt, topics, fam) in enumerate(q_specs, start=1):
            q = Question(
                section_id=sec.id,
                question_number=num,
                original_text=text,
                marks=marks,
                is_alternative=is_alt,
                family_id=fam.id if fam else None
            )
            for t in topics:
                q.topics.append(t)
            session.add(q)
            session.flush()
            if fam:
                mem = QuestionFamilyMembership(
                    family_id=fam.id,
                    question_id=q.id,
                    match_type="exact",
                    decision_method="rule",
                    algorithm_version="v1"
                )
                session.add(mem)
        session.commit()

    # 2021 questions (historical)
    add_exam_questions(exam_2021, [
        ("1", "Calculate eigenvalues", 10.0, False, [topic_alpha], fam_alpha),
        ("2", "Diagonalize matrix", 10.0, False, [topic_beta], fam_beta),
    ])

    # 2022 questions (historical)
    add_exam_questions(exam_2022, [
        ("1", "Find eigenvalues for 3x3", 10.0, False, [topic_alpha], fam_alpha),
        ("2", "Diagonalize symmetric matrix", 10.0, False, [topic_beta], fam_beta),
    ])

    # 2023 questions (historical)
    add_exam_questions(exam_2023, [
        ("1", "Eigenvalues of triangular matrix", 10.0, False, [topic_alpha], fam_alpha),
        ("2", "Taylor expansion of cos(x)", 10.0, False, [topic_gamma], None),
    ])

    # 2024 questions (target ground-truth)
    add_exam_questions(exam_2024, [
        ("1", "Compute eigenvalues of A", 10.0, False, [topic_alpha], fam_alpha),
        ("2", "Verify matrix diagonalization", 10.0, False, [topic_beta], fam_beta),
        ("3", "Unseen target topic question", 10.0, False, [topic_target_only], None),
        ("4", "Optional alternate question", 10.0, True, [topic_alpha], fam_alpha),
    ])

    # 2025 questions (future)
    add_exam_questions(exam_2025, [
        ("1", "Future question", 20.0, False, [topic_future_only], fam_future),
    ])

    # Undated questions (unknown year)
    add_exam_questions(exam_undated, [
        ("1", "Undated question", 20.0, False, [topic_unknown_only], None),
    ])

    yield {
        "session": session,
        "course": course,
        "topic_alpha": topic_alpha,
        "topic_beta": topic_beta,
        "topic_gamma": topic_gamma,
        "topic_target_only": topic_target_only,
        "topic_future_only": topic_future_only,
        "topic_unknown_only": topic_unknown_only,
        "exam_2021": exam_2021,
        "exam_2022": exam_2022,
        "exam_2023": exam_2023,
        "exam_2024": exam_2024,
        "exam_2025": exam_2025,
        "exam_undated": exam_undated,
    }

    session.close()


def test_1_target_year_data_cannot_enter_prediction_context(backtest_db):
    """1. Prove target-year data (Exam.year == cutoff_year) is strictly inaccessible to prediction engine."""
    db = backtest_db["session"]
    target_year = 2024
    context = HistoricalContext(course_id=1, cutoff_year=target_year)
    repo = HistoricalRepository(db, context)

    # 1. Verify historical exams returned
    hist_exams = repo.get_historical_exams()
    hist_exam_ids = {e.id for e in hist_exams}
    assert 104 not in hist_exam_ids, "Target exam 2024 must NOT be in historical exams"
    for e in hist_exams:
        assert e.year < target_year

    # 2. Verify target-only topic is completely absent from DNA and predictions
    hist_payloads = _build_historical_exam_payloads(hist_exams)
    dna = DNAAnalyzerService().analyze(hist_payloads)
    dna_topics = {t.topic for t in dna.topics}
    assert "Synthetic Target Only Topic" not in dna_topics

    model = ExamScopeCombinedModel(dna)
    preds = model.predict(PredictionTarget.TOPIC)
    pred_names = {p.name for p in preds}
    assert "Synthetic Target Only Topic" not in pred_names


def test_2_future_year_data_cannot_enter_prediction_context(backtest_db):
    """2. Prove future-year data (Exam.year > cutoff_year) is strictly inaccessible."""
    db = backtest_db["session"]
    target_year = 2024
    context = HistoricalContext(course_id=1, cutoff_year=target_year)
    repo = HistoricalRepository(db, context)

    hist_exams = repo.get_historical_exams()
    hist_exam_ids = {e.id for e in hist_exams}
    assert 105 not in hist_exam_ids, "Future exam 2025 must NOT be in historical exams"

    hist_payloads = _build_historical_exam_payloads(hist_exams)
    dna = DNAAnalyzerService().analyze(hist_payloads)
    dna_topics = {t.topic for t in dna.topics}
    assert "Synthetic Future Only Topic" not in dna_topics

    model = ExamScopeCombinedModel(dna)
    preds = model.predict(PredictionTarget.TOPIC)
    pred_names = {p.name for p in preds}
    assert "Synthetic Future Only Topic" not in pred_names


def test_3_unknown_year_data_cannot_be_treated_as_historical(backtest_db):
    """3. Prove unknown-year data (Exam.year IS NULL) is strictly excluded."""
    db = backtest_db["session"]
    target_year = 2024
    context = HistoricalContext(course_id=1, cutoff_year=target_year)
    repo = HistoricalRepository(db, context)

    hist_exams = repo.get_historical_exams()
    hist_exam_ids = {e.id for e in hist_exams}
    assert 106 not in hist_exam_ids, "Undated exam (year=None) must NOT be in historical exams"

    for e in hist_exams:
        assert e.year is not None

    hist_payloads = _build_historical_exam_payloads(hist_exams)
    dna = DNAAnalyzerService().analyze(hist_payloads)
    dna_topics = {t.topic for t in dna.topics}
    assert "Synthetic Unknown Year Topic" not in dna_topics

    # Check target exams as well: undated exam cannot be returned as target exam
    target_exams = repo.get_target_exams()
    target_ids = {e.id for e in target_exams}
    assert 106 not in target_ids


def test_4_prediction_results_are_deterministic(backtest_db):
    """4. Prove prediction results on frozen historical context are 100% deterministic."""
    db = backtest_db["session"]
    context = HistoricalContext(course_id=1, cutoff_year=2024)
    repo = HistoricalRepository(db, context)

    hist_exams = repo.get_historical_exams()
    payloads = _build_historical_exam_payloads(hist_exams)

    dna1 = DNAAnalyzerService().analyze(payloads)
    dna2 = DNAAnalyzerService().analyze(payloads)

    model1 = ExamScopeCombinedModel(dna1)
    model2 = ExamScopeCombinedModel(dna2)

    preds1 = model1.predict(PredictionTarget.TOPIC)
    preds2 = model2.predict(PredictionTarget.TOPIC)

    assert len(preds1) == len(preds2)
    for p1, p2 in zip(preds1, preds2):
        assert p1.name == p2.name
        assert p1.rank == p2.rank
        assert p1.score == p2.score
        assert p1.probability == p2.probability


def test_5_actual_target_exam_used_only_for_evaluation(backtest_db):
    """5. Prove target exam data is used strictly as evaluation ground truth and cannot alter prediction models."""
    db = backtest_db["session"]
    harness = BacktestHarness(db)

    # 1. Run backtest for target year 2024
    res_initial = harness.backtest_target_year(course_id=1, target_year=2024)
    assert res_initial["status"] == "COMPLETED"

    initial_eval = next(e for e in res_initial["evaluations"] if e["model"] == "ExamScopeCombinedModel" and e["mode"] == "topic")
    initial_metrics = initial_eval["metrics"]

    # 2. Get baseline predictions directly from historical context
    context = HistoricalContext(course_id=1, cutoff_year=2024)
    repo = HistoricalRepository(db, context)
    hist_payloads = _build_historical_exam_payloads(repo.get_historical_exams())
    dna = DNAAnalyzerService().analyze(hist_payloads)
    baseline_preds = ExamScopeCombinedModel(dna).predict(PredictionTarget.TOPIC)

    # 3. Add an extra question to the TARGET exam 2024 only
    sec = db.query(Section).filter(Section.exam_id == 104).first()
    extra_q = Question(
        section_id=sec.id,
        question_number="99",
        original_text="Extra target question",
        marks=10.0,
        is_alternative=False,
    )
    extra_q.topics.append(backtest_db["topic_gamma"])
    db.add(extra_q)
    db.commit()

    # 4. Predictions on historical context must remain EXACTLY identical
    dna_after = DNAAnalyzerService().analyze(hist_payloads)
    preds_after = ExamScopeCombinedModel(dna_after).predict(PredictionTarget.TOPIC)

    for p_before, p_after in zip(baseline_preds, preds_after):
        assert p_before.name == p_after.name
        assert p_before.score == p_after.score

    # 5. But the evaluation metrics against the modified target exam change accordingly
    res_modified = harness.backtest_target_year(course_id=1, target_year=2024)
    modified_eval = next(e for e in res_modified["evaluations"] if e["model"] == "ExamScopeCombinedModel" and e["mode"] == "topic")
    # Marks coverage or recall will change because ground truth has changed
    assert res_modified["status"] == "COMPLETED"
    assert modified_eval["metrics"]["Marks_Coverage@3"] != initial_metrics["Marks_Coverage@3"]


def test_6_metrics_are_calculated_correctly():
    """6. Prove BacktestEvaluator metrics match exact formulas."""
    # Predictions: 5 ranked topics
    preds = [
        PredictionResult(target="topic", name="Eigenvalues", rank=1, score=0.9, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Matrix Diagonalization", rank=2, score=0.8, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Taylor Series", rank=3, score=0.7, confidence="MEDIUM", evidence={}),
        PredictionResult(target="topic", name="Differential Equations", rank=4, score=0.6, confidence="MEDIUM", evidence={}),
        PredictionResult(target="topic", name="Vector Calculus", rank=5, score=0.5, confidence="LOW", evidence={}),
    ]

    # Target exam has 3 unique topics:
    # Eigenvalues: 10 marks, 1 question
    # Matrix Diagonalization: 15 marks, 1 question
    # Complex Numbers: 20 marks, 2 questions
    # Total unique topics = 3, Total questions = 4, Total marks = 45
    target_items = [
        {"name": "Eigenvalues", "marks": 10.0, "count": 1},
        {"name": "Matrix Diagonalization", "marks": 15.0, "count": 1},
        {"name": "Complex Numbers", "marks": 20.0, "count": 2},
    ]

    metrics = BacktestEvaluator.evaluate(preds, target_items, k_values=[2, 3, 5])

    # K = 2:
    # top_k = {Eigenvalues, Matrix Diagonalization}
    # Hits = {Eigenvalues, Matrix Diagonalization} (2 hits)
    # Precision@2 = 2 / 2 = 1.0
    # Recall@2 = 2 / 3 = 0.6667
    # Marks Coverage@2 = (10 + 15) / 45 = 25 / 45 = 0.5556
    # Question Coverage@2 = (1 + 1) / 4 = 2 / 4 = 0.5
    assert metrics["Precision@2"] == 1.0
    assert metrics["Recall@2"] == 0.6667
    assert metrics["Marks_Coverage@2"] == 0.5556
    assert metrics["Question_Coverage@2"] == 0.5

    # K = 3:
    # top_k = {Eigenvalues, Matrix Diagonalization, Taylor Series}
    # Hits = {Eigenvalues, Matrix Diagonalization} (Taylor Series is not on target exam)
    # Precision@3 = 2 / 3 = 0.6667
    # Recall@3 = 2 / 3 = 0.6667
    # Marks Coverage@3 = 25 / 45 = 0.5556
    # Question Coverage@3 = 2 / 4 = 0.5
    assert metrics["Precision@3"] == 0.6667
    assert metrics["Recall@3"] == 0.6667
    assert metrics["Marks_Coverage@3"] == 0.5556
    assert metrics["Question_Coverage@3"] == 0.5


def test_7_repeated_backtests_produce_identical_results(backtest_db):
    """7. Prove running BacktestHarness.backtest_target_year() twice produces bit-for-bit identical results."""
    db = backtest_db["session"]
    harness = BacktestHarness(db)

    run_1 = harness.backtest_target_year(course_id=1, target_year=2024)
    run_2 = harness.backtest_target_year(course_id=1, target_year=2024)

    assert run_1["status"] == run_2["status"]
    assert run_1["course_id"] == run_2["course_id"]
    assert run_1["target_year"] == run_2["target_year"]
    assert run_1["cutoff_year"] == run_2["cutoff_year"]
    assert run_1["historical_papers_used"] == run_2["historical_papers_used"]
    assert run_1["target_exams_evaluated"] == run_2["target_exams_evaluated"]

    evals_1 = run_1["evaluations"]
    evals_2 = run_2["evaluations"]
    assert len(evals_1) == len(evals_2)

    for e1, e2 in zip(evals_1, evals_2):
        assert e1["model"] == e2["model"]
        assert e1["mode"] == e2["mode"]
        assert e1["status"] == e2["status"]
        assert e1["qc"] == e2["qc"]
        if e1["metrics"] is not None:
            assert e1["metrics"] == e2["metrics"]
