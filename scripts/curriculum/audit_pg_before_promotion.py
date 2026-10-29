"""
Pre-promotion audit of production PostgreSQL for Courses 3-12.
Compares production vs local SQLite for:
- Syllabuses
- Units
- Topics
- Concepts
- question_topic mappings
"""
import os
import sys
import sqlite3
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
import re

def get_pg_url():
    if os.environ.get("RENDER_DATABASE_URL"):
        return os.environ["RENDER_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg2://")
    smoke_file = os.path.join(BASE_DIR, "scripts", "verify_production_smoke.py")
    with open(smoke_file, "r") as f:
        match = re.search(r'postgresql://[^\"]+', f.read())
        if match:
            return match.group(0).replace("postgresql://", "postgresql+psycopg2://")
    raise ValueError("Could not resolve PG_URL")

PG_URL = get_pg_url()

def audit_pg():
    # SQLite connection
    sqlite_conn = sqlite3.connect("production_corpus.db")
    sc = sqlite_conn.cursor()

    # PostgreSQL connection
    engine = create_engine(PG_URL)

    print("=" * 80)
    print("PRE-PROMOTION PRODUCTION VS LOCAL COMPARISON (COURSES 1-13)")
    print("=" * 80)

    with engine.connect() as pg_conn:
        print(f"{'CID':<3} | {'Course Name':<32} | {'Loc U/T':<8} | {'Prod U/T':<9} | {'Loc Map':<8} | {'Prod Map':<9} | {'New Map':<8}")
        print("-" * 90)

        total_loc_mappings = 0
        total_prod_mappings = 0
        total_new_mappings = 0

        for cid in range(1, 14):
            # Local stats
            sc.execute("SELECT name FROM courses WHERE id = ?", (cid,))
            c_row = sc.fetchone()
            c_name = c_row[0] if c_row else "Unknown"

            sc.execute("SELECT count(*) FROM units u JOIN syllabuses s ON u.syllabus_id = s.id WHERE s.course_id = ?", (cid,))
            loc_u = sc.fetchone()[0]
            sc.execute("SELECT count(*) FROM topics t JOIN units u ON t.unit_id = u.id JOIN syllabuses s ON u.syllabus_id = s.id WHERE s.course_id = ?", (cid,))
            loc_t = sc.fetchone()[0]
            sc.execute("""
                SELECT count(DISTINCT q.id) 
                FROM questions q 
                JOIN sections sec ON q.section_id = sec.id 
                JOIN exams e ON sec.exam_id = e.id 
                JOIN question_topic qt ON q.id = qt.question_id 
                WHERE e.course_id = ?
            """, (cid,))
            loc_map = sc.fetchone()[0]

            # Prod stats
            prod_u = pg_conn.execute(text("SELECT count(*) FROM units u JOIN syllabuses s ON u.syllabus_id = s.id WHERE s.course_id = :cid"), {"cid": cid}).scalar()
            prod_t = pg_conn.execute(text("SELECT count(*) FROM topics t JOIN units u ON t.unit_id = u.id JOIN syllabuses s ON u.syllabus_id = s.id WHERE s.course_id = :cid"), {"cid": cid}).scalar()
            prod_map = pg_conn.execute(text("""
                SELECT count(DISTINCT q.id) 
                FROM questions q 
                JOIN sections sec ON q.section_id = sec.id 
                JOIN exams e ON sec.exam_id = e.id 
                JOIN question_topic qt ON q.id = qt.question_id 
                WHERE e.course_id = :cid
            """), {"cid": cid}).scalar()

            new_map = loc_map - prod_map
            total_loc_mappings += loc_map
            total_prod_mappings += prod_map
            total_new_mappings += new_map

            print(f"{cid:<3} | {c_name[:32]:<32} | {loc_u}/{loc_t:<5} | {prod_u}/{prod_t:<6} | {loc_map:<8} | {prod_map:<9} | {new_map:<8}")

        print("-" * 90)
        print(f"TOTALS: Local Mappings={total_loc_mappings}, Prod Mappings={total_prod_mappings}, New to Promote={total_new_mappings}")

        # Check existing student progress in Prod
        stp = pg_conn.execute(text("SELECT count(*) FROM student_topic_progress")).scalar()
        srp = pg_conn.execute(text("SELECT count(*) FROM student_resource_progress")).scalar()
        curr = pg_conn.execute(text("SELECT count(*) FROM curriculum_mappings")).scalar()
        print("\nPRODUCTION INVARIANTS (CURRENT):")
        print(f"  student_topic_progress   : {stp}")
        print(f"  student_resource_progress: {srp}")
        print(f"  curriculum_mappings      : {curr}")

    sqlite_conn.close()

if __name__ == "__main__":
    audit_pg()
