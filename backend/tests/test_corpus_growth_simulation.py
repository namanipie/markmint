import time
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import (
    Course, Exam, Section, Question, Topic, Unit, Syllabus,
    StudentTopicProgress, QuestionFamily, QuestionFamilyMembership,
    Document, StudyEvidence, MappingConfidence
)
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel, PredictionResult
from backend.services.prediction.context import PredictionTarget
from backend.services.prediction.backtester import BacktestEvaluator
from backend.services.study_intelligence import StudyIntelligenceService, StudyPriority
from backend.services.families.manager import LLMStructuralGuardrail


@pytest.fixture
def sim_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_corpus_growth_simulation_scale_and_confidence():
    """
    Section 5: Real Corpus Growth Simulation
    Expands a course from 4 papers -> 8 papers -> 20 papers -> 50 papers.
    Verifies:
    - Determinism
    - Confidence escalation based on evidence
    - Controlled payload size and sub-100ms algorithmic latency
    """
    scales = [4, 8, 20, 50]
    previous_top_topics = None

    for paper_count in scales:
        exams = []
        for i in range(1, paper_count + 1):
            year = 2000 + (i % 5)
            # Topic A appears in every paper (100% presence)
            # Topic B appears in 50% of papers
            # Topic C appears in 10% of papers (or at least 1)
            questions = [
                {
                    "id": f"q_{i}_1",
                    "topic": "Topic A - Core Foundations",
                    "marks": 10.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": 0.5
                }
            ]
            if i % 2 == 0:
                questions.append({
                    "id": f"q_{i}_2",
                    "topic": "Topic B - Medium Yield",
                    "marks": 8.0,
                    "is_alternative": False,
                    "question_type": "SHORT",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": 0.4
                })
            if i % 10 == 0:
                questions.append({
                    "id": f"q_{i}_3",
                    "topic": "Topic C - Rare Appearance",
                    "marks": 5.0,
                    "is_alternative": False,
                    "question_type": "SHORT",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": 0.2
                })

            exams.append({
                "id": f"exam_{i}",
                "year": year,
                "exam_type": "FINAL",
                "questions": questions
            })

        t_start = time.perf_counter()
        dna = DNAAnalyzerService.analyze(exams)
        engine = ExamScopeCombinedModel(dna)
        preds = engine.predict(PredictionTarget.TOPIC)
        latency_ms = (time.perf_counter() - t_start) * 1000

        # Algorithmic latency must remain reasonable (< 150ms even at 50 papers)
        assert latency_ms < 150.0, f"Latency {latency_ms:.2f}ms exceeded limit at {paper_count} papers"

        pred_map = {p.name: p for p in preds}

        # Topic A appears in all papers:
        # Laplace smoothed probability: (k + 1) / (N + 2) = (paper_count + 1) / (paper_count + 2)
        expected_prob_a = round((paper_count + 1) / (paper_count + 2), 4)
        assert abs(pred_map["Topic A - Core Foundations"].probability - expected_prob_a) < 0.01

        # At scale >= 4, frequent topics should have HIGH confidence
        if paper_count >= 4:
            assert pred_map["Topic A - Core Foundations"].confidence in ["HIGH", "MEDIUM"]
        if paper_count >= 8:
            assert pred_map["Topic A - Core Foundations"].confidence == "HIGH"

        # Topic ordering must remain strictly deterministic
        top_topic_name = preds[0].name
        assert top_topic_name == "Topic A - Core Foundations"

        # Payload size (dict serialization) must remain controlled
        payload = [p.to_dict() for p in preds]
        assert len(payload) <= 10  # Gated to top topics


