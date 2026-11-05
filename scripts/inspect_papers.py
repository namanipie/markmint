import sqlite3
import os

db_paths = ['backend/demo.db', 'backend/exam_archive.db', 'backend/data/production_corpus.db']

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"=== {db_path} ===")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Tables: {tables}")
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM \"{t}\"")
                count = cursor.fetchone()[0]
                print(f"  {t}: {count} rows")
            except Exception as e:
                print(f"  {t}: error {e}")
        conn.close()
