"""
Promote Course 8 (Foreign Languages) Track Taxonomy to Render PostgreSQL.

Architecture:
- Parent Course 8 shell has 0 units (acts purely as track container).
- Tracks 1..6 (German, French, Spanish, Japanese, Korean, Chinese) each have exactly 5 units (1..5).
- Delete dummy assessment_coverages for unit 8.
- Delete dummy unit 8 ("General Unit") from PostgreSQL.
- Insert syllabuses 25..30, units 126..155, topics 550..736 from local SQLite.
- Synchronize PostgreSQL sequences.
"""
import sqlite3
import psycopg2

PG_URL = "postgresql://markmint_user:RDXfizQBWXFjhEUbfshlumjwuQajSUFR@dpg-dakpv1gu01pc73bj47e0-a.oregon-postgres.render.com/markmint?sslmode=require"

def main():
    conn_sqlite = sqlite3.connect("production_corpus.db")
    cur_sqlite = conn_sqlite.cursor()

    conn_pg = psycopg2.connect(PG_URL)
    cur_pg = conn_pg.cursor()

    try:
        # 1. Fetch syllabuses 25..30 from SQLite
        cur_sqlite.execute("SELECT id, course_id, track_id, version FROM syllabuses WHERE id >= 25 AND id <= 30;")
        sylls = cur_sqlite.fetchall()

        # 2. Fetch units 126..155 from SQLite
        cur_sqlite.execute("SELECT id, syllabus_id, number, name FROM units WHERE id >= 126 AND id <= 155;")
        units = cur_sqlite.fetchall()

        # 3. Fetch topics 550..736 from SQLite
        cur_sqlite.execute("SELECT id, unit_id, name FROM topics WHERE id >= 550 AND id <= 736;")
        topics = cur_sqlite.fetchall()

        print(f"Ready to promote: {len(sylls)} syllabuses, {len(units)} units, {len(topics)} topics.", flush=True)

        # Delete assessment_coverages referencing dummy unit 8
        cur_pg.execute("DELETE FROM assessment_coverages WHERE unit_id = 8;")
        print(f"Deleted assessment_coverages for unit 8: {cur_pg.rowcount} row(s)", flush=True)

        # Delete dummy unit 8 if present
        cur_pg.execute("DELETE FROM units WHERE id = 8 AND syllabus_id = 8;")
        print(f"Deleted dummy unit 8: {cur_pg.rowcount} row(s)", flush=True)

        # Insert syllabuses
        for s in sylls:
            cur_pg.execute("INSERT INTO syllabuses (id, course_id, track_id, version) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;", s)
        print(f"Inserted/verified {len(sylls)} track syllabuses.", flush=True)

        # Insert units
        for u in units:
            cur_pg.execute("INSERT INTO units (id, syllabus_id, number, name) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;", u)
        print(f"Inserted/verified {len(units)} units.", flush=True)

        # Insert topics
        for t in topics:
            cur_pg.execute("INSERT INTO topics (id, unit_id, name) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING;", t)
        print(f"Inserted/verified {len(topics)} topics.", flush=True)

        # Sync sequences
        cur_pg.execute("SELECT setval('syllabuses_id_seq', (SELECT MAX(id) FROM syllabuses));")
        cur_pg.execute("SELECT setval('units_id_seq', (SELECT MAX(id) FROM units));")
        cur_pg.execute("SELECT setval('topics_id_seq', (SELECT MAX(id) FROM topics));")

        conn_pg.commit()
        print("Successfully committed Course 8 tracks to Render PostgreSQL!", flush=True)

    except Exception as e:
        conn_pg.rollback()
        print(f"ERROR: {e}", flush=True)
        raise
    finally:
        conn_pg.close()
        conn_sqlite.close()

if __name__ == "__main__":
    main()
