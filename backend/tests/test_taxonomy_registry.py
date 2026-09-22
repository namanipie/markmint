"""
Comprehensive unit and integration test suite for the unified declarative taxonomy registry.
Validates structural invariants, database consistency, deterministic loading,
fail-loud validations, and classifier behavioral equivalence for Course 2 (Chemistry)
and Course 13 (SPCM).
"""

import os
import json
import tempfile
import pytest

from backend.core.database import SessionLocal
from backend.core.version import TAXONOMY_VERSION
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_registry import (
    TaxonomyRegistry,
    get_taxonomy_registry,
    reset_taxonomy_registry,
)
from backend.services.taxonomy_rules import (
    CHEMISTRY_TAXONOMY_RULES,
    SPCM_TAXONOMY_RULES,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure a clean registry singleton before and after tests."""
    reset_taxonomy_registry()
    yield
    reset_taxonomy_registry()


def test_registry_discovery_and_deterministic_order():
    """Verify registry discovers registered courses in deterministic sorted order."""
    registry = get_taxonomy_registry()
    course_ids = registry.list_courses()
    assert course_ids == sorted(course_ids), "Courses must be returned in sorted order"
    assert 2 in course_ids, "Course 2 (Chemistry) must be registered"
    assert 13 in course_ids, "Course 13 (SPCM) must be registered"


def test_taxonomy_version_exposure():
    """Verify registry exposes the authoritative taxonomy version."""
    registry = get_taxonomy_registry()
    assert registry.taxonomy_version == TAXONOMY_VERSION
    assert registry.get_course(2).taxonomy_version == "2.0.0"
    assert registry.get_course(13).taxonomy_version == "1.0.0"


def test_chemistry_taxonomy_invariants():
    """Verify Course 2 (Chemistry) declarative structure and invariants."""
    registry = get_taxonomy_registry()
    course = registry.get_course(2)

    assert course.course.id == 2
    assert course.course.canonical_code == "21CYB101J"
    assert course.course.code == "SEM1-CHEM"
    assert course.course.name == "Chemistry"
    assert course.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(course.units) == 5
    # Exactly 45 topics
    total_topics = sum(len(u.topics) for u in course.units)
    assert total_topics == 45

    # Rules count must match
    rules = registry.get_topic_rules(2)
    assert len(rules) == 45
    assert len(CHEMISTRY_TAXONOMY_RULES) == 45

    # Check unit numbers are 1..5
    unit_numbers = [u.number for u in course.units]
    assert unit_numbers == list(range(1, 6))

    # All topic IDs must be unique within course
    topic_ids = [t.id for u in course.units for t in u.topics]
    assert len(topic_ids) == len(set(topic_ids))


def test_spcm_taxonomy_invariants():
    """Verify Course 13 (SPCM) declarative structure and invariants."""
    registry = get_taxonomy_registry()
    course = registry.get_course(13)

    assert course.course.id == 13
    assert course.course.canonical_code == "21PYB102J"
    assert course.course.code == "SEM1-SPCM"
    assert course.course.name == "Semiconductor Physics and Computational Methods"
    assert course.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(course.units) == 5
    # Exactly 27 topics (73 through 99)
    total_topics = sum(len(u.topics) for u in course.units)
    assert total_topics == 27

    # Rules count must match
    rules = registry.get_topic_rules(13)
    assert len(rules) == 27
    assert len(SPCM_TAXONOMY_RULES) == 27

    # Check unit numbers are 1..5
    unit_numbers = [u.number for u in course.units]
    assert unit_numbers == list(range(1, 6))

    # Verify exact topic IDs are 73..99
    topic_ids = sorted([t.id for u in course.units for t in u.topics])
    assert topic_ids == list(range(73, 100))


def test_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 2 and Course 13."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)

    chem_topic_ids = {t.id for u in chem.units for t in u.topics}
    spcm_topic_ids = {t.id for u in spcm.units for t in u.topics}
    assert chem_topic_ids.isdisjoint(spcm_topic_ids), "Topic IDs must not overlap between courses"

    chem_unit_ids = {u.id for u in chem.units}
    spcm_unit_ids = {u.id for u in spcm.units}
    assert chem_unit_ids.isdisjoint(spcm_unit_ids), "Unit IDs must not overlap between courses"


def test_database_validation_chemistry_and_spcm():
    """Verify declarative definitions validate cleanly against current SQLite database taxonomy."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        res_chem = registry.validate_against_database(2, db)
        assert res_chem["valid"] is True, f"Chemistry validation failed: {res_chem.get('mismatches')}"
        assert res_chem["units_verified"] == 5
        assert res_chem["topics_verified"] == 45
        assert len(res_chem["mismatches"]) == 0

        res_spcm = registry.validate_against_database(13, db)
        assert res_spcm["valid"] is True, f"SPCM validation failed: {res_spcm.get('mismatches')}"
        assert res_spcm["units_verified"] == 5
        assert res_spcm["topics_verified"] == 27
        assert len(res_spcm["mismatches"]) == 0
    finally:
        db.close()


def test_chemistry_classifier_behavioral_equivalence():
    """Verify Chemistry classification produces expected topic matches through the registry rules."""
    classifier = TaxonomyClassifierService(CHEMISTRY_TAXONOMY_RULES)

    # Test Schrodinger equation question
    prop1 = classifier.classify(1, "Derive time independent Schrodinger wave equation.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 45  # Quantum Mechanics and Atomic Structure

    # Test Le Chatelier question
    prop2 = classifier.classify(2, "State Le Chatelier's principle and explain the effect of pressure change.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 24  # Le Chatelier Principle

    # Test Crystal Field Theory question
    prop3 = classifier.classify(3, "Calculate crystal field splitting energy for an octahedral complex with strong field ligands.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 51  # Crystal Field Theory


def test_spcm_classifier_behavioral_equivalence():
    """Verify SPCM classification produces expected topic matches through the registry rules."""
    classifier = TaxonomyClassifierService(SPCM_TAXONOMY_RULES)

    # Test Kronig-Penney question
    prop1 = classifier.classify(101, "Discuss the Kronig-Penney model and the origin of energy band gaps.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 75  # Band Theory and Kronig-Penney Model

    # Test Hall Effect question
    prop2 = classifier.classify(102, "Explain how Hall coefficient and carrier mobility are determined using Hall effect measurements.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 91  # Hall Effect and Carrier Mobility

    # Test Carbon Nanotubes question
    prop3 = classifier.classify(103, "Describe the structure, chirality, and density of states of single-walled carbon nanotubes (CNT).")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 96  # Carbon Nanotubes (CNT)


def test_error_handling_malformed_json(tmp_path):
    """Verify registry raises ValueError on invalid JSON."""
    bad_file = tmp_path / "course_bad.json"
    bad_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="Malformed JSON"):
        TaxonomyRegistry(definitions_dir=str(tmp_path))


def test_error_handling_missing_required_fields(tmp_path):
    """Verify registry raises ValueError when required fields are absent."""
    bad_file = tmp_path / "course_bad.json"
    bad_file.write_text(json.dumps({"schema_version": "1.0"}), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required field"):
        TaxonomyRegistry(definitions_dir=str(tmp_path))


def test_error_handling_duplicate_course_id(tmp_path):
    """Verify registry raises ValueError when two files define the same course ID."""
    c1 = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {"id": 100, "name": "Course A", "canonical_code": "A101", "code": "A"},
        "provenance": {"source_document": "Doc", "regulation": "2021", "approved_by": "AC"},
        "units": []
    }
    c2 = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {"id": 100, "name": "Course B", "canonical_code": "B101", "code": "B"},
        "provenance": {"source_document": "Doc", "regulation": "2021", "approved_by": "AC"},
        "units": []
    }
    (tmp_path / "course_100_a.json").write_text(json.dumps(c1), encoding="utf-8")
    (tmp_path / "course_100_b.json").write_text(json.dumps(c2), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate course ID 100"):
        TaxonomyRegistry(definitions_dir=str(tmp_path))


def test_error_handling_globally_duplicate_topic_id(tmp_path):
    """Verify registry raises ValueError when topic ID is duplicated across courses."""
    c1 = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {"id": 101, "name": "Course 101", "canonical_code": "C101", "code": "C1"},
        "provenance": {"source_document": "Doc", "regulation": "2021", "approved_by": "AC"},
        "units": [{
            "id": 1, "number": 1, "name": "Unit 1",
            "topics": [{"id": 500, "name": "Topic Alpha", "canonical_name": "Topic Alpha"}]
        }]
    }
    c2 = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {"id": 102, "name": "Course 102", "canonical_code": "C102", "code": "C2"},
        "provenance": {"source_document": "Doc", "regulation": "2021", "approved_by": "AC"},
        "units": [{
            "id": 2, "number": 1, "name": "Unit 1",
            "topics": [{"id": 500, "name": "Topic Beta", "canonical_name": "Topic Beta"}]
        }]
    }
    (tmp_path / "c1.json").write_text(json.dumps(c1), encoding="utf-8")
    (tmp_path / "c2.json").write_text(json.dumps(c2), encoding="utf-8")

    with pytest.raises(ValueError, match="Globally duplicate topic ID 500"):
        TaxonomyRegistry(definitions_dir=str(tmp_path))


def test_error_handling_duplicate_topic_name_within_course(tmp_path):
    """Verify registry raises ValueError on duplicate topic name within the same course."""
    c = {
        "schema_version": "1.0",
        "taxonomy_version": "1.0.0",
        "course": {"id": 103, "name": "Course 103", "canonical_code": "C103", "code": "C3"},
        "provenance": {"source_document": "Doc", "regulation": "2021", "approved_by": "AC"},
        "units": [{
            "id": 1, "number": 1, "name": "Unit 1",
            "topics": [
                {"id": 601, "name": "Topic Unique", "canonical_name": "Topic Unique"},
                {"id": 602, "name": "Topic Unique", "canonical_name": "Topic Unique"},
            ]
        }]
    }
    (tmp_path / "c3.json").write_text(json.dumps(c), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate topic name 'Topic Unique'"):
        TaxonomyRegistry(definitions_dir=str(tmp_path))