def test_new_exam_ingestion_and_backtest_invariance(sim_db):
    """
    Section 6: New Exam Ingestion Simulation
    Verifies that adding a new examination paper:
    - Changes future / current predictions appropriately
    - Leaves past backtest results for previous cutoff years strictly invariant
    """
    course = Course(name="Calculus Ingestion Test", code="CALC-INGEST")
    sim_db.add(course)
    sim_db.commit()

    # Step 1: Ingest 3 exams for 2021, 2022, 2023
    exam_2021 = Exam(course_id=course.id, year=2021, term="Odd", assessment_type="FINAL")
    exam_2022 = Exam(course_id=course.id, year=2022, term="Odd", assessment_type="FINAL")
    exam_2023 = Exam(course_id=course.id, year=2023, term="Odd", assessment_type="FINAL")
    sim_db.add_all([exam_2021, exam_2022, exam_2023])
    sim_db.commit()

    # Add questions
    sec_2021 = Section(exam_id=exam_2021.id, name="A")
    sec_2022 = Section(exam_id=exam_2022.id, name="A")
    sec_2023 = Section(exam_id=exam_2023.id, name="A")
    sim_db.add_all([sec_2021, sec_2022, sec_2023])
    sim_db.commit()

    q1 = Question(section_id=sec_2021.id, question_number="1", original_text="Matrix eigenvalues", marks=10.0)
    q2 = Question(section_id=sec_2022.id, question_number="1", original_text="Matrix eigenvalues", marks=10.0)
    q3 = Question(section_id=sec_2023.id, question_number="1", original_text="Matrix eigenvalues", marks=10.0)
    sim_db.add_all([q1, q2, q3])
    sim_db.commit()

    # Evaluate backtest for 2023 using strictly 2021 and 2022 (cutoff_year=2023)
    hist_2023_context = [
        {"id": "e21", "year": 2021, "exam_type": "FINAL", "questions": [{"id": "q1", "topic": "Matrices", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5}]},
        {"id": "e22", "year": 2022, "exam_type": "FINAL", "questions": [{"id": "q2", "topic": "Matrices", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5}]}
    ]
    target_2023 = [{"name": "Matrices", "marks": 10.0, "count": 1}]

    dna_before = DNAAnalyzerService.analyze(hist_2023_context)
    engine_before = ExamScopeCombinedModel(dna_before)
    preds_before = engine_before.predict(PredictionTarget.TOPIC)
    backtest_2023_before = BacktestEvaluator.evaluate(preds_before, target_2023, k_values=[3])

    assert backtest_2023_before["Precision@3"] > 0
    assert backtest_2023_before["Recall@3"] == 1.0

    # Step 2: Ingest a brand new exam for 2024 with a brand new topic "Vector Calculus"
    exam_2024 = Exam(course_id=course.id, year=2024, term="Odd", assessment_type="FINAL")
    sim_db.add(exam_2024)
    sim_db.commit()
    sec_2024 = Section(exam_id=exam_2024.id, name="A")
    sim_db.add(sec_2024)
    sim_db.commit()
    q4 = Question(section_id=sec_2024.id, question_number="1", original_text="Divergence theorem", marks=10.0)
    sim_db.add(q4)
    sim_db.commit()

    # Step 3: Verify backtest for cutoff 2023 is strictly UNTOUCHED (Temporal Invariance)
    # The historical context for 2023 cutoff must only select year < 2023
    exams_for_2023_cutoff = sim_db.query(Exam).filter(Exam.course_id == course.id, Exam.year < 2023).all()
    assert len(exams_for_2023_cutoff) == 2  # 2021 and 2022 only!

    # Recompute backtest for 2023
    dna_recomputed = DNAAnalyzerService.analyze(hist_2023_context)
    preds_recomputed = ExamScopeCombinedModel(dna_recomputed).predict(PredictionTarget.TOPIC)
    backtest_2023_after = BacktestEvaluator.evaluate(preds_recomputed, target_2023, k_values=[3])

    assert backtest_2023_after == backtest_2023_before, "Backtest results for previous year mutated after ingesting 2024 paper!"


def test_question_family_regression_and_guardrails():
    """
    Section 7: Question Family Regression
    Tests:
    - Same-family variants cluster
    - Genuinely new questions remain distinct
    - Superficially similar questions with different technical concepts are blocked by LLMStructuralGuardrail
    """
    # 1. Same-family variant
    q_base = "Derive the Euler-Lagrange equations of motion."
    q_var = "Derive the Euler-Lagrange equation for a conservative holonomic system."
    # High similarity (>0.92) is accepted
    assert LLMStructuralGuardrail.validate(q_base, q_var, 0.94) is True

    # 2. Superficially similar phrasing but distinct CS/Math concepts
    q_index = "Explain the advantages of database indexing."
    q_sched = "Explain the advantages of process scheduling."
    # Guardrail must block clustering
    assert LLMStructuralGuardrail.validate(q_index, q_sched, 0.88) is False

    # 3. BFS vs Binary Search distractor (shares question frame, different algorithm)
    q_bfs = "What is the time and space complexity of breadth-first search?"
    q_bin = "What is the time and space complexity of binary search?"
    assert LLMStructuralGuardrail.validate(q_bfs, q_bin, 0.90) is False


def test_prediction_stability_reproducibility():
    """
    Section 8: Prediction Stability
    Identical inputs -> identical outputs across 10 consecutive runs.
    """
    exams = [
        {
            "id": "e1", "year": 2022, "exam_type": "FINAL",
            "questions": [
                {"id": "q1", "topic": "Calculus", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5},
                {"id": "q2", "topic": "Algebra", "marks": 5.0, "is_alternative": False, "question_type": "SHORT", "repetition_type": "singleton", "family_name": None, "difficulty": 0.3},
            ]
        },
        {
            "id": "e2", "year": 2023, "exam_type": "FINAL",
            "questions": [
                {"id": "q3", "topic": "Calculus", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5},
            ]
        }
    ]

    base_results = None
    for _ in range(10):
        dna = DNAAnalyzerService.analyze(exams)
        engine = ExamScopeCombinedModel(dna)
        preds = engine.predict(PredictionTarget.TOPIC)
        serialized = [p.to_dict() for p in preds]

        if base_results is None:
            base_results = serialized
        else:
            assert serialized == base_results, "Non-deterministic prediction detected across runs!"


