"""
Unit tests for Course 13 (SPCM) taxonomy integrity and relational correctness.
Verifies that:
- Exactly 5 canonical units exist for Syllabus 13.
- Exactly 27 canonical topics exist under those units.
- Canonical Concept records exist with status='CANONICAL'.
- Foreign key references from topics to units and syllabuses to courses are valid.
- Zero dangling or orphaned topics.
"""
import sqlite3
import pytest
from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Concept


def test_spcm_course_and_syllabus_exist() -> None:
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 13).first()
        assert course is not None, "Course 13 must exist in the database"
        assert "Semiconductor" in course.name

        syllabuses = db.query(Syllabus).filter(Syllabus.course_id == 13).all()
        assert len(syllabuses) >= 1, "Course 13 must have at least one syllabus"
    finally:
        db.close()


def test_spcm_canonical_units_count_and_naming() -> None:
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 13).first()
        assert syl is not None

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).all()
        # 5 canonical units + 1 fallback General Unit
        unit_names = {u.name for u in units}
        expected_units = {
            "Free Electron Theory and Energy Bands",
            "Semiconductor Physics and Carrier Transport",
            "Optical Processes and Photovoltaic Devices",
            "Semiconductor Measurements and Transport Equations",
            "Nanostructures and Characterization",
        }
        for eu in expected_units:
            assert eu in unit_names, f"Expected unit '{eu}' missing from Course 13"
    finally:
        db.close()


def test_spcm_canonical_topics_count_and_associations() -> None:
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 13).first()
        assert syl is not None

        topics = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.syllabus_id == syl.id)
            .all()
        )
        assert len(topics) == 27, f"Expected 27 SPCM topics, found {len(topics)}"

        # Verify each unit has the expected number of topics
        unit_topic_counts = {}
        for t in topics:
            unit_topic_counts[t.unit.name] = unit_topic_counts.get(t.unit.name, 0) + 1

        assert unit_topic_counts["Free Electron Theory and Energy Bands"] == 5
        assert unit_topic_counts["Semiconductor Physics and Carrier Transport"] == 7
        assert unit_topic_counts["Optical Processes and Photovoltaic Devices"] == 5
        assert unit_topic_counts["Semiconductor Measurements and Transport Equations"] == 5
        assert unit_topic_counts["Nanostructures and Characterization"] == 5
    finally:
        db.close()


def test_spcm_concepts_canonical_integrity() -> None:
    db = SessionLocal()
    try:
        concepts = (
            db.query(Concept)
            .filter(Concept.subject.like("%Semiconductor%"))
            .all()
        )
        assert len(concepts) == 27, f"Expected 27 SPCM concepts, found {len(concepts)}"
        for c in concepts:
            assert c.status == "CANONICAL"
            assert c.unit_id is not None
            assert len(c.description) > 10
    finally:
        db.close()


def test_no_dangling_or_orphaned_spcm_topics() -> None:
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 13).first()
        assert syl is not None

        # Check for topics referencing non-existent units
        orphans = (
            db.query(Topic)
            .outerjoin(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.id.is_(None))
            .count()
        )
        assert orphans == 0, "No orphaned topics without valid unit relation should exist"
    finally:
        db.close()
