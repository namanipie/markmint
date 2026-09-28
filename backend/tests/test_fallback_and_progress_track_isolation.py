"""
Regression tests for Phase 4 Slice 4: Final Fallback + Progress Track Isolation Fix.

Verifies:
1. INT-ADV-1: resolve_family_to_topic Step 2 fallback:
   - Cross-course same canonical name -> returns None
   - Same-course cross-track same canonical name -> returns None
   - Same-track valid fallback -> resolves correctly
   - Trackless valid fallback -> resolves correctly
   - Track-specific family with trackless target -> returns None
   - Trackless family with track target -> returns None
   - Step 1 valid resolution remains unchanged
2. INT-ADV-2: POST /study/progress/{course_id} track context:
   - German progress update updates German topic
   - French progress update updates French topic
   - Invalid track for course rejected (HTTP 400)
   - Omitted track preserves compatibility
   - Unmapped family requiring fallback resolves and updates in track
   - Cross-track family cannot update the wrong topic
   - Cross-track topic_id rejected (HTTP 400)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.core import (
    Course,
    CourseTrack,
    Exam,
    Question,
    QuestionFamily,
    QuestionFamilyMembership,
    Section,
    StudentTopicProgress,
    Syllabus,
    Topic,
    Unit,
    question_topic,
)
from backend.services.study_intelligence import StudyIntelligenceService


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def multi_course_setup(db_session: Session):
    """
    Setup:
    - Course 1: Calculus (Trackless) with Topic "Calculus Intro" and "Grammar"
    - Course 2: Chemistry (Trackless) with Topic "Chemical Bonding"
    - Course 8: Foreign Languages (Multi-track: German id=1, French id=2)
      - German syllabus with Topic "Grammar" and "German Basics"
      - French syllabus with Topic "Grammar" and "French Basics"
    """
    c1 = Course(id=101, name="Calculus And Linear Algebra", code="CALC-101", canonical_code="21MAB101T")
    c2 = Course(id=102, name="Chemistry", code="CHEM-102", canonical_code="21CYB101J")
    c8 = Course(id=108, name="Foreign Languages", code="LANG-108", canonical_code="21LEH-ELECTIVE")
    db_session.add_all([c1, c2, c8])
    db_session.commit()

    # Tracks for Course 8
    tr_ger = CourseTrack(id=201, course_id=c8.id, track_key="german", track_name="German", track_code="GER")
    tr_fre = CourseTrack(id=202, course_id=c8.id, track_key="french", track_name="French", track_code="FRE")
    # Track for another course to test foreign track rejection
    tr_c1 = CourseTrack(id=203, course_id=c1.id, track_key="honors", track_name="Honors", track_code="HON")
    db_session.add_all([tr_ger, tr_fre, tr_c1])
    db_session.commit()

    # Syllabuses
    s_c1 = Syllabus(course_id=c1.id, track_id=None, version="2021")
    s_c2 = Syllabus(course_id=c2.id, track_id=None, version="2021")
    s_ger = Syllabus(course_id=c8.id, track_id=tr_ger.id, version="2021")
    s_fre = Syllabus(course_id=c8.id, track_id=tr_fre.id, version="2021")
    db_session.add_all([s_c1, s_c2, s_ger, s_fre])
    db_session.commit()

    # Units
    u_c1 = Unit(syllabus_id=s_c1.id, number=1, name="Unit 1")
    u_c2 = Unit(syllabus_id=s_c2.id, number=1, name="Unit 1")
    u_ger = Unit(syllabus_id=s_ger.id, number=1, name="German Unit 1")
    u_fre = Unit(syllabus_id=s_fre.id, number=1, name="French Unit 1")
    db_session.add_all([u_c1, u_c2, u_ger, u_fre])
    db_session.commit()

    # Topics
    t_c1_intro = Topic(unit_id=u_c1.id, name="Introduction")
    t_c2_bond = Topic(unit_id=u_c2.id, name="Chemical Bonding")
    t_c2_intro = Topic(unit_id=u_c2.id, name="Introduction")
    t_ger_gram = Topic(unit_id=u_ger.id, name="Grammar")
    t_ger_basic = Topic(unit_id=u_ger.id, name="German Basics")
    t_fre_gram = Topic(unit_id=u_fre.id, name="Grammar")
    t_fre_basic = Topic(unit_id=u_fre.id, name="French Basics")
    db_session.add_all([t_c1_intro, t_c2_bond, t_c2_intro, t_ger_gram, t_ger_basic, t_fre_gram, t_fre_basic])
    db_session.commit()

    return {
        "c1": c1,
        "c2": c2,
        "c8": c8,
        "tr_ger": tr_ger,
        "tr_fre": tr_fre,
        "tr_c1": tr_c1,
        "t_c1_intro": t_c1_intro,
        "t_c2_bond": t_c2_bond,
        "t_c2_intro": t_c2_intro,
        "t_ger_gram": t_ger_gram,
        "t_ger_basic": t_ger_basic,
        "t_fre_gram": t_fre_gram,
        "t_fre_basic": t_fre_basic,
    }


# ==============================================================================
# 1. INT-ADV-1: resolve_family_to_topic STEP 2 FALLBACK TESTS
# ==============================================================================

def test_cross_course_same_canonical_name(db_session: Session, multi_course_setup):
    """
    Course A family 'Introduction' must return None when queried for Course B,
    even though Course B has a topic named 'Introduction'.
    """
    c1 = multi_course_setup["c1"]
    c2 = multi_course_setup["c2"]

    # Family belongs to Course 1 (Calculus)
    fam_c1 = QuestionFamily(
        canonical_name="Introduction",
        subject=c1.name,
        track_id=None,
    )
    db_session.add(fam_c1)
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    # Query for Course 2 (Chemistry)
    result = service.resolve_family_to_topic(fam_c1.id, c2.id, track_id=None)
    assert result is None, "Cross-course family must not resolve to Course B topic"


def test_same_course_cross_track_same_canonical_name(db_session: Session, multi_course_setup):
    """
    German family 'Grammar' queried with French track_id must return None,
    even though French has a topic named 'Grammar'.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    tr_fre = multi_course_setup["tr_fre"]

    fam_ger = QuestionFamily(
        canonical_name="Grammar",
        subject=c8.name,
        track_id=tr_ger.id,
    )
    db_session.add(fam_ger)
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    # Query with French track context
    result = service.resolve_family_to_topic(fam_ger.id, c8.id, track_id=tr_fre.id)
    assert result is None, "German family must not resolve in French track context"


