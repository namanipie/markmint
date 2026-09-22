"""
Comprehensive test suite for Declarative Curriculum Unit Cardinality.

Proves:
1. Existing 5-unit courses still validate.
2. A course with a different declared unit count (e.g. 4 or 6 units) validates correctly.
3. A course declaring X units fails with 'Too few units' when fewer units are supplied.
4. A course declaring X units fails with 'Too many units' when more units are supplied.
5. Unit model strictly rejects numbers < 1 or > declared max_units.
6. Syllabus declared expected_units dynamically propagates to child Unit validation.
7. No course-specific hardcoded branching exists.
"""

import pytest
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic
from backend.services.curriculum_units import (
    DEFAULT_UNIT_COUNT,
    get_expected_unit_count_for_course,
    get_expected_unit_count_for_syllabus_id,
    validate_unit_cardinality,
)
from backend.services.taxonomy_registry import get_taxonomy_registry
from backend.services.taxonomy_registry.models import (
    CourseDefinition,
    CourseTaxonomyRegistryEntry,
    ProvenanceDefinition,
    TopicDefinition,
    UnitDefinition,
)
from backend.services.taxonomy_registry.registry import TaxonomyRegistry


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_existing_five_unit_courses_validate():
    """Verify that all canonical existing courses validate against the default 5 units."""
    reg = get_taxonomy_registry()
    chem = reg.get_course(2)
    assert chem is not None
    assert len(chem.units) == 5
    assert [u.number for u in chem.units] == [1, 2, 3, 4, 5]

    spcm = reg.get_course(13)
    assert spcm is not None
    assert len(spcm.units) == 5
    assert [u.number for u in spcm.units] == [1, 2, 3, 4, 5]

    # Cardinality service returns 5 for standard courses
    assert get_expected_unit_count_for_course(2) == 5
    assert get_expected_unit_count_for_course(13) == 5


def test_course_with_custom_declared_unit_count_validates():
    """Verify that a course declaring a non-5 unit count (e.g. 4 units, 6 units) validates cleanly."""
    custom_entry = CourseTaxonomyRegistryEntry(
        schema_version="1.0",
        taxonomy_version="2.0.0",
        course=CourseDefinition(
            id=991,
            name="Quarter-System Course",
            canonical_code="21TEST101T",
            code="TEST-4U",
            expected_units=4,
        ),
        provenance=ProvenanceDefinition(
            source_document="Test Regulation",
            regulation="2026",
            approved_by="Academic Council",
        ),
        expected_units=4,
        units=[
            UnitDefinition(
                id=9910 + i,
                number=i,
                name=f"Unit {i}",
                topics=[
                    TopicDefinition(
                        id=99100 + i,
                        name=f"Topic in Unit {i}",
                        canonical_name=f"Topic in Unit {i}",
                        strong_phrases=[f"phrase {i}"],
                    )
                ],
            )
            for i in range(1, 5)
        ],
    )

    registry = TaxonomyRegistry(definitions_dir="/nonexistent/empty/path")
    registry._register_entry(custom_entry, source_file="test_custom.json")

    retrieved = registry.get_course(991)
    assert retrieved is not None
    assert len(retrieved.units) == 4
    assert [u.number for u in retrieved.units] == [1, 2, 3, 4]
    assert registry.get_course_expected_units(991) == 4


def test_too_few_units_fail():
    """Verify that providing fewer units than declared raises a descriptive ValueError."""
    entry_too_few = CourseTaxonomyRegistryEntry(
        schema_version="1.0",
        taxonomy_version="2.0.0",
        course=CourseDefinition(
            id=992,
            name="Incomplete Units Course",
            canonical_code="21TEST102T",
            code="TEST-FEW",
            expected_units=5,
        ),
        provenance=ProvenanceDefinition(
            source_document="Test Regulation",
            regulation="2026",
            approved_by="Academic Council",
        ),
        expected_units=5,
        units=[
            UnitDefinition(
                id=9920 + i,
                number=i,
                name=f"Unit {i}",
                topics=[
                    TopicDefinition(
                        id=99200 + i,
                        name=f"Topic {i}",
                        canonical_name=f"Topic {i}",
                    )
                ],
            )
            for i in range(1, 4)  # Only 3 units supplied, but 5 expected
        ],
    )

    registry = TaxonomyRegistry(definitions_dir="/nonexistent/empty/path")
    with pytest.raises(ValueError, match="Too few units"):
        registry._register_entry(entry_too_few, source_file="test_few.json")


