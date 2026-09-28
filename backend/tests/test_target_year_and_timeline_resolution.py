"""
Regression test suite for Phase 4 Slice 2: Target-Year and Timeline Resolution Hygiene.

Verifies:
1. Dead all_years timeline fallback elimination:
   - Future exams (year >= cutoff_year) do NOT appear in prediction timeline
   - Unknown-year exams (year IS NULL) do NOT appear in prediction timeline
   - Existing valid historical years remain accurately represented in timeline
2. Target-year default consistency:
   - Populated corpus derives (max_historical_year + 1)
   - Empty corpus falls back to default 2024
   - Explicit target_year is respected by both endpoints
   - Max historical year derivation is deterministic
   - Unknown-year exams only falls back to 2024
   - Equivalent prediction and intelligence requests resolve identical target_year
"""
import pytest
from sqlalchemy.orm import Session

from backend.models.core import (
    Course,
    CourseTrack,
    Syllabus,
    Unit,
    Topic,
    Exam,
    Section,
    Question,
    QuestionFamily,
    QuestionFamilyMembership,
)
from backend.services.prediction.context import resolve_target_year
from backend.services.intelligence_cache import IntelligenceCacheService
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.endpoints.predictions import get_prediction


@pytest.fixture(autouse=True)
def clean_cache():
    IntelligenceCacheService.clear_memory_cache()
    yield
    IntelligenceCacheService.clear_memory_cache()


def _seed_course_with_taxonomy(db: Session, name: str = "Test Mathematics", code: str = "TMATH101"):
    course = Course(name=name, code=code)
    db.add(course)
    db.commit()

    syllabus = Syllabus(course_id=course.id, version="v1")
    db.add(syllabus)
    db.commit()

    unit = Unit(syllabus_id=syllabus.id, name="Unit 1", number=1, expected_units=5)
    db.add(unit)
    db.commit()

    topic = Topic(unit_id=unit.id, name="Calculus Basics")
    db.add(topic)
    db.commit()

    return course, topic


# ==============================================================================
# 1. TIMELINE RESOLUTION TESTS
# ==============================================================================

def test_timeline_excludes_future_exams(db_session: Session):
    """
    Exams with year >= target_year must NOT appear in topic or family timeline.
    """
    course, topic = _seed_course_with_taxonomy(db_session, "Future Timeline Math", "FTM101")

    fam = QuestionFamily(
        canonical_name="Calculus Limits Question",
        subject=course.name,
        first_seen_year=2021,
        latest_seen_year=2025,
    )
    db_session.add(fam)
    db_session.commit()

    # Historical exam 2020
    e2020 = Exam(course_id=course.id, year=2020, assessment_type="ENDSEM")
    db_session.add(e2020)
    db_session.commit()
    s2020 = Section(exam_id=e2020.id, name="Sec A")
    db_session.add(s2020)
    db_session.commit()
    q2020 = Question(section_id=s2020.id, question_number="1", original_text="Find limit 0", family_id=fam.id)
    q2020.topics.append(topic)
    db_session.add(q2020)

    # Historical exam 2021
    e2021 = Exam(course_id=course.id, year=2021, assessment_type="ENDSEM")
    db_session.add(e2021)
    db_session.commit()
    s2021 = Section(exam_id=e2021.id, name="Sec A")
    db_session.add(s2021)
    db_session.commit()
    q2021 = Question(section_id=s2021.id, question_number="1", original_text="Find limit A", family_id=fam.id)
    q2021.topics.append(topic)
    db_session.add(q2021)

    # Historical exam 2022
    e2022 = Exam(course_id=course.id, year=2022, assessment_type="ENDSEM")
    db_session.add(e2022)
    db_session.commit()
    s2022 = Section(exam_id=e2022.id, name="Sec A")
    db_session.add(s2022)
    db_session.commit()
    q2022 = Question(section_id=s2022.id, question_number="1", original_text="Find limit B", family_id=fam.id)
    q2022.topics.append(topic)
    db_session.add(q2022)

    # Future exam 2025 (target_year will be set to 2023)
    e2025 = Exam(course_id=course.id, year=2025, assessment_type="ENDSEM")
    db_session.add(e2025)
    db_session.commit()
    s2025 = Section(exam_id=e2025.id, name="Sec A")
    db_session.add(s2025)
    db_session.commit()
    q2025 = Question(section_id=s2025.id, question_number="1", original_text="Find limit C", family_id=fam.id)
    q2025.topics.append(topic)
    db_session.add(q2025)
    db_session.commit()

    # Request intelligence with cutoff/target_year=2023
    res = get_intelligence_snapshot(str(course.id), target_year=2023, db=db_session)
    assert "topic_predictions" in res

    topic_preds = res.get("topic_predictions", [])
    assert len(topic_preds) > 0
    t_timeline = topic_preds[0]["timeline"]
    timeline_years = [entry["year"] for entry in t_timeline]

    # Future exam 2025 must NOT appear in timeline
    assert 2025 not in timeline_years
    # Historical years prior to 2023 must appear
    assert timeline_years == [2020, 2021, 2022]


