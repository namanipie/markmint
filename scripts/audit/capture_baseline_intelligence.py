"""
Step 1: Capture baseline measurements and exact JSON payloads for:
Calculus (1), Chemistry (2), EEE CT1 (14), OODP (16), German (8), French (8).
"""
import time
import json
import os
import sys
from sqlalchemy import event
from sqlalchemy.engine import Engine

sys.path.insert(0, os.path.abspath("."))
from backend.core.database import SessionLocal
from backend.api.endpoints.intelligence import get_intelligence_snapshot

CASES = [
    ("calculus", "1", None, None),
    ("chemistry", "2", None, None),
    ("eee_ct1", "14", "CT1", None),
    ("oodp", "16", None, None),
    ("german", "8", None, "german"),
    ("french", "8", None, "french"),
]

def capture_baseline():
    os.makedirs("data/baseline_intelligence", exist_ok=True)
    baseline_stats = {}

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
            res = get_intelligence_snapshot(
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

        total_sql_time = sum(q[1] for q in queries)
        payload_bytes = len(json.dumps(res, default=str))

        # Save baseline payload
        payload_file = f"data/baseline_intelligence/{name}_baseline.json"
        with open(payload_file, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, default=str)

        baseline_stats[name] = {
            "course_id": cid,
            "cycle": cycle,
            "language": lang,
            "queries_count": len(queries),
            "backend_compute_ms": t_total,
            "sql_time_ms": total_sql_time,
            "payload_bytes": payload_bytes,
            "predictions_count": len(res.get("predictions", [])),
            "priorities_count": len(res.get("study_priorities", [])),
        }

        print(f"Captured {name:<12} (id={cid}): {len(queries):3d} queries | {t_total:6.1f}ms | {payload_bytes/1024:5.1f} KB")

    with open("data/baseline_intelligence/stats.json", "w", encoding="utf-8") as f:
        json.dump(baseline_stats, f, indent=2)

    print("\nBaseline capture complete. Saved to data/baseline_intelligence/")

if __name__ == "__main__":
    capture_baseline()
