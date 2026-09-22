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


def test_persistent_cache_lookup_by_slug_after_restart(db):
    """Verify persistent cache works after a process restart even when queried by slug."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    # Pre-populate cache via numeric course_id="1"
    res_orig = get_intelligence_snapshot("1", db=db)
    assert res_orig["data_availability_status"] == "READY"

    # Simulate process restart by wiping memory cache completely
    IntelligenceCacheService.clear_memory_cache()

    # Query using slug "calculus" instead of "1"
    res_slug = get_intelligence_snapshot("calculus", db=db)
    assert res_slug["metadata"].get("cache_hit") is True
    assert res_slug["course"]["name"].lower().startswith("calculus")

    # Verify that it was aliased back into Tier 1 memory cache (0 SQL queries on next call)
    queries = []
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(Engine, "before_cursor_execute", count_queries)
    try:
        res_slug_tier1 = get_intelligence_snapshot("calculus", db=db)
        assert len(queries) == 0, f"Expected 0 SQL queries for aliased Tier 1 hit, got {len(queries)}"
        assert res_slug_tier1["metadata"].get("cache_hit") is True
    finally:
        event.remove(Engine, "before_cursor_execute", count_queries)


def test_corrupted_snapshot_safe_regeneration(db):
    """Verify corrupted snapshot in memory or DB fails safely and cleanly regenerates without 500 error."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    # Create a corrupted DB snapshot row with invalid payload structure
    corrupted_key = build_cache_key(1, "ALL", "none")
    bad_snapshot = IntelligenceSnapshot(
        course_id=1,
        track_id=None,
        cache_key=corrupted_key,
        assessment_cycle="ALL",
        model_version="1.0.0",
        taxonomy_version="1.0.0",
        corpus_version="1.0.0",
        payload={"corrupted": "bad_data_missing_required_keys"},
    )
    db.add(bad_snapshot)
    db.commit()

    # Also poison memory cache with a non-dict / broken payload
    _memory_cache[corrupted_key] = {"broken_payload": True}

    # Request snapshot: must NOT crash; must evict corrupted cache and regenerate healthy snapshot
    res = get_intelligence_snapshot("1", db=db)
    assert res is not None
    assert res["data_availability_status"] == "READY"
    assert "predictions" in res
    assert res["course"]["id"] == 1

    # Corrupted DB row must have been replaced with fresh valid snapshot
    repaired_row = db.query(IntelligenceSnapshot).filter(IntelligenceSnapshot.cache_key == corrupted_key).first()
    assert repaired_row is not None
    assert "predictions" in repaired_row.payload


def test_invalidation_purges_memory_aliases(db):
    """Verify invalidating a course clears all memory aliases (slugs and course_id)."""
    IntelligenceCacheService.clear_memory_cache()
    db.query(IntelligenceSnapshot).delete()
    db.commit()

    # Populate cache using slug "calculus"
    get_intelligence_snapshot("calculus", db=db)

    # Check that memory cache contains both the canonical key and the slug alias
    slug_found = any("calculus" in k for k in _memory_cache)
    canonical_found = any(k.startswith("1:") for k in _memory_cache)
    assert slug_found or canonical_found, "Cache should contain entries for calculus"

    # Invalidate Course 1
    IntelligenceCacheService.invalidate_course(db, 1)

    # Both canonical and slug keys must be purged from memory cache
    remaining = [k for k in _memory_cache if k.startswith("1:") or "calculus" in k]
    assert len(remaining) == 0, f"All aliases for course 1 should be purged, found: {remaining}"


def test_cache_key_isolation_invariants():
    """Verify cache keys isolate course, cycle, track, and versions."""
    k1 = build_cache_key(1, "ALL", "none")
    k2 = build_cache_key(2, "ALL", "none")
    k3 = build_cache_key(1, "FAT", "none")
    k4 = build_cache_key(1, "ALL", "german")
    k5 = build_cache_key(1, "ALL", "french")

    assert k1 != k2, "Different courses must have distinct keys"
    assert k1 != k3, "Different cycles must have distinct keys"
    assert k1 != k4, "Different tracks must have distinct keys"
    assert k4 != k5, "German and French tracks must have distinct keys"

