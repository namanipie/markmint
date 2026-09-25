"""Comprehensive tests for intelligence cache lifecycle and hardening.

Verifies:
1. Equivalent semantic requests generate identical cache keys.
2. Different courses generate different keys.
3. Different target years / cutoffs generate different keys.
4. Different assessment scopes generate different keys.
5. Different tracks/languages generate different keys.
6. Anonymous requests cannot consume personalized cache entries.
7. Student A cannot consume Student B's cache.
8. Successful ingestion invalidates affected course cache (Tier 1, Tier 2, and analysis cache).
9. Failed ingestion does not invalidate existing cache.
10. Multi-course invalidation invalidates all affected courses.
11. Bounded cache never exceeds configured maximum.
12. Cache eviction behaves deterministically (LRU).
13. Cache invalidation is idempotent.
14. Existing intelligence output is unchanged for identical underlying data.
15. Existing temporal isolation remains intact.
"""

import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.core import Base, Course, Exam, Section, Question, IntelligenceSnapshot, CourseTrack
from backend.services.intelligence_cache import (
    IntelligenceCacheService,
    BoundedAnalysisCache,
    build_cache_key,
    canonicalize_identifier,
    canonicalize_cycle,
    canonicalize_track,
    canonicalize_student_id,
    analysis_cache,
)
from backend.services.assessment_cycle import AssessmentCycle
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository


@pytest.fixture
def isolated_db():
    """Create isolated SQLite database for cache lifecycle tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    course1 = Course(id=1, code="21MAB101T", name="Calculus")
    course2 = Course(id=2, code="21CYB101J", name="Chemistry")
    course8 = Course(id=8, code="21FLS101J", name="Foreign Language")
    track_de = CourseTrack(id=1, course_id=8, track_key="german", track_name="German")
    track_fr = CourseTrack(id=2, course_id=8, track_key="french", track_name="French")

    session.add_all([course1, course2, course8, track_de, track_fr])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    IntelligenceCacheService.clear_memory_cache()


def test_1_equivalent_semantic_requests_generate_identical_keys():
    """1. Equivalent semantic requests generate identical canonical cache keys."""
    # Identifier representations (int, str, padded str)
    key_int = build_cache_key(2, "CT1", "german")
    key_str = build_cache_key("2", "CT1", "german")
    key_pad = build_cache_key("  2  ", "CT1", "german")
    assert key_int == key_str == key_pad

    # Cycle case and padding variations
    key_cycle1 = build_cache_key(2, "CT1")
    key_cycle2 = build_cache_key(2, "ct1")
    key_cycle3 = build_cache_key(2, "  ct1  ")
    assert key_cycle1 == key_cycle2 == key_cycle3

    # None vs empty vs ALL cycle
    key_all1 = build_cache_key(2, None)
    key_all2 = build_cache_key(2, "")
    key_all3 = build_cache_key(2, "ALL")
    key_all4 = build_cache_key(2, "all")
    assert key_all1 == key_all2 == key_all3 == key_all4

    # Anonymous student variants
    key_anon_none = build_cache_key(2, "CT1", student_id=None)
    key_anon_empty = build_cache_key(2, "CT1", student_id="")
    key_anon_spaces = build_cache_key(2, "CT1", student_id="   ")
    key_anon_str = build_cache_key(2, "CT1", student_id="anonymous")
    key_anon_upper = build_cache_key(2, "CT1", student_id="ANONYMOUS")
    assert key_anon_none == key_anon_empty == key_anon_spaces == key_anon_str == key_anon_upper


def test_2_different_courses_generate_different_keys():
    """2. Different courses generate different cache keys."""
    key_c1 = build_cache_key(1, "CT1")
    key_c2 = build_cache_key(2, "CT1")
    key_c8 = build_cache_key(8, "CT1")
    assert key_c1 != key_c2
    assert key_c2 != key_c8
    assert key_c1 != key_c8


def test_3_different_target_years_generate_different_keys():
    """3. Different target years / cutoffs generate different keys."""
    key_no_cutoff = build_cache_key(2, "CT1")
    key_2023 = build_cache_key(2, "CT1", cutoff_year=2023)
    key_2024 = build_cache_key(2, "CT1", cutoff_year=2024)

    assert key_no_cutoff != key_2023
    assert key_2023 != key_2024
    assert ":cutoff:2023" in key_2023
    assert ":cutoff:2024" in key_2024


def test_4_different_assessment_scopes_generate_different_keys():
    """4. Different assessment scopes generate different keys."""
    key_all = build_cache_key(2, "ALL")
    key_ct1 = build_cache_key(2, "CT1")
    key_ct2 = build_cache_key(2, "CT2")
    key_endsem = build_cache_key(2, "ENDSEM")

    assert len({key_all, key_ct1, key_ct2, key_endsem}) == 4


def test_5_different_tracks_generate_different_keys():
    """5. Different tracks/languages generate different keys."""
    key_none = build_cache_key(8, "CT1", track=None)
    key_german = build_cache_key(8, "CT1", track="german")
    key_french = build_cache_key(8, "CT1", track="french")

    assert key_none != key_german
    assert key_german != key_french
    assert key_none != key_french


def test_6_anonymous_cannot_consume_personalized_cache():
    """6. Anonymous requests cannot consume personalized cache entries."""
    key_anon = build_cache_key(2, "CT1", student_id="anonymous")
    key_student = build_cache_key(2, "CT1", student_id="student_123")

    assert ":student:" not in key_anon
    assert ":student:student_123" in key_student
    assert key_anon != key_student


def test_7_student_a_cannot_consume_student_b_cache():
    """7. Student A cannot consume Student B's cache."""
    key_a = build_cache_key(2, "CT1", student_id="student_A")
    key_b = build_cache_key(2, "CT1", student_id="student_B")

    assert key_a != key_b
    assert ":student:student_A" in key_a
    assert ":student:student_B" in key_b


