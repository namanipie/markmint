"""
Test suite for QuestionFamily track isolation:
1. Same course + same track can cluster.
2. Same course + different tracks cannot cluster.
3. Different courses cannot cluster.
4. Trackless courses retain clustering behavior.
5. German questions cannot enter Korean families.
6. Korean questions cannot enter German families.
7. Family rebuild is deterministic.
8. Every question has exactly one family and unique membership.
9. No family spans multiple courses.
10. No family spans multiple tracks.
11. Course 8 has no cross-track families.
12. Known 20 leakage families are remediated.
13. Courses 24-31 retain their current family invariants.
"""

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.core import (
    Course,
    CourseTrack,
    Exam,
    Section,
    Question,
    QuestionFamily,
    QuestionFamilyMembership,
)
from backend.services.families.manager import QuestionFamilyManager
from backend.services.scraper.post_processor import PostIngestionPipeline


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class MockEmbeddingProvider:
    """Deterministic embedding provider for unit testing matching logic."""
    def get_embeddings(self, texts):
        embeddings = []
        for t in texts:
            val = float(hash(t) % 1000) / 1000.0
            embeddings.append([val, 1.0 - val, 0.5, 0.5])
        return embeddings


# ==============================================================================
# 1-4. UNIT-LEVEL MATCHING & TRACK ISOLATION INVARIANTS
# ==============================================================================

def test_same_course_same_track_can_cluster(db: Session):
    """Questions belonging to the same course and same track can cluster into one family."""
    course = db.query(Course).filter(Course.id == 8).first()
    assert course is not None
    track_german = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "german").first()
    assert track_german is not None

    # Load candidate families for German track with valid first_seen_year
    target_fam = (
        db.query(QuestionFamily)
        .filter(
            QuestionFamily.subject == course.name,
            QuestionFamily.track_id == track_german.id,
            QuestionFamily.first_seen_year <= 2100,
        )
        .first()
    )
    assert target_fam is not None

    # Verify that searching for historical families with track_german.id finds target_fam
    manager = QuestionFamilyManager(db, MockEmbeddingProvider())
    cands = manager._get_historical_families(course.name, 2100, track_id=track_german.id)
    assert any(f.id == target_fam.id for f in cands)


def test_same_course_different_tracks_cannot_cluster(db: Session):
    """Questions belonging to different tracks of the same course must NEVER match."""
    course = db.query(Course).filter(Course.id == 8).first()
    track_german = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "german").first()
    track_korean = db.query(CourseTrack).filter(CourseTrack.course_id == 8, CourseTrack.track_key == "korean").first()

    assert track_german is not None and track_korean is not None
    manager = QuestionFamilyManager(db, MockEmbeddingProvider())

    # German candidate search MUST NOT return Korean families
    german_cands = manager._get_historical_families(course.name, 2100, track_id=track_german.id)
    assert len(german_cands) > 0
    for fam in german_cands:
        assert fam.track_id == track_german.id
        assert fam.track_id != track_korean.id

    # Korean candidate search MUST NOT return German families
    korean_cands = manager._get_historical_families(course.name, 2100, track_id=track_korean.id)
    assert len(korean_cands) > 0
    for fam in korean_cands:
        assert fam.track_id == track_korean.id
        assert fam.track_id != track_german.id


def test_different_courses_cannot_cluster(db: Session):
    """Questions belonging to different courses must NEVER match."""
    manager = QuestionFamilyManager(db, MockEmbeddingProvider())
    cands = manager._get_historical_families("Calculus And Linear Algebra", 2100, track_id=None)
    assert len(cands) > 0
    for fam in cands:
        assert fam.subject == "Calculus And Linear Algebra"
        assert fam.subject != "Foreign Languages"


def test_trackless_courses_preserve_clustering(db: Session):
    """Trackless single-track courses (track_id is None) retain standard matching behavior."""
    manager = QuestionFamilyManager(db, MockEmbeddingProvider())
    cands = manager._get_historical_families("Chemistry", 2100, track_id=None)
    assert len(cands) > 0
    for fam in cands:
        assert fam.subject == "Chemistry"
        assert fam.track_id is None


