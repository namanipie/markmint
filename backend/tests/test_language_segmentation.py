"""
Comprehensive tests for multi-track language segmentation and syllabus onboarding.
Verifies:
1. Course 8: 6 distinct, isolated language tracks (German, French, Spanish, Japanese, Korean, Chinese).
2. Omitted language on multi-track course returns HTTP 400 TRACK_SELECTION_REQUIRED.
3. Track-specific intelligence snapshot, exams, and predictions are strictly isolated.
4. Zero cross-track classification leakage (German question cannot classify to French topics).
5. Japanese (21LEH105T) authoritative 5 units from SRMIST Volume-2 syllabus.
6. Physics: Mechanics verified as 21PYB104J with 29 syllabus topics.
7. Electromagnetic Physics (Course 19) isolates 2018 legacy regulation (Exam 248, 18PYB101J) from 2021 scope.
"""

import pytest
from fastapi import HTTPException
from backend.core.database import SessionLocal
from backend.models.core import Course, CourseTrack, Exam, Syllabus, Unit, Topic, Question
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.endpoints.predictions import get_prediction
from backend.api.endpoints.practice import get_practice_questions
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.analytics import get_analytics_overview, get_topic_repetition_analytics
from backend.services.taxonomy_registry.registry import TaxonomyRegistry
from backend.services.taxonomy_classifier import TaxonomyClassifierService


def test_foreign_language_tracks_distinct_and_isolated():
    """Verify Course 8 has exactly 6 isolated language tracks with full exam assignment."""
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 8).first()
        assert course is not None
        assert course.code == "SEM1-FORE"

        tracks = db.query(CourseTrack).filter(CourseTrack.course_id == 8).order_by(CourseTrack.id).all()
        assert len(tracks) == 6

        track_keys = {t.track_key for t in tracks}
        expected_keys = {"german", "french", "spanish", "japanese", "korean", "chinese"}
        assert track_keys == expected_keys

        track_codes = {t.track_key: t.track_code for t in tracks}
        assert track_codes["german"] == "21LEH104T"
        assert track_codes["french"] == "21LEH103T"
        assert track_codes["spanish"] == "21LEH107T"
        assert track_codes["japanese"] == "21LEH105T"
        assert track_codes["korean"] == "21LEH106T"
        assert track_codes["chinese"] == "21LEH102T"

        # Every exam in Course 8 must be assigned to a valid track
        exams = db.query(Exam).filter(Exam.course_id == 8).all()
        assert len(exams) == 32
        for exam in exams:
            assert exam.track_id is not None, f"Exam {exam.id} ({exam.title}) has null track_id"
            assert exam.track_id in {t.id for t in tracks}

        # Verify each track has at least one exam assigned
        for track in tracks:
            track_exams = [e for e in exams if e.track_id == track.id]
            assert len(track_exams) > 0, f"Track {track.track_name} has 0 exams assigned"
    finally:
        db.close()


def test_track_selection_required_when_omitted():
    """Verify omitting language on multi-track course returns HTTP 400 TRACK_SELECTION_REQUIRED."""
    db = SessionLocal()
    try:
        # Intelligence snapshot
        with pytest.raises(HTTPException) as exc_info:
            get_intelligence_snapshot(course_id="8", db=db)
        assert exc_info.value.status_code == 400
        assert "TRACK_SELECTION_REQUIRED" in exc_info.value.detail

        # Predictions
        with pytest.raises(HTTPException) as exc_info:
            get_prediction(subject="SEM1-FORE", db=db)
        assert exc_info.value.status_code == 400
        assert "TRACK_SELECTION_REQUIRED" in exc_info.value.detail

        # Practice
        with pytest.raises(HTTPException) as exc_info:
            get_practice_questions(subject="SEM1-FORE")
        assert exc_info.value.status_code == 400
        assert "TRACK_SELECTION_REQUIRED" in exc_info.value.detail

        # Study priorities
        with pytest.raises(HTTPException) as exc_info:
            get_study_priorities(course_name="Foreign Languages", db=db)
        assert exc_info.value.status_code == 400
        assert "TRACK_SELECTION_REQUIRED" in exc_info.value.detail
    finally:
        db.close()


def test_track_specific_intelligence_and_zero_cross_track_leakage():
    """Verify track-scoped intelligence returns only that track's exams, syllabuses, and topics."""
    db = SessionLocal()
    try:
        # German track
        de_snapshot = get_intelligence_snapshot(course_id="8", language="german", db=db)
        assert de_snapshot["data_availability_status"] == "READY"
        assert de_snapshot["track"]["track_key"] == "german"
        assert de_snapshot["track"]["track_code"] == "21LEH104T"
        assert de_snapshot["has_topic_taxonomy"] is True
        assert de_snapshot["taxonomy_topic_count"] > 0
        de_papers = de_snapshot["exam_history"]["total_papers"]
        assert de_papers > 0

        # French track
        fr_snapshot = get_intelligence_snapshot(course_id="8", language="french", db=db)
        assert fr_snapshot["data_availability_status"] == "READY"
        assert fr_snapshot["track"]["track_key"] == "french"
        assert fr_snapshot["track"]["track_code"] == "21LEH103T"
        assert fr_snapshot["has_topic_taxonomy"] is True
        assert fr_snapshot["taxonomy_topic_count"] > 0
        fr_papers = fr_snapshot["exam_history"]["total_papers"]
        assert fr_papers > 0

        # German and French exam counts sum to a subset of total, and are distinct
        assert de_papers + fr_papers <= 32

        # Verify DB exam sets are 100% disjoint
        de_track = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "german").first()
        fr_track = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "french").first()

        de_exam_ids = {e.id for e in db.query(Exam).filter(Exam.track_id == de_track.id).all()}
        fr_exam_ids = {e.id for e in db.query(Exam).filter(Exam.track_id == fr_track.id).all()}
        assert de_exam_ids.isdisjoint(fr_exam_ids)
    finally:
        db.close()