def test_8_successful_ingestion_invalidates_affected_course_cache(isolated_db):
    """8. Successful ingestion invalidates affected course cache across Tier 1, Tier 2, and analysis cache."""
    IntelligenceCacheService.clear_memory_cache()

    payload = {
        "data_availability_status": "SUFFICIENT",
        "course": {"id": 1, "name": "Calculus"},
        "metadata": {"generated": True},
        "predictions": [{"topic": "Derivatives", "score": 0.85}],
    }

    # Populate Tier 1 and Tier 2
    IntelligenceCacheService.store_snapshot(
        db=isolated_db,
        course_id=1,
        assessment_cycle="ALL",
        track_id=None,
        payload=payload,
    )

    # Populate analysis cache for course 1
    analysis_cache.set((1, "ALL", None, None, "dna"), {"dna_metric": 42})
    analysis_cache.set((1, "ALL", "evolution"), {"trend": "increasing"})

    # Verify all are populated
    assert IntelligenceCacheService.get_snapshot(isolated_db, 1) is not None
    assert analysis_cache.get((1, "ALL", None, None, "dna")) is not None
    assert analysis_cache.get((1, "ALL", "evolution")) is not None

    # Invalidate course 1
    deleted_db = IntelligenceCacheService.invalidate_course(isolated_db, course_id=1)
    assert deleted_db >= 1

    # Verify all are invalidated
    assert IntelligenceCacheService.get_snapshot(isolated_db, 1) is None
    assert analysis_cache.get((1, "ALL", None, None, "dna")) is None
    assert analysis_cache.get((1, "ALL", "evolution")) is None


def test_9_failed_ingestion_does_not_invalidate_existing_cache(isolated_db):
    """9. Failed ingestion does not invalidate existing cache."""
    IntelligenceCacheService.clear_memory_cache()

    payload = {
        "data_availability_status": "SUFFICIENT",
        "course": {"id": 2, "name": "Chemistry"},
        "metadata": {"generated": True},
    }
    IntelligenceCacheService.store_snapshot(
        db=isolated_db,
        course_id=2,
        assessment_cycle="ALL",
        track_id=None,
        payload=payload,
    )
    analysis_cache.set((2, "ALL", None, None, "dna"), {"status": "valid"})

    # Simulate an aborted/failed ingestion transaction
    try:
        isolated_db.begin_nested()
        isolated_db.add(Exam(course_id=2, year=2025, assessment_type="INVALID"))
        raise ValueError("Simulated parsing/ingestion failure before commit")
    except ValueError:
        isolated_db.rollback()

    # Cache must remain intact and valid
    cached = IntelligenceCacheService.get_snapshot(isolated_db, 2)
    assert cached is not None
    assert cached["course"]["name"] == "Chemistry"
    assert analysis_cache.get((2, "ALL", None, None, "dna")) == {"status": "valid"}


