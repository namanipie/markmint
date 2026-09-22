"""
Tests for Generalized Course Assessment Plan Registry.
Validates:
1. Existing Course 1 behavior (Calculus, unchanged)
2. Existing Course 23 behavior (Building Materials, unchanged)
3. Course 24 behavior (Data Structures and Algorithms - CLA1/CLA2/ENDSEM)
4. Course 29 behavior (Artificial Intelligence - CLA1/CLA2/ENDSEM)
5. Unsupported course fails safely
6. Valid and invalid assessment cycles fail safely
7. Track-aware behavior (Foreign Languages tracks)
8. Course isolation remains strictly enforced
"""
import pytest
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.services.assessment_plan_registry import (
    COURSE_ASSESSMENT_PLANS,
    get_course_assessment_plan,
    normalize_course_assessment_type,
    get_course_raw_types_for_cycle,
    is_exam_in_course_cycle,
    get_course_assessment_scope,
)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_course_1_behavior(db: Session):
    """Verify existing Course 1 (Calculus) retains exact assessment plan semantics."""
    plan = get_course_assessment_plan(1)
    assert plan is not None
    assert plan.course_id == 1
    assert plan.canonical_code == "21MAB101T"
    assert plan.course_name == "Calculus And Linear Algebra"
    
    comp_codes = [c.code for c in plan.components]
    assert comp_codes == ["CT1", "CT2", "ENDSEM"]
    
    # Normalization
    assert normalize_course_assessment_type(1, "FT2") == "CT2"
    assert normalize_course_assessment_type(1, "FT-II") == "CT2"
    assert normalize_course_assessment_type(1, "CLA-1") == "CT1"
    
    # Scope
    scope_endsem = get_course_assessment_scope(1, "ENDSEM", db=db)
    assert scope_endsem.has_authoritative_plan is True
    assert scope_endsem.has_authoritative_unit_scope is False
    assert scope_endsem.evidence_status == "UNPLANNED_OBSERVED_ONLY"
    
    scope_ct1 = get_course_assessment_scope(1, "CT1", db=db)
    assert scope_ct1.has_authoritative_plan is True
    assert scope_ct1.component_code == "CT1"


def test_course_23_behavior(db: Session):
    """Verify existing Course 23 (Building Materials) retains exact assessment plan semantics."""
    plan = get_course_assessment_plan(23)
    assert plan is not None
    assert plan.course_id == 23
    assert plan.canonical_code == "21CEB101T"
    assert plan.course_name == "Building Materials in the Built Environment"
    
    comp_codes = [c.code for c in plan.components]
    assert comp_codes == ["CT1", "CT2", "ENDSEM"]
    
    assert normalize_course_assessment_type(23, "CT1") == "CT1"
    assert normalize_course_assessment_type(23, "CT2") == "CT2"
    
    scope_ct1 = get_course_assessment_scope(23, "CT1", db=db)
    assert scope_ct1.has_authoritative_plan is True
    assert scope_ct1.component_code == "CT1"


def test_course_24_behavior(db: Session):
    """Verify Course 24 (Data Structures and Algorithms) resolves CLA-1, CLA-2, ENDSEM."""
    plan = get_course_assessment_plan(24)
    assert plan is not None
    assert plan.course_id == 24
    assert plan.canonical_code == "21CSC201J"
    assert plan.course_name == "Data Structures and Algorithms"
    
    comp_codes = [c.code for c in plan.components]
    assert comp_codes == ["CLA1", "CLA2", "ENDSEM"]
    
    # Normalization
    assert normalize_course_assessment_type(24, "CLA1") == "CLA1"
    assert normalize_course_assessment_type(24, "CLA-1") == "CLA1"
    assert normalize_course_assessment_type(24, "CT1") == "CLA1"
    assert normalize_course_assessment_type(24, "Cycle Test 1") == "CLA1"
    assert normalize_course_assessment_type(24, "CLA2") == "CLA2"
    assert normalize_course_assessment_type(24, "CLA-2") == "CLA2"
    assert normalize_course_assessment_type(24, "CT2") == "CLA2"
    assert normalize_course_assessment_type(24, "ENDSEM") == "ENDSEM"
    
    # Raw types for cycle
    cla1_raw = get_course_raw_types_for_cycle(24, "CLA1")
    assert "CLA1" in cla1_raw
    assert "CLA-1" in cla1_raw
    assert "CT1" in cla1_raw
    
    # Resolving cycle by CT1 alias
    ct1_raw = get_course_raw_types_for_cycle(24, "CT1")
    assert "CLA1" in ct1_raw
    assert "CLA-1" in ct1_raw
    
    # Scope for CLA1: authoritative units 1 and 2
    scope_cla1 = get_course_assessment_scope(24, "CLA1", db=db)
    assert scope_cla1.has_authoritative_plan is True
    assert scope_cla1.has_authoritative_unit_scope is True
    assert scope_cla1.in_scope_unit_numbers == {1, 2}
    assert scope_cla1.component_code == "CLA1"
    
    # Scope for CLA2: authoritative units 3, 4, 5
    scope_cla2 = get_course_assessment_scope(24, "CLA2", db=db)
    assert scope_cla2.has_authoritative_plan is True
    assert scope_cla2.has_authoritative_unit_scope is True
    assert scope_cla2.in_scope_unit_numbers == {3, 4, 5}
    assert scope_cla2.component_code == "CLA2"
    
    # Scope for ENDSEM
    scope_endsem = get_course_assessment_scope(24, "ENDSEM", db=db)
    assert scope_endsem.has_authoritative_plan is True
    assert scope_endsem.component_code == "ENDSEM"


