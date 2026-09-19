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
    """Verify all 23 courses have registered course assessment plans with source evidence."""
    assert len(COURSE_ASSESSMENT_PLANS) == 23
    for course_id, plan in COURSE_ASSESSMENT_PLANS.items():
        assert plan.course_id == course_id
        assert len(plan.components) >= 2, f"Course {course_id} must define at least 2 components"
        assert plan.source_document is not None and len(plan.source_document) > 0
        for comp in plan.components:
            assert len(comp.syllabus_units) > 0, f"Component {comp.code} for course {course_id} must have units"


def test_assessment_scope_unit_enforcement(db: Session):
    """Verify assessment scopes retrieve the exact units and topics for specific courses."""
    scope_calc_ct1 = get_course_assessment_scope(1, "CT1", db=db)
    assert scope_calc_ct1.in_scope_unit_numbers == {1, 2}
    assert scope_calc_ct1.component_code == "CT1"
    assert len(scope_calc_ct1.in_scope_topic_names) > 0

    scope_calc_ct2 = get_course_assessment_scope(1, "CT2", db=db)
    assert scope_calc_ct2.in_scope_unit_numbers == {3, 4, 5, 6}
    assert scope_calc_ct2.component_code == "CT2"
    assert len(scope_calc_ct2.in_scope_topic_names) > 0

    assert scope_calc_ct1.in_scope_unit_numbers.isdisjoint(scope_calc_ct2.in_scope_unit_numbers)
    assert scope_calc_ct1.in_scope_topic_names.isdisjoint(scope_calc_ct2.in_scope_topic_names)

    scope_bld_ct1 = get_course_assessment_scope(4, "CT1", db=db)
    assert scope_bld_ct1.in_scope_unit_numbers == {1, 2}
    scope_bld_ct2 = get_course_assessment_scope(4, "CT2", db=db)
    assert scope_bld_ct2.in_scope_unit_numbers == {3, 4}


def test_prediction_candidate_restriction_by_scope(db: Session):
    """Verify that predictions under CT1 exclude topics from later units (candidate restriction)."""
    pred_ct1 = get_prediction(subject="1", assessment_cycle="CT1", db=db)
    scope_ct1 = get_course_assessment_scope(1, "CT1", db=db)

    assert pred_ct1["assessment_cycle"] == "CT1"
    assert pred_ct1["assessment_component"] == "CT1"
    assert "assessment_scope" in pred_ct1

    for p in pred_ct1["predictions"]:
        if p.get("target") == "topic" or "topic_id" in p:
            assert p["name"] in scope_ct1.in_scope_topic_names, (
                f"Topic '{p['name']}' belongs to outside units but appeared in CT1 predictions!"
            )


def test_truthful_zero_evidence_scope_reporting(db: Session):
    """Verify that in-scope topics with 0 historical appearances are reported truthfully."""
    snapshot = get_intelligence_snapshot("1", assessment_cycle="CT1", db=db)
    scope = snapshot.get("assessment_scope")
    assert scope is not None
    assert scope["student_cycle"] == "CT1"
    assert scope["component_code"] == "CT1"
    assert scope["total_in_scope_topics"] > 0
    assert "unobserved_in_scope_topics" in scope

    unobserved = scope["unobserved_in_scope_topics"]
    for item in unobserved:
        assert item["status"] == "UNOBSERVED_IN_SCOPE"
        assert item["message"] == "In syllabus scope, but no historical evidence available"

    pred_names = {p["name"] for p in snapshot["predictions"]}
    for item in unobserved:
        assert item["name"] not in pred_names


def test_family_mode_courses_respect_assessment_cycle(db: Session):
    """Verify that courses without topic taxonomy keep family mode and filter exams by cycle."""
    courses = db.query(Course).all()
    family_course = None
    for c in courses:
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
    assert snap["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]

    q_res = get_course_historical_questions("1", assessment_cycle="CT2", db=db)
    assert q_res["assessment_cycle"] == "CT2"
    assert q_res["assessment_component"] == "CT2"

    pred = get_prediction(subject="1", assessment_cycle="CT2", db=db)
    assert pred["assessment_cycle"] == "CT2"
    assert pred["assessment_component"] == "CT2"
    assert pred["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]

    prio = get_study_priorities(course_name="Calculus", assessment_cycle="CT2", db=db)
    assert prio["assessment_cycle"] == "CT2"
    assert prio["assessment_component"] == "CT2"
    assert prio["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]

    practice = get_practice_questions(subject="1", assessment_cycle="CT2")
    assert practice["assessment_cycle"] == "CT2"
    assert practice["assessment_component"] == "CT2"
    assert practice["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]
