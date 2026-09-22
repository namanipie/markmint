"""
Centralized declarative unit cardinality and validation service.

Resolves expected unit counts from declarative course taxonomy entries
or database models without hardcoded course-specific branching.
Defaults to 5 units for backward compatibility with canonical first-year courses.
"""

from typing import List, Optional, Set, Any


DEFAULT_UNIT_COUNT = 5


def get_expected_unit_count_for_course(course_id: int, track_id: Optional[int] = None) -> int:
    """
    Resolve the expected syllabus unit count for a course (and optional track).
    Inspects declarative taxonomy registry definitions if loaded; otherwise returns DEFAULT_UNIT_COUNT (5).
    """
    try:
        from backend.services.taxonomy_registry import get_taxonomy_registry
        reg = get_taxonomy_registry()
        entry = reg.get_course(course_id)
        if entry:
            if entry.expected_units is not None:
                return entry.expected_units
            if entry.course.expected_units is not None:
                return entry.course.expected_units
            if entry.tracks and track_id is not None:
                # Count units registered for this specific track
                track_units = [u for u in entry.units if u.track_id == track_id]
                if track_units:
                    return len(track_units)
            elif not entry.tracks and entry.units:
                return len(entry.units)
    except Exception:
        pass

    return DEFAULT_UNIT_COUNT


def get_expected_unit_count_for_syllabus_id(syllabus_id: int) -> int:
    """
    Resolve expected unit count given a syllabus_id.
    Safely falls back to DEFAULT_UNIT_COUNT (5).
    """
    try:
        from backend.core.database import SessionLocal
        from backend.models.core import Syllabus
        db = SessionLocal()
        try:
            syl = db.query(Syllabus).filter(Syllabus.id == syllabus_id).first()
            if syl:
                return get_expected_unit_count_for_course(syl.course_id, track_id=syl.track_id)
        finally:
            db.close()
    except Exception:
        pass

    return DEFAULT_UNIT_COUNT


def validate_unit_cardinality(
    expected_count: int,
    unit_numbers: List[int],
    context_label: str = "Course"
) -> None:
    """
    Validate that unit numbers strictly match the declared expected count.
    Enforces:
    - len(unit_numbers) == expected_count (raises 'Too few units' or 'Too many units')
    - 1 <= unit_number <= expected_count
    - Units must cover exactly 1..expected_count without duplicates or gaps.
    """
    if len(unit_numbers) < expected_count:
        raise ValueError(
            f"Too few units for {context_label}: expected {expected_count}, got {len(unit_numbers)}"
        )
    if len(unit_numbers) > expected_count:
        raise ValueError(
            f"Too many units for {context_label}: expected {expected_count}, got {len(unit_numbers)}"
        )

    expected_sequence = list(range(1, expected_count + 1))
    sorted_numbers = sorted(unit_numbers)
    if sorted_numbers != expected_sequence:
        raise ValueError(
            f"Unit numbers for {context_label} must strictly be {expected_sequence}, got {sorted_numbers}"
        )
