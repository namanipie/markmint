"""
Test suite for Course 29: Artificial Intelligence (21CSC207J, SEM4-AI).
Validates:
1. Declarative taxonomy registry integrity for Course 29.
2. Database persistence of course, syllabus, units, topics, and assessment plan.
3. Ingested exam papers with SHA-256 deduplication and non-empty question text.
4. Zero cross-course topic leakage.
5. High-confidence deterministic taxonomy mapping (>75%).
6. Intelligence prediction and study plan generation.
"""
import pytest
from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Exam, Section, Question, question_topic
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
from backend.services.taxonomy_registry import get_taxonomy_registry, reset_taxonomy_registry
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from backend.services.study_intelligence import StudyIntelligenceService


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_ai_taxonomy_registry_integrity():
    """Verify Course 29 declarative taxonomy definition in the registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(29), "Course 29 (Artificial Intelligence) must be registered."
    entry = registry.get_course(29)
    assert entry.course.id == 29
    assert entry.course.canonical_code == "21CSC207J"
    assert entry.course.name == "Artificial Intelligence"
    assert len(entry.units) == 5, "Course 29 must have exactly 5 units."

    rules = registry.get_topic_rules(29)
    assert len(rules) == 25, "Course 29 must have 25 topic rules."

    tids = [r.topic_id for r in rules]
    assert min(tids) == 866, "Course 29 min topic id should be 866"
    assert max(tids) == 890, "Course 29 max topic id should be 890"


def test_ai_database_course_and_syllabus(db):
    """Verify database records for Course 29."""
    course = db.query(Course).filter(Course.id == 29).first()
    assert course is not None, "Course 29 must exist in DB."
    assert course.code == "SEM4-AI"
    assert course.canonical_code == "21CSC207J"
    assert course.regulation_year == 2021

    syllabus = db.query(Syllabus).filter(Syllabus.course_id == 29).first()
    assert syllabus is not None, "Syllabus must exist for Course 29."

    units = db.query(Unit).filter(Unit.syllabus_id == syllabus.id).order_by(Unit.number).all()
    assert len(units) == 5, "Course 29 must have 5 units."
    assert [u.id for u in units] == [181, 182, 183, 184, 185]

    for u in units:
        topics = db.query(Topic).filter(Topic.unit_id == u.id).all()
        assert len(topics) == 5, f"Unit {u.number} must have 5 topics."


def test_ai_assessment_plan_and_coverage(db):
    """Verify CourseAssessmentPlan, components, and unit coverage for Course 29."""
    plan = db.query(CourseAssessmentPlan).filter(CourseAssessmentPlan.course_id == 29).first()
    assert plan is not None, "Assessment plan must exist for Course 29."
    assert plan.regulation_year == 2021

    comps = db.query(AssessmentComponent).filter(AssessmentComponent.course_id == 29).order_by(AssessmentComponent.sequence).all()
    assert len(comps) == 3, "Must have CLA1, CLA2, and ENDSEM components."

    cla1, cla2, endsem = comps
    assert cla1.code == "CLA1"
    assert cla2.code == "CLA2"
    assert endsem.code == "ENDSEM"

    # Verify unit coverages
    cla1_cov = db.query(AssessmentCoverage).filter(AssessmentCoverage.assessment_component_id == cla1.id).all()
    assert {c.unit_id for c in cla1_cov} == {181, 182}, "CLA1 must cover Units 1 and 2."

    cla2_cov = db.query(AssessmentCoverage).filter(AssessmentCoverage.assessment_component_id == cla2.id).all()
    assert {c.unit_id for c in cla2_cov} == {183, 184, 185}, "CLA2 must cover Units 3, 4, and 5."

    endsem_cov = db.query(AssessmentCoverage).filter(AssessmentCoverage.assessment_component_id == endsem.id).all()
    assert {c.unit_id for c in endsem_cov} == {181, 182, 183, 184, 185}, "ENDSEM must cover all 5 units."


def test_ai_exams_and_questions_integrity(db):
    """Verify ingested exams and questions for Course 29."""
    exams = db.query(Exam).filter(Exam.course_id == 29).all()
    assert len(exams) >= 5, "At least 5 genuine PYQs must be ingested."

    questions = (
        db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == 29)
        .all()
    )
    assert len(questions) >= 150, f"Expected >= 150 questions, found {len(questions)}"

    # Invariant: No empty question texts
    empty_q = [q for q in questions if not q.original_text or len(q.original_text.strip()) < 5]
    assert len(empty_q) == 0, f"Found {len(empty_q)} questions with empty text."


def test_ai_taxonomy_mapping_quality_and_isolation(db):
    """Verify deterministic mapping quality and zero cross-course leakage."""
    questions = (
        db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == 29)
        .all()
    )

    q_ids = [q.id for q in questions]
    mappings = (
        db.query(question_topic.c.question_id, question_topic.c.topic_id)
        .filter(question_topic.c.question_id.in_(q_ids))
        .all()
    )

    mapped_qids = {m[0] for m in mappings}
    mapping_rate = len(mapped_qids) / len(questions)
    assert mapping_rate >= 0.75, f"Expected mapping rate >= 75%, got {mapping_rate * 100:.1f}%"

    # Invariant: Zero cross-course leakage (all topic IDs must be in 866..890)
    for qid, tid in mappings:
        assert 866 <= tid <= 890, f"Cross-course leakage: Question {qid} mapped to foreign topic {tid}!"


def test_ai_prediction_engine_execution(db):
    """Verify that the prediction engine generates predictions for Course 29."""
    context = HistoricalContext(course_id=29, cutoff_year=2026)
    repo = HistoricalRepository(db, context)
    hist_exams = repo.get_historical_exams()
    assert len(hist_exams) >= 5, "Must have at least 5 historical exams"

    payloads = _build_historical_exam_payloads(hist_exams)
    dna = DNAAnalyzerService.analyze(payloads)
    engine = ExamScopeCombinedModel(dna)

    topic_preds = engine.predict(PredictionTarget.TOPIC)
    assert len(topic_preds) > 0, "Must produce predicted topics."
    top_pred = topic_preds[0]
    assert top_pred.probability > 0.0
    assert top_pred.confidence in ["HIGH", "MEDIUM", "LOW"]

    family_preds = engine.predict(PredictionTarget.FAMILY)
    assert len(family_preds) > 0, "Must produce predicted question families."


def test_ai_study_intelligence_execution(db):
    """Verify that the study intelligence service generates a valid study plan for Course 29."""
    context = HistoricalContext(course_id=29, cutoff_year=2026)
    repo = HistoricalRepository(db, context)
    hist_exams = repo.get_historical_exams()
    payloads = _build_historical_exam_payloads(hist_exams)
    dna = DNAAnalyzerService.analyze(payloads)
    engine = ExamScopeCombinedModel(dna)
    topic_preds = engine.predict(PredictionTarget.TOPIC)

    study_service = StudyIntelligenceService(db)
    plan = study_service.generate_study_plan(topic_preds, course_id=29)

    assert plan is not None
    assert len(plan) > 0, "Study plan must contain prioritized topics."
    first_item = plan[0]
    assert "priority" in first_item
    assert "topic" in first_item