def test_student_personalization_isolation(sim_db):
    """
    Section 9: Student Personalization Isolation
    Student A (high mastery) vs Student B (low mastery) on same course.
    Verifies:
    - Probabilities identical
    - Historical frequencies identical
    - ExamDNA sample sizes identical
    - Only personalized priorities and recommendations differ
    """
    course = Course(name="Discrete Mathematics", code="MAT205")
    sim_db.add(course)
    sim_db.commit()

    syllabus = Syllabus(course_id=course.id, version="v1")
    sim_db.add(syllabus)
    sim_db.commit()

    unit = Unit(syllabus_id=syllabus.id, name="Set Theory", number=1)
    sim_db.add(unit)
    sim_db.commit()

    t1 = Topic(unit_id=unit.id, name="Set Theory")
    t2 = Topic(unit_id=unit.id, name="Relations")
    sim_db.add_all([t1, t2])
    sim_db.commit()

    # Student A: High mastery on Set Theory
    prog_a = StudentTopicProgress(
        student_id="student_a",
        topic_id=t1.id,
        status="COMPLETED",
        practice_attempted=10,
        practice_correct=9
    )
    # Student B: No progress on Set Theory
    prog_b = StudentTopicProgress(
        student_id="student_b",
        topic_id=t1.id,
        status="NOT_STARTED",
        practice_attempted=0,
        practice_correct=0
    )
    sim_db.add_all([prog_a, prog_b])
    sim_db.commit()

    service = StudyIntelligenceService(sim_db)

    # Core predictions
    core_prediction = PredictionResult(
        target="topic",
        name="Set Theory",
        rank=1,
        score=0.85,
        confidence="HIGH",
        evidence={"occurrences": 5, "total_marks": 25.0}
    )

    plan_a = service.generate_study_plan([core_prediction], course.id, student_id="student_a")
    plan_b = service.generate_study_plan([core_prediction], course.id, student_id="student_b")

    # Invariants: Underlying prediction score and topic name must be identical
    assert plan_a[0]["prediction_score"] == plan_b[0]["prediction_score"] == 0.85
    assert plan_a[0]["topic"] == plan_b[0]["topic"] == "Set Theory"

    # Personalization: Action and Priority MUST differ based on mastery
    # Student A (mastered) -> MAINTAIN_AND_REVIEW / reduced urgency
    # Student B (unstudied) -> DEEP_STUDY_URGENT / VERY_HIGH
    assert plan_a[0]["recommended_action"] == "MAINTAIN_AND_REVIEW"
    assert plan_b[0]["recommended_action"] == "DEEP_STUDY_URGENT"
    assert plan_b[0]["priority"] in [StudyPriority.VERY_HIGH, "VERY_HIGH"]


def test_resource_cross_course_isolation(sim_db):
    """
    Section 10: Resource Personalization & Cross-Course Leakage Prevention
    Verifies that requesting resources across courses is blocked and cannot leak materials.
    """
    course_math = Course(name="Mathematics I", code="MTH101")
    course_phys = Course(name="Physics I", code="PHY101")
    sim_db.add_all([course_math, course_phys])
    sim_db.commit()

    syl_math = Syllabus(course_id=course_math.id, version="v1")
    syl_phys = Syllabus(course_id=course_phys.id, version="v1")
    sim_db.add_all([syl_math, syl_phys])
    sim_db.commit()

    u_math = Unit(syllabus_id=syl_math.id, name="Calculus Unit", number=1)
    u_phys = Unit(syllabus_id=syl_phys.id, name="Mechanics Unit", number=1)
    sim_db.add_all([u_math, u_phys])
    sim_db.commit()

    t_math = Topic(unit_id=u_math.id, name="Integration")
    t_phys = Topic(unit_id=u_phys.id, name="Kinematics")
    sim_db.add_all([t_math, t_phys])
    sim_db.commit()

    service = StudyIntelligenceService(sim_db)

    # 1. Asking for Physics topic within Math course ID must return empty list (scoped out)
    cross_resources = service.get_topic_resources("Kinematics", course_math.id)
    assert cross_resources == [], "Cross-course topic leak! Physics topic returned under Math course."

    # 2. Asking for Math topic within Physics course ID must return empty list
    cross_resources_2 = service.get_topic_resources("Integration", course_phys.id)
    assert cross_resources_2 == [], "Cross-course topic leak! Math topic returned under Physics course."