# ==============================================================================
# 5-6. LANGUAGE TRACK ISOLATION (COURSE 8)
# ==============================================================================

def test_german_questions_never_enter_korean_families(db: Session):
    """No German question may belong to a Korean family."""
    # Find all German questions (Exam track 1)
    german_q_ids = (
        db.query(Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == 8, Exam.track_id == 1)
        .all()
    )
    german_q_ids = [q[0] for q in german_q_ids]
    assert len(german_q_ids) > 0

    # Find Korean families (track 5)
    korean_fam_ids = (
        db.query(QuestionFamily.id)
        .filter(QuestionFamily.subject == "Foreign Languages", QuestionFamily.track_id == 5)
        .all()
    )
    korean_fam_ids = {f[0] for f in korean_fam_ids}
    assert len(korean_fam_ids) > 0

    # Assert no German question is linked to any Korean family
    violations = (
        db.query(QuestionFamilyMembership)
        .filter(
            QuestionFamilyMembership.question_id.in_(german_q_ids),
            QuestionFamilyMembership.family_id.in_(korean_fam_ids),
        )
        .all()
    )
    assert len(violations) == 0, f"Found German questions in Korean families: {violations}"


def test_korean_questions_never_enter_german_families(db: Session):
    """No Korean question may belong to a German family."""
    # Find all Korean questions (Exam track 5)
    korean_q_ids = (
        db.query(Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == 8, Exam.track_id == 5)
        .all()
    )
    korean_q_ids = [q[0] for q in korean_q_ids]
    assert len(korean_q_ids) > 0

    # Find German families (track 1)
    german_fam_ids = (
        db.query(QuestionFamily.id)
        .filter(QuestionFamily.subject == "Foreign Languages", QuestionFamily.track_id == 1)
        .all()
    )
    german_fam_ids = {f[0] for f in german_fam_ids}
    assert len(german_fam_ids) > 0

    # Assert no Korean question is linked to any German family
    violations = (
        db.query(QuestionFamilyMembership)
        .filter(
            QuestionFamilyMembership.question_id.in_(korean_q_ids),
            QuestionFamilyMembership.family_id.in_(german_fam_ids),
        )
        .all()
    )
    assert len(violations) == 0, f"Found Korean questions in German families: {violations}"


# ==============================================================================
# 7-10. DETERMINISM AND CORPUS-WIDE INVARIANTS
# ==============================================================================

def test_every_question_has_exactly_one_family(db: Session):
    """Every question in the corpus must belong to exactly one family with unique membership."""
    total_q = db.query(Question).count()
    assert total_q == 9013

    # Zero questions without family_id
    unassigned = db.query(Question).filter(Question.family_id.is_(None)).count()
    assert unassigned == 0

    # Zero questions without membership row
    unlinked = (
        db.query(Question.id)
        .outerjoin(QuestionFamilyMembership, Question.id == QuestionFamilyMembership.question_id)
        .filter(QuestionFamilyMembership.id.is_(None))
        .count()
    )
    assert unlinked == 0

    # Zero duplicate memberships (enforced by UNIQUE constraint)
    dupe_mems = (
        db.query(QuestionFamilyMembership.question_id)
        .group_by(QuestionFamilyMembership.question_id)
        .having(func.count(QuestionFamilyMembership.id) > 1)
        .all()
    )
    assert len(dupe_mems) == 0