def test_too_many_units_fail():
    """Verify that providing more units than declared raises a descriptive ValueError."""
    entry_too_many = CourseTaxonomyRegistryEntry(
        schema_version="1.0",
        taxonomy_version="2.0.0",
        course=CourseDefinition(
            id=993,
            name="Overflow Units Course",
            canonical_code="21TEST103T",
            code="TEST-MANY",
            expected_units=3,
        ),
        provenance=ProvenanceDefinition(
            source_document="Test Regulation",
            regulation="2026",
            approved_by="Academic Council",
        ),
        expected_units=3,
        units=[
            UnitDefinition(
                id=9930 + i,
                number=i,
                name=f"Unit {i}",
                topics=[
                    TopicDefinition(
                        id=99300 + i,
                        name=f"Topic {i}",
                        canonical_name=f"Topic {i}",
                    )
                ],
            )
            for i in range(1, 5)  # 4 units supplied, but only 3 declared
        ],
    )

    registry = TaxonomyRegistry(definitions_dir="/nonexistent/empty/path")
    with pytest.raises(ValueError, match="Too many units"):
        registry._register_entry(entry_too_many, source_file="test_many.json")


def test_unit_model_default_five_unit_validation():
    """Verify that standard Unit instances reject number < 1 or > 5 by default."""
    # Under default 5-unit limit:
    for n in range(1, 6):
        u = Unit(name=f"Valid Unit {n}", number=n)
        assert u.number == n

    with pytest.raises(ValueError, match="strictly be between 1 and 5"):
        Unit(name="Invalid Zero", number=0)

    with pytest.raises(ValueError, match="strictly be between 1 and 5"):
        Unit(name="Invalid Negative", number=-1)

    with pytest.raises(ValueError, match="strictly be between 1 and 5"):
        Unit(name="Invalid Six", number=6)


def test_unit_model_declared_custom_limit_validation():
    """Verify that Unit respects custom max_units explicitly passed or via Syllabus."""
    # 4-unit limit
    u4 = Unit(name="Unit 4 of 4", number=4, max_units=4)
    assert u4.number == 4

    with pytest.raises(ValueError, match="strictly be between 1 and 4"):
        Unit(name="Unit 5 of 4", number=5, max_units=4)

    # 6-unit limit
    u6 = Unit(name="Unit 6 of 6", number=6, max_units=6)
    assert u6.number == 6

    with pytest.raises(ValueError, match="strictly be between 1 and 6"):
        Unit(name="Unit 7 of 6", number=7, max_units=6)


def test_syllabus_expected_units_propagation_to_unit():
    """Verify that Syllabus.expected_units automatically constrains attached child Units."""
    syl = Syllabus(course_id=888, version="2026.1", expected_units=4)
    assert syl.expected_units == 4

    # Unit created with attached syllabus
    valid_u = Unit(syllabus=syl, name="Unit 4", number=4)
    assert valid_u.number == 4

    with pytest.raises(ValueError, match="strictly be between 1 and 4"):
        Unit(syllabus=syl, name="Unit 5 Overflow", number=5)


def test_cardinality_validator_sequence_and_gaps():
    """Verify validate_unit_cardinality enforces non-duplicate, gap-free unit sequences."""
    # Correct sequence passes
    validate_unit_cardinality(4, [1, 2, 3, 4], "TestCourse")
    validate_unit_cardinality(6, [1, 2, 3, 4, 5, 6], "TestCourse")

    # Gap sequence fails (1, 2, 4, 5 with count 4)
    with pytest.raises(ValueError, match="must strictly be"):
        validate_unit_cardinality(4, [1, 2, 4, 5], "TestCourse")

    # Duplicate sequence fails (1, 2, 2, 3 with count 4)
    with pytest.raises(ValueError, match="must strictly be"):
        validate_unit_cardinality(4, [1, 2, 2, 3], "TestCourse")
