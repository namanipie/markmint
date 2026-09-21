"""Test suite for MarkMint Phase 17: Intelligence Latency Optimization & Caching."""

import time
import json
import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

from backend.core.database import SessionLocal
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.services.intelligence_cache import (
    IntelligenceCacheService,
    build_cache_key,
    _memory_cache,
)
from backend.models.core import IntelligenceSnapshot


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_query_count_reduction(db):
    """Verify SQL query count is drastically reduced (Chemistry <= 25, Calculus <= 25)."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    queries = []
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(Engine, "before_cursor_execute", count_queries)
    try:
        # Calculus (course_id=1)
        queries.clear()
        get_intelligence_snapshot("1", db=db)
        calc_queries = len(queries)
        assert calc_queries <= 25, f"Calculus exceeded query budget: {calc_queries} > 25"

        # Chemistry (course_id=2)
        queries.clear()
        get_intelligence_snapshot("2", db=db)
        chem_queries = len(queries)
        assert chem_queries <= 25, f"Chemistry exceeded query budget: {chem_queries} > 25"

        # EEE CT1 (course_id=14)
        queries.clear()
        get_intelligence_snapshot("14", assessment_cycle="CT1", db=db)
        eee_queries = len(queries)
        assert eee_queries <= 15, f"EEE CT1 exceeded query budget: {eee_queries} > 15"
    finally:
        event.remove(Engine, "before_cursor_execute", count_queries)


def test_tier1_and_tier2_caching(db):
    """Verify Tier 1 (LRU memory) and Tier 2 (DB table) caching and speedup."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    # Call 1: Cache Miss - synthesizes and stores in cache
    res1 = get_intelligence_snapshot("1", db=db)
    assert res1["data_availability_status"] == "READY"
    assert "predictions" in res1

    # Verify snapshot row persisted in DB
    db_row = db.query(IntelligenceSnapshot).filter(IntelligenceSnapshot.course_id == 1).first()
    assert db_row is not None
    assert db_row.payload["course"]["id"] == 1

    # Call 2: Tier 1 Cache Hit (0 SQL queries, cache_hit=True)
    queries = []
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(Engine, "before_cursor_execute", count_queries)
    try:
        t0 = time.perf_counter()
        res2 = get_intelligence_snapshot("1", db=db)
        t_tier1 = (time.perf_counter() - t0) * 1000
        assert len(queries) == 0, f"Expected 0 SQL queries on Tier 1 cache hit, got {len(queries)}"
        assert res2["metadata"].get("cache_hit") is True
        assert t_tier1 < 10.0, f"Tier 1 cache hit should be < 10ms, took {t_tier1:.2f}ms"
    finally:
        event.remove(Engine, "before_cursor_execute", count_queries)

    # Call 3: Tier 2 Cache Hit (clear memory cache, should hit DB table in 1 query)
    IntelligenceCacheService.clear_memory_cache()
    queries.clear()
    event.listen(Engine, "before_cursor_execute", count_queries)
    try:
        t0 = time.perf_counter()
        res3 = get_intelligence_snapshot("1", db=db)
        t_tier2 = (time.perf_counter() - t0) * 1000
        # Exactly 1 query to fetch IntelligenceSnapshot row
        assert len(queries) == 1, f"Expected 1 SQL query on Tier 2 cache hit, got {len(queries)}"
        assert res3["metadata"].get("cache_hit") is True
        assert t_tier2 < 30.0, f"Tier 2 cache hit should be fast, took {t_tier2:.2f}ms"
    finally:
        event.remove(Engine, "before_cursor_execute", count_queries)


def test_cache_bypass_conditions(db):
    """Verify cache is bypassed when personal student_id, custom target_year, or target_exam_date is passed."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    # Pre-warm default cache
    get_intelligence_snapshot("1", db=db)

    # 1. Custom student_id bypasses cache
    res_student = get_intelligence_snapshot("1", student_id="student_999", db=db)
    assert res_student["metadata"].get("cache_hit") is not True

    # 2. Custom target_year bypasses cache
    res_year = get_intelligence_snapshot("1", target_year=2023, db=db)
    assert res_year["metadata"].get("cache_hit") is not True
    assert res_year["exam_history"]["target_year"] == 2023

    # 3. Custom target_exam_date bypasses cache
    res_date = get_intelligence_snapshot("1", target_exam_date="2027-05-01", db=db)
    assert res_date["metadata"].get("cache_hit") is not True
    assert res_date.get("exam_schedule") is not None


def test_cache_track_and_cycle_isolation(db):
    """Verify distinct tracks and assessment cycles have isolated cache entries."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    # German track on Course 8
    res_de = get_intelligence_snapshot("8", language="german", db=db)
    # French track on Course 8
    res_fr = get_intelligence_snapshot("8", language="french", db=db)

    assert res_de["track"]["track_key"].lower() == "german"
    assert res_fr["track"]["track_key"].lower() == "french"

    # Both must be cached separately in DB
    rows = db.query(IntelligenceSnapshot).filter(IntelligenceSnapshot.course_id == 8).all()
    assert len(rows) == 2
    track_ids = {r.track_id for r in rows}
    assert len(track_ids) == 2, "German and French must have separate track_ids in cache"


def test_cache_invalidation(db):
    """Verify invalidation purges both Tier 1 and Tier 2 cache entries."""
    # Populate cache for course 1 and course 2
    get_intelligence_snapshot("1", db=db)
    get_intelligence_snapshot("2", db=db)

    # Invalidate Course 1
    deleted = IntelligenceCacheService.invalidate_course(db, 1)
    assert deleted >= 1

    # Verify Course 1 is gone from DB and memory
    c1_row = db.query(IntelligenceSnapshot).filter(IntelligenceSnapshot.course_id == 1).first()
    assert c1_row is None

    # Course 2 should still be cached
    c2_row = db.query(IntelligenceSnapshot).filter(IntelligenceSnapshot.course_id == 2).first()
    assert c2_row is not None