def test_same_track_valid_fallback(db_session: Session, multi_course_setup):
    """
    German family 'Grammar' queried with German track_id resolves to German topic.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    t_ger_gram = multi_course_setup["t_ger_gram"]

    fam_ger = QuestionFamily(
        canonical_name="Grammar",
        subject=c8.name,
        track_id=tr_ger.id,
    )
    db_session.add(fam_ger)
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    result = service.resolve_family_to_topic(fam_ger.id, c8.id, track_id=tr_ger.id)
    assert result is not None
    assert result.id == t_ger_gram.id
    assert result.name == "Grammar"


def test_trackless_valid_fallback(db_session: Session, multi_course_setup):
    """
    Trackless family 'Chemical Bonding' in Chemistry resolves to Chemistry topic.
    """
    c2 = multi_course_setup["c2"]
    t_c2_bond = multi_course_setup["t_c2_bond"]

    fam_chem = QuestionFamily(
        canonical_name="Chemical Bonding",
        subject=c2.name,
        track_id=None,
    )
    db_session.add(fam_chem)
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    result = service.resolve_family_to_topic(fam_chem.id, c2.id, track_id=None)
    assert result is not None
    assert result.id == t_c2_bond.id


def test_track_specific_family_with_trackless_target(db_session: Session, multi_course_setup):
    """
    Track-specific German family with trackless target (track_id=None) must NOT
    silently resolve to any topic.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]

    fam_ger = QuestionFamily(
        canonical_name="Grammar",
        subject=c8.name,
        track_id=tr_ger.id,
    )
    db_session.add(fam_ger)
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    result = service.resolve_family_to_topic(fam_ger.id, c8.id, track_id=None)
    assert result is None, "Track-specific family must not resolve to trackless context"


def test_trackless_family_with_track_specific_target(db_session: Session, multi_course_setup):
    """
    Trackless family queried with a specific track context must NOT match.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]

    fam_trackless = QuestionFamily(
        canonical_name="Grammar",
        subject=c8.name,
        track_id=None,
    )
    db_session.add(fam_trackless)
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    result = service.resolve_family_to_topic(fam_trackless.id, c8.id, track_id=tr_ger.id)
    assert result is None, "Trackless family must not resolve to track-specific context"


def test_step1_authoritative_resolution_unchanged(db_session: Session, multi_course_setup):
    """
    Existing Step 1 mapping through Question -> Section -> Exam -> Topic remains authoritative.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    t_ger_basic = multi_course_setup["t_ger_basic"]

    exam = Exam(course_id=c8.id, track_id=tr_ger.id, year=2023)
    db_session.add(exam)
    db_session.commit()

    section = Section(exam_id=exam.id, name="Sec A")
    db_session.add(section)
    db_session.commit()

    fam = QuestionFamily(canonical_name="Any Name", subject=c8.name, track_id=tr_ger.id)
    db_session.add(fam)
    db_session.commit()

    q = Question(section_id=section.id, question_number=1, original_text="German Q1", family_id=fam.id)
    db_session.add(q)
    db_session.commit()

    # Link question to topic
    db_session.execute(question_topic.insert().values(question_id=q.id, topic_id=t_ger_basic.id))
    db_session.commit()

    service = StudyIntelligenceService(db_session)
    result = service.resolve_family_to_topic(fam.id, c8.id, track_id=tr_ger.id)
    assert result is not None
    assert result.id == t_ger_basic.id


# ==============================================================================
# 2. FIX INT-ADV-2: STUDY PROGRESS TRACK CONTEXT API TESTS
# ==============================================================================