def test_timeline_excludes_unknown_year_exams(db_session: Session):
    """
    Exams with year=None must NOT appear in topic or family timeline.
    """
    course, topic = _seed_course_with_taxonomy(db_session, "Unknown Year Math", "UYM101")

    fam = QuestionFamily(
        canonical_name="Unknown Year Question",
        subject=course.name,
        first_seen_year=2022,
        latest_seen_year=2022,
    )
    db_session.add(fam)
    db_session.commit()

    # Historical exam 2022
    e2022 = Exam(course_id=course.id, year=2022, assessment_type="ENDSEM")
    db_session.add(e2022)
    db_session.commit()
    s2022 = Section(exam_id=e2022.id, name="Sec A")
    db_session.add(s2022)
    db_session.commit()
    q2022 = Question(section_id=s2022.id, question_number="1", original_text="Differentiate X", family_id=fam.id)
    q2022.topics.append(topic)
    db_session.add(q2022)

    # Exam with year=None
    enull = Exam(course_id=course.id, year=None, assessment_type="ENDSEM")
    db_session.add(enull)
    db_session.commit()
    snull = Section(exam_id=enull.id, name="Sec A")
    db_session.add(snull)
    db_session.commit()
    qnull = Question(section_id=snull.id, question_number="1", original_text="Differentiate Y", family_id=fam.id)
    qnull.topics.append(topic)
    db_session.add(qnull)
    db_session.commit()

    res = get_intelligence_snapshot(str(course.id), target_year=2023, db=db_session)
    topic_preds = res.get("topic_predictions", [])
    assert len(topic_preds) > 0
    t_timeline = topic_preds[0]["timeline"]
    timeline_years = [entry["year"] for entry in t_timeline]

    # None must NOT appear in timeline
    assert None not in timeline_years
    assert timeline_years == [2022]


def test_timeline_preserves_historical_years(db_session: Session):
    """
    Valid historical exam years (2020, 2021, 2022) must all be preserved in the timeline.
    """
    course, topic = _seed_course_with_taxonomy(db_session, "Preserve History Math", "PHM101")

    fam = QuestionFamily(
        canonical_name="Preserved Question",
        subject=course.name,
        first_seen_year=2020,
        latest_seen_year=2022,
    )
    db_session.add(fam)
    db_session.commit()

    for yr in [2020, 2021, 2022]:
        e = Exam(course_id=course.id, year=yr, assessment_type="ENDSEM")
        db_session.add(e)
        db_session.commit()
        s = Section(exam_id=e.id, name="Sec A")
        db_session.add(s)
        db_session.commit()
        q = Question(section_id=s.id, question_number="1", original_text=f"Question in {yr}", family_id=fam.id)
        q.topics.append(topic)
        db_session.add(q)
    db_session.commit()

    res = get_intelligence_snapshot(str(course.id), target_year=2023, db=db_session)
    t_timeline = res["topic_predictions"][0]["timeline"]
    assert [e["year"] for e in t_timeline] == [2020, 2021, 2022]
    assert all(e["exam_exists"] is True for e in t_timeline)
    assert all(e["present"] is True for e in t_timeline)


# ==============================================================================
# 2. TARGET-YEAR RESOLUTION CONSISTENCY TESTS
# ==============================================================================

def test_resolve_target_year_populated_corpus(db_session: Session):
    """
    Populated corpus derives max_historical_year + 1.
    """
    course, _ = _seed_course_with_taxonomy(db_session, "Populated Math", "POP101")
    e1 = Exam(course_id=course.id, year=2021, assessment_type="ENDSEM")
    e2 = Exam(course_id=course.id, year=2023, assessment_type="ENDSEM")
    db_session.add_all([e1, e2])
    db_session.commit()

    resolved = resolve_target_year(db_session, course.id)
    assert resolved == 2024  # 2023 + 1


def test_resolve_target_year_empty_corpus(db_session: Session):
    """
    Empty corpus (0 exams) derives fallback default (2024).
    """
    course, _ = _seed_course_with_taxonomy(db_session, "Empty Math", "EMPTY101")
    resolved = resolve_target_year(db_session, course.id)
    assert resolved == 2024