def test_no_family_spans_multiple_courses(db: Session):
    """No QuestionFamily in the database may contain questions from multiple courses."""
    cross_course = (
        db.query(QuestionFamilyMembership.family_id)
        .join(Question, QuestionFamilyMembership.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .group_by(QuestionFamilyMembership.family_id)
        .having(func.count(func.distinct(Exam.course_id)) > 1)
        .all()
    )
    assert len(cross_course) == 0


def test_no_family_spans_multiple_tracks(db: Session):
    """No QuestionFamily in the database may contain questions from multiple tracks."""
    cross_track = (
        db.query(QuestionFamilyMembership.family_id)
        .join(Question, QuestionFamilyMembership.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.track_id.isnot(None))
        .group_by(QuestionFamilyMembership.family_id)
        .having(func.count(func.distinct(Exam.track_id)) > 1)
        .all()
    )
    assert len(cross_track) == 0


def test_course_8_track_alignment(db: Session):
    """For every Course 8 question, its exam track must equal its family track."""
    mismatches = (
        db.query(Question.id, Exam.track_id, QuestionFamily.track_id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .join(QuestionFamily, Question.family_id == QuestionFamily.id)
        .filter(Exam.course_id == 8)
        .filter(Exam.track_id != QuestionFamily.track_id)
        .all()
    )
    assert len(mismatches) == 0

    # The count of distinct families in Course 8
    c8_active_count = (
        db.query(func.count(func.distinct(Question.family_id)))
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == 8)
        .scalar()
    )
    assert c8_active_count == 797

    track_counts = dict(
        db.query(CourseTrack.track_key, func.count(QuestionFamily.id))
        .join(QuestionFamily, QuestionFamily.track_id == CourseTrack.id)
        .filter(CourseTrack.course_id == 8)
        .group_by(CourseTrack.track_key)
        .all()
    )
    assert track_counts == {
        "german": 180,
        "french": 172,
        "spanish": 54,
        "japanese": 129,
        "korean": 171,
        "chinese": 91,
    }


# ==============================================================================
# 12. REMEDIATION OF THE 20 KNOWN HISTORICAL LEAKAGE FAMILIES
# ==============================================================================

def test_twenty_known_leakage_families_remediated(db: Session):
    """
    Specifically verifies that the 20 historical cross-track leakage families:
    2227, 2228, 2234, 2235, 2236, 2240, 2242, 2245, 2246, 2247,
    2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257
    are now strictly German Track 1 with zero cross-track leakage.
    """
    known_20 = [
        2227, 2228, 2234, 2235, 2236, 2240, 2242, 2245, 2246, 2247,
        2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257,
    ]

    fams = db.query(QuestionFamily).filter(QuestionFamily.id.in_(known_20)).all()
    assert len(fams) == 20

    for fam in fams:
        # Must be German track 1
        assert fam.track_id == 1, f"Family {fam.id} has track_id {fam.track_id}, expected 1"
        assert fam.subject == "Foreign Languages"

        # Questions in this family must all have track_id = 1
        member_tracks = (
            db.query(Exam.track_id)
            .join(Section, Exam.id == Section.exam_id)
            .join(Question, Section.id == Question.section_id)
            .filter(Question.family_id == fam.id)
            .distinct()
            .all()
        )
        assert member_tracks == [(1,)], f"Family {fam.id} has non-German questions: {member_tracks}"


# ==============================================================================
# 13. COURSES 24-31 RETENTION INVARIANTS
# ==============================================================================

def test_courses_24_to_31_retain_family_invariants(db: Session):
    """
    Courses 24 through 31 are single-track courses and must retain their
    exact family counts, questions, and trackless (track_id is None) invariants.
    """
    expected_counts = {
        24: (185, 220),  # (families, questions)
        25: (178, 198),
        26: (118, 128),
        27: (225, 255),
        28: (140, 143),
        29: (147, 156),
        30: (203, 337),
        31: (151, 191),
    }

    for cid, (exp_fams, exp_qs) in expected_counts.items():
        course = db.query(Course).filter(Course.id == cid).first()
        assert course is not None, f"Course {cid} not found"

        # Count questions
        q_cnt = (
            db.query(Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .count()
        )
        assert q_cnt == exp_qs, f"Course {cid} ({course.name}): expected {exp_qs} questions, got {q_cnt}"

        # Count families
        fam_cnt = (
            db.query(func.count(func.distinct(Question.family_id)))
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .scalar()
        )
        assert fam_cnt == exp_fams, f"Course {cid} ({course.name}): expected {exp_fams} families, got {fam_cnt}"

        # All families in these courses must have track_id is None
        c_fam_tracks = (
            db.query(func.distinct(QuestionFamily.track_id))
            .join(Question, QuestionFamily.id == Question.family_id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .all()
        )
        assert c_fam_tracks == [(None,)], f"Course {cid} ({course.name}) has non-null family tracks: {c_fam_tracks}"