def test_api_german_progress_update(client: TestClient, db_session: Session, multi_course_setup):
    """POST /study/progress/{course_id} with German track_id updates German topic."""
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    t_ger_gram = multi_course_setup["t_ger_gram"]
    t_fre_gram = multi_course_setup["t_fre_gram"]

    payload = {
        "user_id": "student_german",
        "track_id": tr_ger.id,
        "topic": "Grammar",
        "status": "COMPLETED",
    }
    resp = client.post(f"/api/study/progress/{c8.id}", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["topic_id"] == t_ger_gram.id
    assert data["status"] == "COMPLETED"

    # Verify French topic has no progress for this student
    fre_prog = (
        db_session.query(StudentTopicProgress)
        .filter_by(student_id="student_german", topic_id=t_fre_gram.id)
        .first()
    )
    assert fre_prog is None


def test_api_french_progress_update(client: TestClient, db_session: Session, multi_course_setup):
    """POST /study/progress/{course_id} with French track_id updates French topic."""
    c8 = multi_course_setup["c8"]
    tr_fre = multi_course_setup["tr_fre"]
    t_fre_gram = multi_course_setup["t_fre_gram"]

    payload = {
        "user_id": "student_french",
        "track_id": tr_fre.id,
        "topic": "Grammar",
        "status": "STARTED",
    }
    resp = client.post(f"/api/study/progress/{c8.id}", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["topic_id"] == t_fre_gram.id
    assert data["status"] == "STARTED"


def test_api_invalid_track_for_course(client: TestClient, multi_course_setup):
    """Invalid track_id or track from another course is rejected with HTTP 400."""
    c8 = multi_course_setup["c8"]
    tr_c1 = multi_course_setup["tr_c1"]

    # Non-existent track ID
    resp = client.post(f"/api/study/progress/{c8.id}", json={"track_id": 9999, "topic": "Grammar"})
    assert resp.status_code == 400
    assert "does not belong to course" in resp.json()["detail"]

    # Track belonging to Course 1 (Calculus) passed to Course 8
    resp = client.post(f"/api/study/progress/{c8.id}", json={"track_id": tr_c1.id, "topic": "Grammar"})
    assert resp.status_code == 400
    assert "does not belong to course" in resp.json()["detail"]


def test_api_omitted_track_preserves_compatibility(client: TestClient, multi_course_setup):
    """Trackless course (Chemistry) omitting track_id works normally."""
    c2 = multi_course_setup["c2"]
    t_c2_bond = multi_course_setup["t_c2_bond"]

    payload = {
        "user_id": "student_chem",
        "topic": "Chemical Bonding",
        "status": "COMPLETED",
    }
    resp = client.post(f"/api/study/progress/{c2.id}", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["topic_id"] == t_c2_bond.id


def test_api_unmapped_family_fallback_progress_update(client: TestClient, db_session: Session, multi_course_setup):
    """
    Unmapped German family with matching canonical name resolves via Step 2 fallback
    when track_id is supplied, updating the German topic.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    t_ger_gram = multi_course_setup["t_ger_gram"]

    fam_ger = QuestionFamily(
        canonical_name="Grammar",
        subject=c8.name,
        track_id=tr_ger.id,
    )
    db_session.add(fam_ger)
    db_session.commit()

    payload = {
        "user_id": "student_fallback",
        "track_id": tr_ger.id,
        "family_id": fam_ger.id,
        "status": "STARTED",
    }
    resp = client.post(f"/api/study/progress/{c8.id}", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["topic_id"] == t_ger_gram.id


def test_api_cross_track_family_cannot_update_wrong_topic(client: TestClient, db_session: Session, multi_course_setup):
    """
    Passing German family with French track context is rejected safely,
    and French topic progress is never written.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    tr_fre = multi_course_setup["tr_fre"]
    t_fre_gram = multi_course_setup["t_fre_gram"]

    fam_ger = QuestionFamily(
        canonical_name="Grammar",
        subject=c8.name,
        track_id=tr_ger.id,
    )
    db_session.add(fam_ger)
    db_session.commit()

    payload = {
        "user_id": "student_attacker",
        "track_id": tr_fre.id,
        "family_id": fam_ger.id,
        "status": "COMPLETED",
    }
    resp = client.post(f"/api/study/progress/{c8.id}", json=payload)
    assert resp.status_code == 400
    assert "belongs to track" in resp.json()["detail"]

    # Verify no progress was created for the French topic
    fre_prog = (
        db_session.query(StudentTopicProgress)
        .filter_by(student_id="student_attacker", topic_id=t_fre_gram.id)
        .first()
    )
    assert fre_prog is None


def test_api_cross_track_topic_id_rejected(client: TestClient, db_session: Session, multi_course_setup):
    """
    Providing a topic_id from French track when requesting German track is rejected.
    """
    c8 = multi_course_setup["c8"]
    tr_ger = multi_course_setup["tr_ger"]
    t_fre_gram = multi_course_setup["t_fre_gram"]

    payload = {
        "user_id": "student_topic_id",
        "track_id": tr_ger.id,
        "topic_id": t_fre_gram.id,
        "status": "STARTED",
    }
    resp = client.post(f"/api/study/progress/{c8.id}", json=payload)
    assert resp.status_code == 400
    assert "does not belong to course" in resp.json()["detail"]
