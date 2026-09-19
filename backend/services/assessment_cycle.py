"""
Canonical Assessment Cycle Normalization Service.

Defines the canonical assessment cycles for MarkMint (ALL, CT1, CT2, ENDSEM),
normalizes variant database labels and user queries, and provides query filter builders.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import func


class AssessmentCycle(str, Enum):
    ALL = "ALL"
    CT1 = "CT1"
    CT2 = "CT2"
    ENDSEM = "ENDSEM"


CYCLE_LABELS: Dict[str, str] = {
    AssessmentCycle.ALL.value: "All Assessments",
    AssessmentCycle.CT1.value: "CT1",
    AssessmentCycle.CT2.value: "CT2",
    AssessmentCycle.ENDSEM.value: "End Semester",
}

# Explicit database assessment_type strings mapped to canonical cycles
CYCLE_TO_RAW_TYPES: Dict[str, Set[str]] = {
    AssessmentCycle.CT1.value: {
        "CT1",
        "CT-1",
        "CYCLE TEST 1",
        "CYCLE TEST - 1",
        "CYCLE TEST-1",
        "CAT 1",
        "CAT-1",
        "CAT1",
        "CLA1",
        "CLA-1",
        "CLA 1",
        "INTERNAL ASSESSMENT - 1",
        "INTERNAL ASSESSMENT - I",
        "INTERNAL ASSESSMENT - I [FJI]",
        "FJ-1",
    },
    AssessmentCycle.CT2.value: {
        "CT2",
        "CT-2",
        "CYCLE TEST 2",
        "CYCLE TEST - 2",
        "CYCLE TEST-2",
        "CAT 2",
        "CAT-2",
        "CAT2",
        "CLA-T2",
        "CLAT-2",
        "CLA2",
        "CLA-2",
        "CLA 2",
        "FT2",
        "FT-II",
        "FT - II",
        "INTERNAL ASSESSMENT - 2",
        "INTERNAL ASSESSMENT - II",
    },
    AssessmentCycle.ENDSEM.value: {
        "END_SEM",
        "ENDSEM",
        "END SEM",
        "END-SEM",
        "END_SEMESTER",
        "END SEMESTER",
        "END-SEMESTER",
        "DEGREE EXAMINATION",
        "SEMESTER EXAMINATION",
        "UNIVERSITY EXAMINATION",
    },
}

# Reverse lookup for fast normalization of raw string variants
_RAW_TO_CYCLE: Dict[str, str] = {}
for cycle, raw_set in CYCLE_TO_RAW_TYPES.items():
    for raw in raw_set:
        _RAW_TO_CYCLE[raw.upper()] = cycle

# Additional user/query string aliases
_QUERY_ALIASES: Dict[str, str] = {
    "ALL": AssessmentCycle.ALL.value,
    "ALL ASSESSMENTS": AssessmentCycle.ALL.value,
    "ALL_ASSESSMENTS": AssessmentCycle.ALL.value,
    "*": AssessmentCycle.ALL.value,
    "CT1": AssessmentCycle.CT1.value,
    "CT 1": AssessmentCycle.CT1.value,
    "CYCLE 1": AssessmentCycle.CT1.value,
    "INTERNAL 1": AssessmentCycle.CT1.value,
    "INTERNAL I": AssessmentCycle.CT1.value,
    "CT2": AssessmentCycle.CT2.value,
    "CT 2": AssessmentCycle.CT2.value,
    "CYCLE 2": AssessmentCycle.CT2.value,
    "INTERNAL 2": AssessmentCycle.CT2.value,
    "INTERNAL II": AssessmentCycle.CT2.value,
    "ENDSEM": AssessmentCycle.ENDSEM.value,
    "END SEM": AssessmentCycle.ENDSEM.value,
    "END SEMESTER": AssessmentCycle.ENDSEM.value,
    "END_SEMESTER": AssessmentCycle.ENDSEM.value,
    "END-SEMESTER": AssessmentCycle.ENDSEM.value,
    "SEMESTER": AssessmentCycle.ENDSEM.value,
    "DEGREE": AssessmentCycle.ENDSEM.value,
}


def normalize_assessment_cycle(val: Any) -> Optional[str]:
    """
    Normalize an input string (from URL query, database, or UI) into a canonical cycle.
    Handles FastAPI Query objects gracefully when endpoints are called directly in unit tests.
    Returns:
        - "ALL" if val is "ALL" or an "all" alias
        - "CT1", "CT2", or "ENDSEM" for recognized cycles
        - Normalized uppercase string if an explicit unmapped type is provided (e.g. "CT3")
        - None if val is None or empty
    """
    if val is None:
        return None
    
    # Handle FastAPI Query / params default objects
    if hasattr(val, "default"):
        val = val.default
    
    if val is None or not isinstance(val, str):
        return None
    
    clean = val.strip()
    if not clean:
        return None
    
    upper = clean.upper()
    if upper in _QUERY_ALIASES:
        return _QUERY_ALIASES[upper]
    
    if upper in _RAW_TO_CYCLE:
        return _RAW_TO_CYCLE[upper]
    
    stripped = upper.replace("-", " ").replace("_", " ")
    if stripped in _QUERY_ALIASES:
        return _QUERY_ALIASES[stripped]
    
    return upper


def get_raw_types_for_cycle(canonical_cycle: Optional[str]) -> Set[str]:
    """Return the set of raw database assessment_type strings for a canonical cycle."""
    if not canonical_cycle or canonical_cycle == AssessmentCycle.ALL.value:
        return set()
    
    norm = normalize_assessment_cycle(canonical_cycle)
    if norm in CYCLE_TO_RAW_TYPES:
        return CYCLE_TO_RAW_TYPES[norm]
    
    return {canonical_cycle.upper()}


def is_exam_in_cycle(exam_assessment_type: Optional[str], canonical_cycle: Optional[str]) -> bool:
    """Check whether a single exam's assessment_type matches the selected canonical cycle."""
    if not canonical_cycle or canonical_cycle == AssessmentCycle.ALL.value:
        return True
    
    if not exam_assessment_type:
        return False
    
    raw_types = get_raw_types_for_cycle(canonical_cycle)
    return exam_assessment_type.upper() in {t.upper() for t in raw_types}


def filter_exams_by_cycle(query, exam_col, canonical_cycle: Optional[str]):
    """Apply assessment cycle filter to an existing SQLAlchemy query."""
    if not canonical_cycle or canonical_cycle == AssessmentCycle.ALL.value:
        return query
    
    raw_types = get_raw_types_for_cycle(canonical_cycle)
    if not raw_types:
        return query
    
    return query.filter(func.upper(exam_col).in_([t.upper() for t in raw_types]))
