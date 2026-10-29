import time
import os
import sys
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import event
from sqlalchemy.engine import Engine
from backend.core.database import SessionLocal, engine
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.models.core import Course, Exam, Question, Topic, QuestionFamily, Section

def profile_course(cid: str, cycle: str = None, language: str = None):
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
            language=language,
            db=db
        )
        t_total = (time.perf_counter() - t0) * 1000
    finally:
        event.remove(Engine, "before_cursor_execute", before_cursor_execute)
        event.remove(Engine, "after_cursor_execute", after_cursor_execute)
        db.close()

    total_query_time = sum(q[1] for q in queries)
    # Detect duplicate / similar query patterns
    from collections import Counter
    query_templates = Counter([q[0].split("WHERE")[0].strip() for q in queries])

    course_obj = db.query(Course).filter(Course.id == int(cid)).first() if cid.isdigit() else None
    cname = course_obj.name if course_obj else cid

    print(f"\n{'='*70}")
    print(f"PROFILE FOR: {cname} (ID: {cid}, cycle={cycle}, lang={language})")
    print(f"{'='*70}")
    print(f"Total Wall Time      : {t_total:7.1f} ms")
    print(f"Total SQL Queries    : {len(queries)}")
    print(f"Total SQL Query Time : {total_query_time:7.1f} ms")
    print(f"Python CPU / Compute : {t_total - total_query_time:7.1f} ms")
    print("\nTop Repeated Query Types:")
    for template, count in query_templates.most_common(8):
        print(f"  [{count:3d}x] {template[:90]}...")
    
    # Check individual longest queries
    queries_sorted = sorted(queries, key=lambda x: x[1], reverse=True)
    print("\nTop 3 Longest Queries:")
    for q_text, q_ms in queries_sorted[:3]:
        print(f"  [{q_ms:5.1f} ms] {q_text[:110]}...")

    return {
        "course": cname,
        "queries_count": len(queries),
        "total_ms": t_total,
        "sql_ms": total_query_time,
        "query_templates": query_templates
    }

if __name__ == "__main__":
    profile_course("1") # Calculus
    profile_course("2") # Chemistry
    profile_course("14", cycle="CT1") # EEE
    profile_course("16") # OODP
    profile_course("8", language="german") # German