def test_10_multi_course_invalidation_invalidates_all_affected(isolated_db):
    """10. Multi-course invalidation invalidates all affected courses."""
    IntelligenceCacheService.clear_memory_cache()

    payload1 = {"data_availability_status": "SUFFICIENT", "course": {"id": 1}, "metadata": {}}
    payload2 = {"data_availability_status": "SUFFICIENT", "course": {"id": 2}, "metadata": {}}

    IntelligenceCacheService.store_snapshot(isolated_db, 1, "ALL", None, payload1)
    IntelligenceCacheService.store_snapshot(isolated_db, 2, "ALL", None, payload2)
    analysis_cache.set((1, "ALL", None, None, "dna"), {"c": 1})
    analysis_cache.set((2, "ALL", None, None, "dna"), {"c": 2})

    for cid in [1, 2]:
        IntelligenceCacheService.invalidate_course(isolated_db, cid)

    assert IntelligenceCacheService.get_snapshot(isolated_db, 1) is None
    assert IntelligenceCacheService.get_snapshot(isolated_db, 2) is None
    assert analysis_cache.get((1, "ALL", None, None, "dna")) is None
    assert analysis_cache.get((2, "ALL", None, None, "dna")) is None


def test_11_bounded_cache_never_exceeds_maximum():
    """11. Bounded cache never exceeds configured maximum entries."""
    bounded = BoundedAnalysisCache(max_size=5, ttl=60.0)

    for i in range(20):
        bounded.set((i, "ALL", "dna"), {"val": i})

    assert len(bounded) == 5


def test_12_cache_eviction_behaves_deterministically():
    """12. Cache eviction behaves deterministically according to LRU."""
    bounded = BoundedAnalysisCache(max_size=3, ttl=60.0)

    bounded.set("a", 1)
    bounded.set("b", 2)
    bounded.set("c", 3)

    # Touch 'a' so 'b' becomes the oldest
    assert bounded.get("a") == 1

    # Insert 'd' -> 'b' should be evicted
    bounded.set("d", 4)

    assert bounded.get("a") == 1
    assert bounded.get("b") is None
    assert bounded.get("c") == 3
    assert bounded.get("d") == 4


def test_13_cache_invalidation_is_idempotent(isolated_db):
    """13. Cache invalidation is idempotent and safe to repeat."""
    deleted_1 = IntelligenceCacheService.invalidate_course(isolated_db, course_id=999)
    deleted_2 = IntelligenceCacheService.invalidate_course(isolated_db, course_id=999)

    assert deleted_1 == 0
    assert deleted_2 == 0


def test_14_existing_intelligence_output_is_unchanged(isolated_db):
    """14. Existing intelligence snapshot output is unchanged for identical underlying data."""
    IntelligenceCacheService.clear_memory_cache()

    original_payload = {
        "data_availability_status": "SUFFICIENT",
        "course": {"id": 1, "code": "21MAB101T", "name": "Calculus"},
        "metadata": {"model_version": "2.0"},
        "predictions": [{"topic": "Integrals", "score": 0.92}],
    }

    IntelligenceCacheService.store_snapshot(
        isolated_db,
        course_id=1,
        assessment_cycle="ALL",
        track_id=None,
        payload=original_payload,
    )

    cached_1 = IntelligenceCacheService.get_snapshot(isolated_db, 1, "ALL")
    cached_2 = IntelligenceCacheService.get_snapshot(isolated_db, "1", "ALL")

    assert cached_1 == original_payload
    assert cached_2 == original_payload


def test_15_existing_temporal_isolation_remains_intact(isolated_db):
    """15. Existing temporal isolation remains intact (cutoff_year strictly isolates historical data)."""
    # Create exams for years 2021, 2022, 2023, 2024
    exam21 = Exam(course_id=1, year=2021, assessment_type="ENDSEM")
    exam22 = Exam(course_id=1, year=2022, assessment_type="ENDSEM")
    exam23 = Exam(course_id=1, year=2023, assessment_type="ENDSEM")
    exam24 = Exam(course_id=1, year=2024, assessment_type="ENDSEM")
    isolated_db.add_all([exam21, exam22, exam23, exam24])
    isolated_db.commit()

    context = HistoricalContext(course_id=1, cutoff_year=2023)
    repo = HistoricalRepository(isolated_db, context)

    historical_exams = repo.get_historical_exams()
    historical_years = [e.year for e in historical_exams]

    # Historical exams must strictly exclude >= 2023
    assert all(y < 2023 for y in historical_years)
    assert 2023 not in historical_years
    assert 2024 not in historical_years
    assert set(historical_years) == {2021, 2022}