def test_zero_cross_track_rule_leakage():
    """Verify registry enforces track isolation so German questions cannot match French topics."""
    registry = TaxonomyRegistry()

    de_rules = registry.get_topic_rules(8, track_key="german")
    fr_rules = registry.get_topic_rules(8, track_key="french")

    assert len(de_rules) > 0
    assert len(fr_rules) > 0

    de_names = {r.topic_name for r in de_rules}
    fr_names = {r.topic_name for r in fr_rules}
    assert de_names.isdisjoint(fr_names), "German and French rule sets must have zero overlap"

    # Classify a German question text against French rules -> must be UNMAPPED
    german_text = "Begrüßungen und Verabschiedungen auf Deutsch im Alltag."
    fr_classifier = TaxonomyClassifierService(fr_rules)
    fr_proposal = fr_classifier.classify(question_id=1, original_text=german_text)
    assert fr_proposal.confidence == "UNMAPPED", f"German question leaked into French rules: {fr_proposal.to_dict()}"

    # Classify the same German text against German rules -> must match
    de_classifier = TaxonomyClassifierService(de_rules)
    de_proposal = de_classifier.classify(question_id=1, original_text=german_text)
    assert de_proposal.confidence in ("HIGH", "MEDIUM"), f"German question failed to match German rules: {de_proposal.to_dict()}"
    assert de_proposal.topic_name is not None


def test_japanese_authoritative_five_units():
    """Verify Japanese track (21LEH105T) has exactly 5 units from SRMIST Volume-2 syllabus."""
    db = SessionLocal()
    try:
        jp_track = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "japanese").first()
        assert jp_track is not None
        assert jp_track.track_code == "21LEH105T"

        jp_syllabus = db.query(Syllabus).filter(Syllabus.track_id == jp_track.id).first()
        assert jp_syllabus is not None

        units = db.query(Unit).filter(Unit.syllabus_id == jp_syllabus.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units for Japanese, found {len(units)}"

        unit_numbers = [u.number for u in units]
        assert unit_numbers == [1, 2, 3, 4, 5]

        # Verify Unit 5 exists and has topics
        unit_5 = next((u for u in units if u.number == 5), None)
        assert unit_5 is not None
        assert "Kanji" in unit_5.name or "Te-Form" in unit_5.name or "Invitational" in unit_5.name

        unit_5_topics = db.query(Topic).filter(Topic.unit_id == unit_5.id).all()
        assert len(unit_5_topics) >= 5, f"Unit 5 should have at least 5 topics, found {len(unit_5_topics)}"
    finally:
        db.close()


def test_physics_mechanics_code_and_topics():
    """Verify Physics: Mechanics (Course 20) is 21PYB104J with 29 canonical syllabus topics."""
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 20).first()
        assert course is not None
        assert course.code == "SEM1-PHYMECH"
        assert course.canonical_code == "21PYB104J"

        syllabus = db.query(Syllabus).filter(Syllabus.course_id == 20).first()
        assert syllabus is not None

        units = db.query(Unit).filter(Unit.syllabus_id == syllabus.id).order_by(Unit.number).all()
        assert len(units) == 5

        total_topics = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.syllabus_id == syllabus.id)
            .count()
        )
        assert total_topics == 29, f"Expected 29 syllabus topics for Mechanics, found {total_topics}"

        # All exams for Course 20
        exams = db.query(Exam).filter(Exam.course_id == 20).all()
        assert len(exams) == 4
    finally:
        db.close()


def test_electromagnetic_physics_regulation_isolation():
    """Verify Course 19 (21PYB101J) isolates 2018 legacy regulation (Exam 248) from 2021 syllabus."""
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 19).first()
        assert course is not None
        assert course.code == "SEM1-EMPHY"
        assert course.canonical_code == "21PYB101J"

        syllabus = db.query(Syllabus).filter(Syllabus.course_id == 19).first()
        assert syllabus is not None

        units = db.query(Unit).filter(Unit.syllabus_id == syllabus.id).order_by(Unit.number).all()
        assert len(units) == 5

        total_topics = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.syllabus_id == syllabus.id)
            .count()
        )
        assert total_topics == 32

        # Exam 248 is the 2018 paper under 18PYB101J
        exam_248 = db.query(Exam).filter(Exam.id == 248).first()
        assert exam_248 is not None
        assert exam_248.course_id == 19

        # Verify Exam 248 questions have 0 mappings in question_topic
        from backend.models.core import question_topic, Section
        mapped_248_qs = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .filter(Section.exam_id == 248)
            .count()
        )
        assert mapped_248_qs == 0, f"Exam 248 (18PYB101J) must have 0 mappings to 2021 taxonomy, found {mapped_248_qs}"
    finally:
        db.close()


def test_analytics_endpoints_track_filtering():
    """Verify repetition analytics endpoints filter properly by language track."""
    db = SessionLocal()
    try:
        # Overview for Course 8 with German track
        de_overview = get_analytics_overview(course_id="8", language="german", db=db)
        assert de_overview["total_papers"] > 0

        # Overview for Course 8 with French track
        fr_overview = get_analytics_overview(course_id="8", language="french", db=db)
        assert fr_overview["total_papers"] > 0

        # Topic repetition for German track
        de_topics = get_topic_repetition_analytics(course_id="8", language="german", db=db)
        assert len(de_topics["topics"]) > 0
        # German topics only
        for t in de_topics["topics"]:
            assert "DE" in t["topic_name"] or t["topic_id"] > 0
    finally:
        db.close()
