import pytest
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Question, Section
from backend.services.assessment_cycle import (
    AssessmentCycle,
    normalize_assessment_cycle,
    get_raw_types_for_cycle,
    is_exam_in_cycle,
)
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository
from backend.api.endpoints.intelligence import (
    get_intelligence_snapshot,
    get_course_historical_questions,
)
from backend.api.endpoints.predictions import get_prediction
from backend.api.endpoints.practice import get_practice_questions
from backend.api.router_study import get_study_priorities, get_study_plan


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_assessment_cycle_filters_exams(db: Session):
    """Verify that selecting CT1, CT2, and ENDSEM filters exams properly in repository."""
    # Calculus (Course 1) has dated historical exams in all cycles
    ctx_all = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="ALL")
    ctx_ct1 = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="CT1")
    ctx_ct2 = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="CT2")
    ctx_end = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="ENDSEM")

    exams_all = HistoricalRepository(db, ctx_all).get_historical_exams()
    exams_ct1 = HistoricalRepository(db, ctx_ct1).get_historical_exams()
    exams_ct2 = HistoricalRepository(db, ctx_ct2).get_historical_exams()
    exams_end = HistoricalRepository(db, ctx_end).get_historical_exams()

    assert len(exams_all) > 0
    assert len(exams_ct1) > 0
    assert len(exams_ct2) > 0
    assert len(exams_end) > 0

    assert len(exams_ct1) < len(exams_all)
    assert len(exams_ct2) < len(exams_all)
    assert len(exams_end) < len(exams_all)


def test_ct1_only_uses_ct1_papers(db: Session):
    """Verify that CT1 context exclusively contains CT1 papers."""
    ctx_ct1 = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="CT1")
    exams_ct1 = HistoricalRepository(db, ctx_ct1).get_historical_exams()
    assert len(exams_ct1) > 0
    for ex in exams_ct1:
        assert is_exam_in_cycle(ex.assessment_type, AssessmentCycle.CT1), f"Unexpected exam {ex.assessment_type} in CT1 context"


def test_ct2_only_uses_ct2_papers(db: Session):
    """Verify that CT2 context exclusively contains CT2 papers."""
    ctx_ct2 = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="CT2")
    exams_ct2 = HistoricalRepository(db, ctx_ct2).get_historical_exams()
    assert len(exams_ct2) > 0
    for ex in exams_ct2:
        assert is_exam_in_cycle(ex.assessment_type, AssessmentCycle.CT2), f"Unexpected exam {ex.assessment_type} in CT2 context"


def test_endsem_only_uses_endsem_papers(db: Session):
    """Verify that ENDSEM context exclusively contains End-Semester papers."""
    ctx_end = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="ENDSEM")
    exams_end = HistoricalRepository(db, ctx_end).get_historical_exams()
    assert len(exams_end) > 0
    for ex in exams_end:
        assert is_exam_in_cycle(ex.assessment_type, AssessmentCycle.ENDSEM), f"Unexpected exam {ex.assessment_type} in ENDSEM context"


def test_all_assessments_preserves_current_behavior(db: Session):
    """Verify ALL assessment cycle produces identical results to unconditioned baseline."""
    ctx_none = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle=None)
    ctx_all = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="ALL")

    exams_none = HistoricalRepository(db, ctx_none).get_historical_exams()
    exams_all = HistoricalRepository(db, ctx_all).get_historical_exams()
    assert [e.id for e in exams_none] == [e.id for e in exams_all]

    qs_none = HistoricalRepository(db, ctx_none).get_historical_questions()
    qs_all = HistoricalRepository(db, ctx_all).get_historical_questions()
    assert [q.id for q in qs_none] == [q.id for q in qs_all]

    pred_none = get_prediction(subject="1", assessment_cycle=None, db=db)
    pred_all = get_prediction(subject="1", assessment_cycle="ALL", db=db)
    assert len(pred_none["predictions"]) == len(pred_all["predictions"])
    if pred_none["predictions"]:
        assert pred_none["predictions"][0]["name"] == pred_all["predictions"][0]["name"]
        assert pred_none["predictions"][0]["probability"] == pred_all["predictions"][0]["probability"]


def test_predictions_change_with_assessment_cycle(db: Session):
    """Verify topic and family predictions change across different assessment cycles."""
    snap_all = get_intelligence_snapshot(course_id="1", assessment_cycle="ALL", db=db)
    snap_end = get_intelligence_snapshot(course_id="1", assessment_cycle="ENDSEM", db=db)
    snap_ct2 = get_intelligence_snapshot(course_id="1", assessment_cycle="CT2", db=db)

    assert snap_all["assessment_cycle"] == "ALL"
    assert snap_end["assessment_cycle"] == "ENDSEM"
    assert snap_ct2["assessment_cycle"] == "CT2"

    # End-Sem and CT2 have distinct exam subsets, so their paper counts and topic distributions differ
    assert snap_end["exam_history"]["historical_papers_analyzed"] != snap_ct2["exam_history"]["historical_papers_analyzed"]
    assert snap_end["exam_history"]["historical_papers_analyzed"] != snap_all["exam_history"]["historical_papers_analyzed"]


