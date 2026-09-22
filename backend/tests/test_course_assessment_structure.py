"""
Comprehensive Test Suite for Course-Specific Assessment Structure Layer.

Verifies:
1. Raw assessment provenance preservation in database
2. Course-specific assessment type normalization (no global FT->CT assumptions)
3. Authoritative course assessment plan registry across all 23 courses
4. Syllabus unit and topic candidate restriction
5. Truthful zero-evidence handling for in-scope topics with no past appearances
6. Family mode courses preserve family predictions under assessment filtering
7. End-to-end API contracts for snapshot, predictions, study-plan, and practice
"""
import pytest
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Topic, Unit, Syllabus
from backend.services.assessment_cycle import (
    AssessmentCycle,
    normalize_assessment_cycle,
    get_raw_types_for_cycle,
    is_exam_in_cycle,
    filter_exams_by_cycle,
)
from backend.services.assessment_plan_registry import (
    COURSE_ASSESSMENT_PLANS,
    get_course_assessment_plan,
    normalize_course_assessment_type,
    get_course_raw_types_for_cycle,
    is_exam_in_course_cycle,
    get_course_assessment_scope,
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


def test_raw_assessment_provenance_preserved(db: Session):
    """Verify that raw Exam.assessment_type strings are preserved in the DB and not overwritten."""
    raw_types_in_db = {
        row[0] for row in db.query(Exam.assessment_type).filter(Exam.assessment_type != None).distinct().all()
    }
    assert any("FT" in t.upper() for t in raw_types_in_db), "Raw FT labels should be preserved"
    assert any("INTERNAL" in t.upper() for t in raw_types_in_db), "Raw INTERNAL labels should be preserved"
    assert any("END" in t.upper() or "DEGREE" in t.upper() for t in raw_types_in_db), "Raw EndSem labels should be preserved"


def test_course_specific_normalization():
    """Verify normalization respects course-specific plans rather than a universal assumption."""
    assert normalize_course_assessment_type(1, "FT2") == "CT2"
    assert normalize_course_assessment_type(1, "FT-II") == "CT2"
    assert normalize_course_assessment_type(1, "FT - II") == "CT2"

    norm_eng_ft4 = normalize_course_assessment_type(15, "FT IV")
    assert norm_eng_ft4 != "CT2", "English FT IV must not be mapped to CT2"
    assert norm_eng_ft4 == "FT_IV"

    assert normalize_course_assessment_type(2, "INTERNAL ASSESSMENT - 1") == "CT1"
    assert normalize_course_assessment_type(2, "INTERNAL ASSESSMENT - I") == "CT1"
    assert normalize_course_assessment_type(2, "INTERNAL ASSESSMENT - I [FJI]") == "CT1"

    assert normalize_course_assessment_type(14, "CT3") == "CT3"


def test_all_courses_have_authoritative_plans():
    """Verify all courses have registered course assessment plans with source evidence."""
    assert len(COURSE_ASSESSMENT_PLANS) >= 23
    for cid in range(1, 24):
        assert cid in COURSE_ASSESSMENT_PLANS, f"Course {cid} must have registered plan"
    for course_id, plan in COURSE_ASSESSMENT_PLANS.items():
        assert plan.course_id == course_id
        assert len(plan.components) >= 2, f"Course {course_id} must define at least 2 components"
        assert plan.source_document is not None and len(plan.source_document) > 0
        for comp in plan.components:
            assert comp.code is not None and len(comp.code) > 0
            if comp.has_authoritative_unit_scope:
                assert comp.syllabus_units is not None and len(comp.syllabus_units) > 0


def test_assessment_scope_unit_enforcement(db: Session):
    """Verify assessment scopes retrieve authoritative intended units or truthful observed scope."""
    # ENDSEM has no authoritative circular in repo; intended scope is None, observed scope covers all 5 units from actual exam questions
    scope_calc_endsem = get_course_assessment_scope(1, "ENDSEM", db=db)
    assert scope_calc_endsem.in_scope_unit_numbers == set()
    assert scope_calc_endsem.has_authoritative_unit_scope is False
    assert scope_calc_endsem.intended_scope is None
    assert scope_calc_endsem.evidence_status == "UNPLANNED_OBSERVED_ONLY"
    assert set(scope_calc_endsem.observed_scope["unit_numbers"]) == {1, 2, 3, 4, 5}
    assert len(scope_calc_endsem.observed_scope["topic_names"]) > 0

    # CT1 has no authoritative circular in repo; intended scope is None, observed scope comes from exam questions
    scope_calc_ct1 = get_course_assessment_scope(1, "CT1", db=db)
    assert scope_calc_ct1.has_authoritative_unit_scope is False
    assert scope_calc_ct1.intended_scope is None
    assert scope_calc_ct1.in_scope_unit_numbers == set()
    assert scope_calc_ct1.observed_scope["unit_numbers"] == [1]
    assert scope_calc_ct1.evidence_status == "UNPLANNED_OBSERVED_ONLY"

    # CT2 has no authoritative circular in repo; observed scope covers units observed on actual CT2 papers
    scope_calc_ct2 = get_course_assessment_scope(1, "CT2", db=db)
    assert scope_calc_ct2.has_authoritative_unit_scope is False
    assert scope_calc_ct2.intended_scope is None
    assert scope_calc_ct2.in_scope_unit_numbers == set()
    assert set(scope_calc_ct2.observed_scope["unit_numbers"]) == {1, 2}


def test_prediction_candidate_restriction_by_scope(db: Session):
    """Verify that predictions under ENDSEM preserve observed topic candidates without artificial restriction."""
    pred_endsem = get_prediction(subject="1", assessment_cycle="ENDSEM", db=db)
    scope_endsem = get_course_assessment_scope(1, "ENDSEM", db=db)

    assert pred_endsem["assessment_cycle"] == "ENDSEM"
    assert pred_endsem["assessment_component"] == "ENDSEM"
    assert "assessment_scope" in pred_endsem
    assert scope_endsem.has_authoritative_unit_scope is False
    assert len(pred_endsem["predictions"]) > 0

    observed_topics = set(scope_endsem.observed_scope["topic_names"])
    for p in pred_endsem["predictions"]:
        if p.get("target") == "topic" or "topic_id" in p:
            assert p["name"] in observed_topics, (
                f"Topic '{p['name']}' not in observed topics for ENDSEM!"
            )


def test_truthful_zero_evidence_scope_reporting(db: Session):
    """Verify that when no authoritative circular exists, unobserved in-scope topics are not fabricated."""
    snapshot = get_intelligence_snapshot("1", assessment_cycle="ENDSEM", db=db)
    scope = snapshot.get("assessment_scope")
    assert scope is not None
    assert scope["student_cycle"] == "ENDSEM"
    assert scope["component_code"] == "ENDSEM"
    assert scope["intended_scope"] is None
    assert scope["evidence_status"] == "UNPLANNED_OBSERVED_ONLY"
    assert scope["total_in_scope_topics"] == 0
    assert len(scope["unobserved_in_scope_topics"]) == 0


def test_family_mode_courses_respect_assessment_cycle(db: Session):
    """Verify that courses without topic taxonomy keep family mode and filter exams by cycle."""
    courses = db.query(Course).all()
    family_course = None
    for c in courses:
        if c.tracks:
            continue
        s = get_intelligence_snapshot(str(c.id), assessment_cycle="ALL", db=db)
        if s.get("prediction_mode") == "family":
            family_course = c
            break

    if family_course:
        snap_all = get_intelligence_snapshot(str(family_course.id), assessment_cycle="ALL", db=db)
        assert snap_all["prediction_mode"] == "family"

        snap_ct1 = get_intelligence_snapshot(str(family_course.id), assessment_cycle="CT1", db=db)
        if snap_ct1["data_availability_status"] == "READY":
            assert snap_ct1["prediction_mode"] == "family"
            assert snap_ct1["assessment_cycle"] == "CT1"
            assert "assessment_scope" in snap_ct1


def test_api_endpoints_expose_assessment_structure(db: Session):
    """Verify that all relevant endpoints return the assessment structure metadata."""
    snap = get_intelligence_snapshot("1", assessment_cycle="CT2", db=db)
    assert snap["assessment_cycle"] == "CT2"
    assert snap["assessment_component"] == "CT2"
    assert "assessment_scope" in snap
    assert snap["assessment_scope"]["evidence_status"] == "UNPLANNED_OBSERVED_ONLY"
    assert set(snap["assessment_scope"]["observed_scope"]["unit_numbers"]) == {1, 2}

    q_res = get_course_historical_questions("1", assessment_cycle="CT2", db=db)
    assert q_res["assessment_cycle"] == "CT2"
    assert q_res["assessment_component"] == "CT2"

    pred = get_prediction(subject="1", assessment_cycle="CT2", db=db)
    assert pred["assessment_cycle"] == "CT2"
    assert pred["assessment_component"] == "CT2"
    assert pred["assessment_scope"]["evidence_status"] == "UNPLANNED_OBSERVED_ONLY"
    assert set(pred["assessment_scope"]["observed_scope"]["unit_numbers"]) == {1, 2}

    prio = get_study_priorities(course_name="Calculus", assessment_cycle="CT2", db=db)
    assert prio["assessment_cycle"] == "CT2"
    assert prio["assessment_component"] == "CT2"
    assert prio["assessment_scope"]["evidence_status"] == "UNPLANNED_OBSERVED_ONLY"
    assert set(prio["assessment_scope"]["observed_scope"]["unit_numbers"]) == {1, 2}

    practice = get_practice_questions(subject="1", assessment_cycle="CT2")
    assert practice["assessment_cycle"] == "CT2"
    assert practice["assessment_component"] == "CT2"
    assert practice["assessment_scope"]["evidence_status"] == "UNPLANNED_OBSERVED_ONLY"
    assert set(practice["assessment_scope"]["observed_scope"]["unit_numbers"]) == {1, 2}