def test_resolve_target_year_explicit(db_session: Session):
    """
    Explicit target_year overrides dynamic derivation.
    """
    course, _ = _seed_course_with_taxonomy(db_session, "Explicit Math", "EXP101")
    e = Exam(course_id=course.id, year=2023, assessment_type="ENDSEM")
    db_session.add(e)
    db_session.commit()

    resolved = resolve_target_year(db_session, course.id, target_year=2022)
    assert resolved == 2022


def test_resolve_target_year_max_historical_year(db_session: Session):
    """
    Verify that if the latest exam is 2025, resolved target_year is 2026.
    """
    course, _ = _seed_course_with_taxonomy(db_session, "Max Year Math", "MAX101")
    e1 = Exam(course_id=course.id, year=2022, assessment_type="ENDSEM")
    e2 = Exam(course_id=course.id, year=2025, assessment_type="ENDSEM")
    db_session.add_all([e1, e2])
    db_session.commit()

    resolved = resolve_target_year(db_session, course.id)
    assert resolved == 2026


def test_resolve_target_year_unknown_year_exams_only(db_session: Session):
    """
    Corpus containing only exams with year=None falls back to 2024.
    """
    course, _ = _seed_course_with_taxonomy(db_session, "Null Year Math", "NULL101")
    e1 = Exam(course_id=course.id, year=None, assessment_type="ENDSEM")
    e2 = Exam(course_id=course.id, year=None, assessment_type="CT1")
    db_session.add_all([e1, e2])
    db_session.commit()

    resolved = resolve_target_year(db_session, course.id)
    assert resolved == 2024


def test_equivalent_prediction_and_intelligence_requests(db_session: Session):
    """
    Assert that get_prediction and get_intelligence_snapshot resolve the exact same
    target_year for populated, empty, unknown-year, and explicit requests.
    """
    # 1. Populated course
    course_pop, topic = _seed_course_with_taxonomy(db_session, "Equiv Pop Math", "EPM101")
    fam = QuestionFamily(canonical_name="Equiv Fam", subject=course_pop.name, first_seen_year=2022, latest_seen_year=2022)
    db_session.add(fam)
    db_session.commit()
    e = Exam(course_id=course_pop.id, year=2022, assessment_type="ENDSEM")
    db_session.add(e)
    db_session.commit()
    s = Section(exam_id=e.id, name="Sec A")
    db_session.add(s)
    db_session.commit()
    q = Question(section_id=s.id, question_number="1", original_text="Text 1", family_id=fam.id)
    q.topics.append(topic)
    db_session.add(q)
    db_session.commit()

    pred_res = get_prediction(subject=str(course_pop.id), db=db_session)
    intel_res = get_intelligence_snapshot(course_id=str(course_pop.id), db=db_session)
    assert pred_res["target_year"] == 2023
    assert intel_res["target_year"] == 2023
    assert intel_res["exam_history"]["target_year"] == 2023

    # 2. Empty course
    course_empty, _ = _seed_course_with_taxonomy(db_session, "Equiv Empty Math", "EEM101")
    pred_empty = get_prediction(subject=str(course_empty.id), db=db_session)
    intel_empty = get_intelligence_snapshot(course_id=str(course_empty.id), db=db_session)
    assert pred_empty["target_year"] == 2024
    assert intel_empty["target_year"] == 2024
    assert intel_empty["exam_history"]["target_year"] == 2024

    # 3. Explicit target_year
    pred_exp = get_prediction(subject=str(course_pop.id), target_year=2021, db=db_session)
    intel_exp = get_intelligence_snapshot(course_id=str(course_pop.id), target_year=2021, db=db_session)
    assert pred_exp["target_year"] == 2021
    assert intel_exp["target_year"] == 2021
    assert intel_exp["exam_history"]["target_year"] == 2021

    # 4. Unknown-year only
    course_null, _ = _seed_course_with_taxonomy(db_session, "Equiv Null Math", "ENM101")
    enull = Exam(course_id=course_null.id, year=None, assessment_type="ENDSEM")
    db_session.add(enull)
    db_session.commit()

    pred_null = get_prediction(subject=str(course_null.id), db=db_session)
    intel_null = get_intelligence_snapshot(course_id=str(course_null.id), db=db_session)
    assert pred_null["target_year"] == 2024
    assert intel_null["target_year"] == 2024
    assert intel_null["exam_history"]["target_year"] == 2024
