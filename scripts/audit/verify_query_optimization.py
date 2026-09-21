"""
Verify query counts, compute times, and semantic equivalence of optimized get_intelligence_snapshot.
Tests both:
1. Uncached Algorithmic Optimization (Chemistry 867 -> 22, Calculus 321 -> 22)
2. Cached Fast-Path (0 SQL queries, < 1ms)
"""
import time
import json
import os
import sys
from sqlalchemy import event
from sqlalchemy.engine import Engine

sys.path.insert(0, os.path.abspath("."))
from backend.core.database import SessionLocal
from backend.models.core import IntelligenceSnapshot
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.services.intelligence_cache import IntelligenceCacheService

CASES = [
    ("calculus", "1", None, None),
    ("chemistry", "2", None, None),
    ("eee_ct1", "14", "CT1", None),
    ("oodp", "16", None, None),
    ("german", "8", None, "german"),
    ("french", "8", None, "french"),
]

def clean_metadata(payload):
    p = json.loads(json.dumps(payload, default=str))
    if "metadata" in p:
        p["metadata"].pop("generated_at", None)
        p["metadata"].pop("latency_ms", None)
        p["metadata"].pop("cache_hit", None)
    if "available_assessment_types" in p and isinstance(p["available_assessment_types"], list):
        p["available_assessment_types"] = sorted(p["available_assessment_types"])
    if "exam_history" in p and isinstance(p["exam_history"], dict):
        if "available_assessment_types" in p["exam_history"] and isinstance(p["exam_history"]["available_assessment_types"], list):
            p["exam_history"]["available_assessment_types"] = sorted(p["exam_history"]["available_assessment_types"])
    return p

def verify():
    with open("data/baseline_intelligence/stats.json", "r", encoding="utf-8") as f:
        baseline_stats = json.load(f)

    # 1. Reset caches for clean uncached test
    IntelligenceCacheService.clear_memory_cache()
    db = SessionLocal()
    db.query(IntelligenceSnapshot).delete()
    db.commit()
    db.close()

    print("=== PART 1: UNCACHED ALGORITHMIC OPTIMIZATION ===")
    print(f"{'Course':<12} | {'Old Queries':<11} | {'New Queries':<11} | {'Reduction':<10} | {'Old Time':<10} | {'New Time':<10} | {'Semantic Match'}")
    print("-" * 88)

    all_passed = True

    for name, cid, cycle, lang in CASES:
        db = SessionLocal()
        queries = []

        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.perf_counter()

        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = (time.perf_counter() - context._query_start_time) * 1000
            queries.append((statement, total_time))

        event.listen(Engine, "before_cursor_execute", before_cursor_execute)
        event.listen(Engine, "after_cursor_execute", after_cursor_execute)

        try:
            t0 = time.perf_counter()
            new_res = get_intelligence_snapshot(
                course_id=cid,
                target_year=None,
                target_exam_date=None,
                student_id="anonymous",
                assessment_cycle=cycle,
                language=lang,
                db=db
            )
            t_total = (time.perf_counter() - t0) * 1000
        finally:
            event.remove(Engine, "before_cursor_execute", before_cursor_execute)
            event.remove(Engine, "after_cursor_execute", after_cursor_execute)
            db.close()

        old_stat = baseline_stats[name]
        old_q = old_stat["queries_count"]
        new_q = len(queries)
        reduction = f"-{((old_q - new_q) / old_q) * 100:.1f}%"

        with open(f"data/baseline_intelligence/{name}_baseline.json", "r", encoding="utf-8") as f:
            base_res = json.load(f)

        clean_base = clean_metadata(base_res)
        clean_new = clean_metadata(new_res)

        semantic_match = (clean_base == clean_new)
        if not semantic_match:
            all_passed = False
            print(f"\n[DIFF for {name}]")
            for key in clean_base:
                if clean_base[key] != clean_new.get(key):
                    print(f"  Field mismatch: {key}")

        status_str = "EXACT MATCH (100%)" if semantic_match else "MISMATCH"
        print(f"{name:<12} | {old_q:<11d} | {new_q:<11d} | {reduction:<10} | {old_stat['backend_compute_ms']:6.1f}ms   | {t_total:6.1f}ms   | {status_str}")

    print("-" * 88)

    print("\n=== PART 2: TIER 1 CACHED WARM PATH (LRU MEMORY) ===")
    print(f"{'Course':<12} | {'Queries':<11} | {'Latency':<10} | {'Cache Hit':<10}")
    print("-" * 55)

    for name, cid, cycle, lang in CASES:
        db = SessionLocal()
        queries = []
        def append_query(c, cu, s, p, co, e):
            queries.append(s)

        event.listen(Engine, "before_cursor_execute", append_query)
        try:
            t0 = time.perf_counter()
            cached_res = get_intelligence_snapshot(
                course_id=cid,
                target_year=None,
                target_exam_date=None,
                student_id="anonymous",
                assessment_cycle=cycle,
                language=lang,
                db=db
            )
            t_cached = (time.perf_counter() - t0) * 1000
        finally:
            event.remove(Engine, "before_cursor_execute", append_query)
            db.close()

        cache_hit = cached_res.get("metadata", {}).get("cache_hit", False)
        print(f"{name:<12} | {len(queries):<11d} | {t_cached:6.2f}ms   | {str(cache_hit):<10}")
        if len(queries) != 0 or not cache_hit:
            all_passed = False

    print("-" * 55)

    if all_passed:
        print("\nALL TESTS PASSED PERFECTLY!")
    else:
        print("\nSOME CHECKS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    verify()