def test_course_29_behavior(db: Session):
    """Verify Course 29 (Artificial Intelligence) resolves CLA-1, CLA-2, ENDSEM."""
    plan = get_course_assessment_plan(29)
    assert plan is not None
    assert plan.course_id == 29
    assert plan.canonical_code == "21CSC207J"
    assert plan.course_name == "Artificial Intelligence"
    
    comp_codes = [c.code for c in plan.components]
    assert comp_codes == ["CLA1", "CLA2", "ENDSEM"]
    
    # Scope for CLA1: units 1 and 2
    scope_cla1 = get_course_assessment_scope(29, "CLA1", db=db)
    assert scope_cla1.has_authoritative_plan is True
    assert scope_cla1.has_authoritative_unit_scope is True
    assert scope_cla1.in_scope_unit_numbers == {1, 2}
    
    # Scope for CLA2: units 3, 4, 5
    scope_cla2 = get_course_assessment_scope(29, "CLA2", db=db)
    assert scope_cla2.has_authoritative_plan is True
    assert scope_cla2.has_authoritative_unit_scope is True
    assert scope_cla2.in_scope_unit_numbers == {3, 4, 5}


def test_unsupported_course_fails_safely(db: Session):
    """Verify unsupported courses return None and safe unmapped scopes."""
    assert get_course_assessment_plan(9999) is None
    assert normalize_course_assessment_type(9999, "CT1") is None
    assert get_course_raw_types_for_cycle(9999, "CT1") == set()
    assert is_exam_in_course_cycle(9999, "CT1", "CT1") is False
    
    scope = get_course_assessment_scope(9999, "CT1", db=db)
    assert scope.has_authoritative_plan is False
    assert scope.has_authoritative_unit_scope is False
    assert scope.in_scope_unit_numbers == set()
    assert "No authoritative course assessment plan" in (scope.notes or "")


def test_invalid_cycle_fails_safely(db: Session):
    """Verify querying an unsupported or missing assessment cycle fails safely."""
    # 1. Non-existent cycle name
    scope_bogus = get_course_assessment_scope(1, "NON_EXISTENT_CYCLE", db=db)
    assert scope_bogus.has_authoritative_plan is False
    assert scope_bogus.has_authoritative_unit_scope is False
    assert scope_bogus.in_scope_unit_numbers == set()
    assert "does not exist in course 1 assessment plan" in (scope_bogus.notes or "")
    
    # 2. Cycle that exists in other courses but not Course 24 (Course 24 has no CT3)
    scope_ct3 = get_course_assessment_scope(24, "CT3", db=db)
    assert scope_ct3.has_authoritative_plan is False
    assert scope_ct3.has_authoritative_unit_scope is False
    assert scope_ct3.in_scope_unit_numbers == set()
    assert "does not exist in course 24 assessment plan" in (scope_ct3.notes or "")


def test_track_aware_behavior(db: Session):
    """Verify track-aware assessment plans resolve correctly for Foreign Languages (Course 8)."""
    # Track 1: German (21LEH104T)
    plan_german = get_course_assessment_plan(8, db=db, track_id=1)
    assert plan_german is not None
    assert "German" in plan_german.source_document
    
    scope_german = get_course_assessment_scope(8, "CT1", db=db, track_id=1)
    assert scope_german.has_authoritative_plan is True
    assert "German" in (scope_german.source_document or "")
    
    # Track 2: French (21LEH103T)
    plan_french = get_course_assessment_plan(8, db=db, track_id=2)
    assert plan_french is not None
    assert "French" in plan_french.source_document
    
    # Track separation verified
    assert plan_german.source_document != plan_french.source_document


def test_course_isolation_strict(db: Session):
    """Verify strict isolation between course assessment plans."""
    # Normalizing "FT2" on Course 1 maps to "CT2"
    assert normalize_course_assessment_type(1, "FT2") == "CT2"
    
    # Normalizing "FT IV" on Course 15 maps to "FT_IV"
    assert normalize_course_assessment_type(15, "FT IV") == "FT_IV"
    
    # Course 24 does not accept "FT2"
    assert normalize_course_assessment_type(24, "FT2") is None
    
    # Normalizing "CLA1" on Course 24 maps to "CLA1"
    assert normalize_course_assessment_type(24, "CLA1") == "CLA1"
    
    # Normalizing "CLA-1" on Course 1 maps to "CT1"
    assert normalize_course_assessment_type(1, "CLA-1") == "CT1"
