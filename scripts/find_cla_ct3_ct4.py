import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import engine
from sqlalchemy import text

print("=== CHECKING ALL CT3, CT4, CLA, FT, AND INTERNAL PAPERS IN DATABASE ===")

sql = text("""
    SELECT 
        e.id,
        c.code,
        c.name,
        e.assessment_type,
        d.title,
        d.source,
        COUNT(q.id) as q_count
    FROM exams e
    JOIN courses c ON e.course_id = c.id
    LEFT JOIN documents d ON e.document_id = d.id
    LEFT JOIN sections s ON s.exam_id = e.id
    LEFT JOIN questions q ON q.section_id = s.id
    WHERE 
        UPPER(e.assessment_type) LIKE '%CT3%' OR
        UPPER(e.assessment_type) LIKE '%CT-3%' OR
        UPPER(e.assessment_type) LIKE '%CT4%' OR
        UPPER(e.assessment_type) LIKE '%CT-4%' OR
        UPPER(e.assessment_type) LIKE '%CLA%' OR
        UPPER(e.assessment_type) LIKE '%FT%' OR
        UPPER(e.assessment_type) LIKE '%INTERNAL%' OR
        UPPER(e.assessment_type) LIKE '%FJ%' OR
        UPPER(d.title) LIKE '%CT3%' OR
        UPPER(d.title) LIKE '%CT4%' OR
        UPPER(d.title) LIKE '%CLA%' OR
        UPPER(d.title) LIKE '%FT%' OR
        UPPER(d.title) LIKE '%INTERNAL%'
    GROUP BY e.id, c.code, c.name, e.assessment_type, d.title, d.source
    ORDER BY c.code, e.id
""")

with engine.connect() as conn:
    rows = conn.execute(sql).fetchall()
    print(f"Total matching exams: {len(rows)}\n")
    for r in rows:
        print(f"ID: {r[0]:3d} | Course: {r[1]:10s} ({r[2][:25]:25s}) | Type: {str(r[3]):25s} | Qs: {r[6]:2d} | Title: {str(r[4])[:40]}")