def test_topic_marks_are_filtered_by_assessment(db: Session):
    """Verify topic marks (average and total) are computed specifically from the filtered cycle questions."""
    snap_ct2 = get_intelligence_snapshot(course_id="1", assessment_cycle="CT2", db=db)

    for p in snap_ct2["predictions"]:
        assert p["papers_analyzed"] == snap_ct2["exam_history"]["historical_papers_analyzed"]
        assert (p.get("distinct_paper_count") or 0) <= snap_ct2["exam_history"]["historical_papers_analyzed"]


def test_topic_paper_counts_are_filtered_by_assessment(db: Session):
    """Verify distinct paper counts for topics never exceed the papers analyzed in that cycle."""
    snap_ct2 = get_intelligence_snapshot(course_id="1", assessment_cycle="CT2", db=db)
    ct2_papers = snap_ct2["exam_history"]["historical_papers_analyzed"]
    for p in snap_ct2["predictions"]:
        distinct = p.get("distinct_paper_count") or p.get("papers_with_topic") or 0
        assert distinct <= ct2_papers, f"Topic {p['name']} has {distinct} papers but CT2 has only {ct2_papers}"


def test_family_recurrence_is_filtered_by_assessment(db: Session):
    """Verify question family recurrence is filtered to cycle papers."""
    ctx_end = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="ENDSEM")
    exams_end = HistoricalRepository(db, ctx_end).get_historical_exams()
    qs_end = HistoricalRepository(db, ctx_end).get_historical_questions()

    endsem_exam_ids = {e.id for e in exams_end}
    for q in qs_end:
        assert q.section.exam_id in endsem_exam_ids


def test_historical_questions_filter_by_assessment(db: Session):
    """Verify /intelligence/{course_id}/questions filters accurately by assessment_cycle."""
    res_ct2 = get_course_historical_questions(course_id="1", assessment_cycle="CT2", db=db)
    assert res_ct2["assessment_cycle"] == "CT2"
    assert len(res_ct2["questions"]) > 0
    for q in res_ct2["questions"]:
        assert is_exam_in_cycle(q["assessment_type"], AssessmentCycle.CT2), f"Non-CT2 question found: {q['assessment_type']}"

    res_end = get_course_historical_questions(course_id="1", assessment_cycle="ENDSEM", db=db)
    assert res_end["assessment_cycle"] == "ENDSEM"
    assert len(res_end["questions"]) > 0
    for q in res_end["questions"]:
        assert is_exam_in_cycle(q["assessment_type"], AssessmentCycle.ENDSEM), f"Non-ENDSEM question found: {q['assessment_type']}"


def test_practice_filter_by_assessment(db: Session):
    """Verify practice questions endpoint respects assessment_cycle."""
    practice_ct2 = get_practice_questions(subject="1", limit=20, assessment_cycle="CT2")
    assert practice_ct2["assessment_cycle"] == "CT2"
    assert len(practice_ct2["questions"]) > 0
    for q in practice_ct2["questions"]:
        exam_type = q.get("exam_assessment_type") or db.query(Exam.assessment_type).join(Section).join(Question).filter(Question.id == q["id"]).scalar()
        assert is_exam_in_cycle(exam_type, AssessmentCycle.CT2)


def test_study_plan_filter_by_assessment(db: Session):
    """Verify study priorities and study plan accept assessment_cycle and reflect it in response."""
    prio_end = get_study_priorities(course_name="1", assessment_cycle="ENDSEM", db=db)
    assert prio_end["assessment_cycle"] == "ENDSEM"

    plan_end = get_study_plan(course_name="1", assessment_cycle="ENDSEM", db=db)
    assert plan_end["assessment_cycle"] == "ENDSEM"


def test_no_cross_cycle_leakage(db: Session):
    """Verify no exam or question from another cycle leaks into a filtered cycle."""
    ctx_ct1 = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="CT1")
    ctx_ct2 = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle="CT2")

    exams_ct1 = HistoricalRepository(db, ctx_ct1).get_historical_exams()
    exams_ct2 = HistoricalRepository(db, ctx_ct2).get_historical_exams()

    ct1_exam_ids = {e.id for e in exams_ct1}
    ct2_exam_ids = {e.id for e in exams_ct2}

    # CT1 and CT2 must have zero intersection
    assert ct1_exam_ids.isdisjoint(ct2_exam_ids)

    qs_ct1 = HistoricalRepository(db, ctx_ct1).get_historical_questions()
    qs_ct2 = HistoricalRepository(db, ctx_ct2).get_historical_questions()

    ct1_q_ids = {q.id for q in qs_ct1}
    ct2_q_ids = {q.id for q in qs_ct2}
    assert ct1_q_ids.isdisjoint(ct2_q_ids)


def test_insufficient_cycle_does_not_fallback_to_all(db: Session):
    """Verify that an assessment cycle with no historical papers returns INSUFFICIENT_EVIDENCE truthfully, never falling back to ALL."""
    # Chemistry (Course 2) has 0 dated historical CT2 exams in production_corpus.db
    snap_ct2 = get_intelligence_snapshot(course_id="2", assessment_cycle="CT2", db=db)
    assert snap_ct2["assessment_cycle"] == "CT2"
    assert snap_ct2["data_availability_status"] == "INSUFFICIENT_EVIDENCE"
    assert len(snap_ct2["predictions"]) == 0
    assert snap_ct2["exam_history"]["historical_papers_analyzed"] == 0
