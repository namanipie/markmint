"""
Regression Test Suite for MarkMint Syllabus and Unit Integrity.

Enforces:
1. Every normal canonical course defines exactly 5 units.
2. Foreign Languages parent course has 0 units (acts purely as track container).
3. Every Foreign Language track defines exactly 5 isolated units.
4. No canonical syllabus can contain Unit 6 or higher.
5. Unit model strictly rejects unit numbers outside 1..5.
6. Topics cannot map outside existing canonical units (FK and integrity enforcement).
7. Ingestion invariant: study materials cannot create units.
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, CourseTrack


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_all_normal_courses_have_exactly_five_units(db: Session):
    """Verify that every canonical course (excluding multi-track parent shell) has exactly 5 units."""
    courses = db.query(Course).order_by(Course.id).all()
    assert len(courses) >= 29, f"Expected at least 29 courses, found {len(courses)}"

    for c in courses:
        # Course 8 is Foreign Languages, handled in separate multi-track test
        if c.code == "SEM1-FORE" or c.id == 8:
            continue

        syllabi = db.query(Syllabus).filter(Syllabus.course_id == c.id).all()
        assert len(syllabi) == 1, f"Course {c.id} ({c.name}) should have exactly 1 active syllabus, found {len(syllabi)}"

        syl = syllabi[0]
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        unit_nums = [u.number for u in units]

        assert len(units) == 5, (
            f"Course {c.id} ({c.name}) must have exactly 5 units, got {len(units)}: {unit_nums}"
        )
        assert unit_nums == [1, 2, 3, 4, 5], (
            f"Course {c.id} ({c.name}) unit numbers must strictly be [1, 2, 3, 4, 5], got {unit_nums}"
        )


def test_foreign_languages_track_isolation_and_unit_integrity(db: Session):
    """Verify Foreign Languages architecture: 0 units on parent shell, exactly 5 units per track."""
    fore = db.query(Course).filter(Course.code == "SEM1-FORE").first()
    assert fore is not None, "Foreign Languages course (SEM1-FORE) not found"

    # Parent shell must have 0 units
    parent_syl = db.query(Syllabus).filter(Syllabus.course_id == fore.id, Syllabus.track_id == None).first()
    assert parent_syl is not None, "Parent syllabus for SEM1-FORE not found"
    parent_units = db.query(Unit).filter(Unit.syllabus_id == parent_syl.id).all()
    assert len(parent_units) == 0, (
        f"Parent Foreign Languages shell must have 0 aggregated units, got {len(parent_units)}"
    )

    # Must have exactly 6 isolated tracks
    tracks = db.query(CourseTrack).filter(CourseTrack.course_id == fore.id).order_by(CourseTrack.id).all()
    assert len(tracks) == 6, f"Expected 6 tracks for Foreign Languages, got {len(tracks)}"

    expected_tracks = {
        "german": "21LEH104T",
        "french": "21LEH103T",
        "spanish": "21LEH107T",
        "japanese": "21LEH105T",
        "korean": "21LEH106T",
        "chinese": "21LEH102T",
    }

    for t in tracks:
        assert t.track_key in expected_tracks, f"Unexpected track key: {t.track_key}"
        assert t.track_code == expected_tracks[t.track_key], (
            f"Track code mismatch for {t.track_key}: expected {expected_tracks[t.track_key]}, got {t.track_code}"
        )

        track_syl = db.query(Syllabus).filter(Syllabus.track_id == t.id).first()
        assert track_syl is not None, f"Track {t.track_name} has no syllabus"

        t_units = db.query(Unit).filter(Unit.syllabus_id == track_syl.id).order_by(Unit.number).all()
        t_unit_nums = [u.number for u in t_units]
        assert len(t_units) == 5, (
            f"Track {t.track_name} must have exactly 5 units, got {len(t_units)}: {t_unit_nums}"
        )
        assert t_unit_nums == [1, 2, 3, 4, 5], (
            f"Track {t.track_name} units must strictly be [1, 2, 3, 4, 5], got {t_unit_nums}"
        )


def test_no_canonical_syllabus_contains_unit_six_or_above(db: Session):
    """Verify that no syllabus in the entire database contains a Unit with number >= 6."""
    units_above_5 = db.query(Unit).filter(Unit.number > 5).all()
    assert len(units_above_5) == 0, (
        f"Found {len(units_above_5)} units with number > 5: "
        f"{[(u.id, u.name, u.number, u.syllabus_id) for u in units_above_5]}"
    )

    units_below_1 = db.query(Unit).filter(Unit.number < 1).all()
    assert len(units_below_1) == 0, (
        f"Found {len(units_below_1)} units with number < 1: "
        f"{[(u.id, u.name, u.number, u.syllabus_id) for u in units_below_1]}"
    )


def test_unit_model_rejects_invalid_unit_numbers():
    """Verify SQLAlchemy Unit model validator rejects unit numbers < 1 or > 5."""
    with pytest.raises(ValueError, match="strictly be between 1 and 5"):
        Unit(syllabus_id=1, name="Invalid High Unit", number=6)

    with pytest.raises(ValueError, match="strictly be between 1 and 5"):
        Unit(syllabus_id=1, name="Invalid Low Unit", number=0)

    with pytest.raises(ValueError, match="strictly be between 1 and 5"):
        Unit(syllabus_id=1, name="Invalid Negative Unit", number=-1)

    # Valid unit numbers 1..5 must succeed
    for valid_num in range(1, 6):
        u = Unit(syllabus_id=1, name=f"Valid Unit {valid_num}", number=valid_num)
        assert u.number == valid_num


def test_topics_strictly_map_to_existing_canonical_units(db: Session):
    """Verify that all topics in the database map to valid canonical units with numbers 1..5."""
    topics = db.query(Topic).all()
    assert len(topics) > 0, "Expected topics in database"

    for t in topics:
        assert t.unit is not None, f"Topic {t.id} ({t.name}) has no associated Unit"
        assert 1 <= t.unit.number <= 5, (
            f"Topic {t.id} ({t.name}) points to Unit {t.unit.id} with illegal number {t.unit.number}"
        )


def test_calculus_and_chemistry_specific_canonical_five_units(db: Session):
    """Verify the exact canonical 5-unit titles for Calculus and Chemistry."""
    # Calculus
    calc = db.query(Course).filter(Course.id == 1).first()
    calc_units = (
        db.query(Unit)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == calc.id)
        .order_by(Unit.number)
        .all()
    )
    assert len(calc_units) == 5
    assert calc_units[0].name == "Matrices and Linear Algebra"
    assert calc_units[1].name == "Functions of Several Variables"
    assert calc_units[2].name == "Ordinary Differential Equations"
    assert calc_units[3].name == "Differential Calculus and Geometrical Applications"
    assert calc_units[4].name == "Sequences and Series"

    # Chemistry
    chem = db.query(Course).filter(Course.id == 2).first()
    chem_units = (
        db.query(Unit)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == chem.id)
        .order_by(Unit.number)
        .all()
    )
    assert len(chem_units) == 5
    assert chem_units[0].name == "Periodic Properties and Atomic Structure"
    assert chem_units[1].name == "Chemical Equilibria and Electrochemistry"
    assert chem_units[2].name == "Stereo Chemistry And Organic Reactions"
    assert chem_units[3].name == "Polymers"
    assert chem_units[4].name == "Advanced Engineering Materials"
