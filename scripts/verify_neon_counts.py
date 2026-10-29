import os
import psycopg2
import dotenv

dotenv.load_dotenv('.env')
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

tables = [
    'courses',
    'course_tracks',
    'syllabuses',
    'units',
    'topics',
    'documents',
    'exams',
    'sections',
    'questions',
    'question_families',
    'question_family_memberships',
    'curriculum_mappings'
]

print("=== Neon PostgreSQL Corpus Verification ===")
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{t}";')
        count = cur.fetchone()[0]
        print(f"[OK] {t}: {count}")
    except Exception as e:
        print(f"[ERROR] {t}: {e}")
        conn.rollback()

cur.close()
conn.close()
