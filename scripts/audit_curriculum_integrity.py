import sqlite3
import os
from sqlalchemy import create_engine, text

def audit_sqlite(db_path="production_corpus.db"):
    print("=" * 80)
    print(f"AUDITING LOCAL SQLITE: {db_path}")
    print("=" * 80)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    total = cur.execute("SELECT count(*) FROM curriculum_mappings").fetchone()[0]
    distinct_triplets = cur.execute("""
        SELECT count(*) FROM (
            SELECT DISTINCT branch_name, semester, curriculum_id FROM curriculum_mappings
        )
    """).fetchone()[0]
    
    print(f"Total rows: {total}")
    print(f"Distinct (branch_name, semester, curriculum_id): {distinct_triplets}")
    
    dups = cur.execute("""
        SELECT branch_name, semester, curriculum_id, count(*)
        FROM curriculum_mappings
        GROUP BY branch_name, semester, curriculum_id
        HAVING count(*) > 1
    """).fetchall()
    print(f"Duplicate (branch_name, semester, curriculum_id) triplets: {len(dups)}")
    if dups:
        for d in dups[:5]:
            print(f"  Duplicate: {d}")
            
    # Check status
    statuses = cur.execute("SELECT status, count(*) FROM curriculum_mappings GROUP BY status").fetchall()
    print(f"Status distribution: {statuses}")
    
    # Check course_id distribution
    courses = cur.execute("SELECT course_id, count(*) FROM curriculum_mappings WHERE status = 'MATCHED' GROUP BY course_id ORDER BY course_id").fetchall()
    print(f"Matched courses: {courses}")
    
    # Check for anomalies: e.g. course_id assigned but status != 'MATCHED' or vice-versa
    anom1 = cur.execute("SELECT count(*) FROM curriculum_mappings WHERE status = 'MATCHED' AND course_id IS NULL").fetchone()[0]
    anom2 = cur.execute("SELECT count(*) FROM curriculum_mappings WHERE status != 'MATCHED' AND course_id IS NOT NULL").fetchone()[0]
    print(f"Anomalies (MATCHED but course_id NULL): {anom1}")
    print(f"Anomalies (NOT MATCHED but course_id NOT NULL): {anom2}")
    
    # Check curriculum_id collisions across branches
    curr_id_collisions = cur.execute("""
        SELECT curriculum_id, count(DISTINCT branch_name), count(DISTINCT subject_name), count(DISTINCT course_id)
        FROM curriculum_mappings
        GROUP BY curriculum_id
        HAVING count(DISTINCT branch_name) > 1
        ORDER BY count(DISTINCT course_id) DESC, count(DISTINCT subject_name) DESC
    """).fetchall()
    print(f"curriculum_ids shared across multiple branches: {len(curr_id_collisions)}")
    multi_course_collisions = [c for c in curr_id_collisions if c[3] > 1]
    print(f"curriculum_ids mapping to multiple DIFFERENT course_ids: {len(multi_course_collisions)}")
    for c in multi_course_collisions[:5]:
        print(f"  curriculum_id '{c[0]}' spans {c[1]} branches, {c[2]} subject names, {c[3]} different course_ids")
        
    conn.close()
    return total, distinct_triplets, len(dups)

def audit_postgres(pg_url):
    print("\n" + "=" * 80)
    print("AUDITING REMOTE POSTGRESQL")
    print("=" * 80)
    clean_url = pg_url.replace("postgresql://", "postgresql+psycopg2://")
    engine = create_engine(clean_url)
    with engine.connect() as conn:
        total = conn.execute(text("SELECT count(*) FROM curriculum_mappings")).fetchone()[0]
        distinct_triplets = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT DISTINCT branch_name, semester, curriculum_id FROM curriculum_mappings
            ) t
        """)).fetchone()[0]
        print(f"Total rows: {total}")
        print(f"Distinct (branch_name, semester, curriculum_id): {distinct_triplets}")
        
        dups = conn.execute(text("""
            SELECT branch_name, semester, curriculum_id, count(*)
            FROM curriculum_mappings
            GROUP BY branch_name, semester, curriculum_id
            HAVING count(*) > 1
        """)).fetchall()
        print(f"Duplicate triplets: {len(dups)}")
        
        statuses = conn.execute(text("SELECT status, count(*) FROM curriculum_mappings GROUP BY status")).fetchall()
        print(f"Status distribution: {statuses}")
        
        courses = conn.execute(text("SELECT course_id, count(*) FROM curriculum_mappings WHERE status = 'MATCHED' GROUP BY course_id ORDER BY course_id")).fetchall()
        print(f"Matched courses: {courses}")
        
        anom1 = conn.execute(text("SELECT count(*) FROM curriculum_mappings WHERE status = 'MATCHED' AND course_id IS NULL")).fetchone()[0]
        anom2 = conn.execute(text("SELECT count(*) FROM curriculum_mappings WHERE status != 'MATCHED' AND course_id IS NOT NULL")).fetchone()[0]
        print(f"Anomalies (MATCHED but course_id NULL): {anom1}")
        print(f"Anomalies (NOT MATCHED but course_id NOT NULL): {anom2}")

if __name__ == "__main__":
    audit_sqlite()
    pg_url = os.environ.get("RENDER_DATABASE_URL")
    if not pg_url:
        pg_url = "postgresql://markmint_user:RDXfizQBWXFjhEUbfshlumjwuQajSUFR@dpg-dakpv1gu01pc73bj47e0-a.oregon-postgres.render.com/markmint?sslmode=require"
    audit_postgres(pg_url)
