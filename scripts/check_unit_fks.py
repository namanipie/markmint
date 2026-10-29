import sqlite3

conn = sqlite3.connect("production_corpus.db")
c = conn.cursor()
bad_unit_ids = [15, 19, 25, 26, 27, 28, 29, 30, 31, 32, 33]

for t in ["concepts", "syllabus_concept", "assessment_coverages", "topics"]:
    rows = c.execute(f"SELECT * FROM {t} WHERE unit_id IN ({','.join(str(i) for i in bad_unit_ids)})").fetchall()
    print(f"Table {t}: {len(rows)} rows pointing to bad units")
    if rows:
        cols = [col[1] for col in c.execute(f"PRAGMA table_info('{t}')").fetchall()]
        print("  Cols:", cols)
        for r in rows[:3]:
            print("  Sample:", r)

conn.close()
