import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import dotenv

dotenv.load_dotenv('.env')

pg_url = os.environ.get('DATABASE_URL')
if not pg_url:
    print("Error: DATABASE_URL not found in .env")
    sys.exit(1)

print("Connecting to Neon PostgreSQL...")
pg_conn = psycopg2.connect(pg_url)
pg_cur = pg_conn.cursor()

sl_conn = sqlite3.connect('production_corpus.db')
sl_cur = sl_conn.cursor()

TABLES_IN_ORDER = [
    "courses",
    "course_tracks",
    "syllabuses",
    "units",
    "topics",
    "subtopics",
    "concepts",
    "concept_aliases",
    "concept_relationship",
    "syllabus_concept",
    "documents",
    "document_provenances",
    "exams",
    "course_assessment_plans",
    "assessment_components",
    "sections",
    "question_families",
    "questions",
    "question_topic",
    "question_concept",
    "question_family_memberships",
    "study_evidences",
    "evidences",
    "assessment_coverages",
    "intelligence_snapshots",
    "failed_search_logs",
    "paper_submissions",
]

# Truncate tables in reverse order to respect foreign keys
for table in reversed(TABLES_IN_ORDER):
    try:
        pg_cur.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
        pg_conn.commit()
    except Exception:
        pg_conn.rollback()

for table in TABLES_IN_ORDER:
    # Check if table exists in SQLite
    sl_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
    if not sl_cur.fetchone():
        print(f"Skipping {table} (not in SQLite)")
        continue

    # Get column names
    sl_cur.execute(f"PRAGMA table_info({table});")
    cols = [col[1] for col in sl_cur.fetchall()]
    
    # Fetch all rows from SQLite
    cols_joined = ", ".join([f'"{c}"' for c in cols])
    sl_cur.execute(f"SELECT {cols_joined} FROM {table};")
    rows = sl_cur.fetchall()
    
    # Fetch PG column types
    pg_cur.execute("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s;
    """, (table,))
    pg_col_meta = {r[0]: (r[1], r[2]) for r in pg_cur.fetchall()}

    # Clean rows for type/enum mismatches
    cleaned_rows = []
    for r in rows:
        row_list = list(r)
        for idx, col in enumerate(cols):
            val = row_list[idx]
            dt, udt = pg_col_meta.get(col, (None, None))
            
            if dt == "boolean":
                if val is not None:
                    row_list[idx] = bool(val)
            elif dt in ("json", "jsonb"):
                if val is not None and isinstance(val, str) and val.strip().lower() in ("null", "", "none"):
                    row_list[idx] = None
            elif udt == "conceptstatus":
                if val == "active":
                    row_list[idx] = "CANONICAL"
        cleaned_rows.append(tuple(row_list))
    rows = cleaned_rows

    # Prepare INSERT
    placeholders = ", ".join(["%s"] * len(cols))
    insert_sql = f'INSERT INTO "{table}" ({cols_joined}) VALUES ({placeholders})'
    
    print(f"Migrating {len(rows)} rows into {table}...", flush=True)
    execute_batch(pg_cur, insert_sql, rows, page_size=1000)
    pg_conn.commit()
    print(f"[OK] Table {table}: {len(rows)} rows migrated.", flush=True)

# Reset sequences in Postgres for all serial primary keys
print("Updating Postgres sequences...")
pg_cur.execute("""
SELECT 'SELECT SETVAL(' ||
       quote_literal(quote_ident(PGT.schemaname) || '.' || quote_ident(s.relname)) ||
       ', COALESCE(MAX(' ||quote_ident(C.attname)|| '), 1) ) FROM ' ||
       quote_ident(PGT.schemaname)|| '.'||quote_ident(T.relname)|| ';'
FROM pg_class AS S,
     pg_depend AS D,
     pg_class AS T,
     pg_attribute AS C,
     pg_tables AS PGT
WHERE S.relkind = 'S'
  AND S.oid = D.objid
  AND D.refobjid = T.oid
  AND D.refobjsubid = C.attnum
  AND T.relname = PGT.tablename
  AND PGT.schemaname = 'public';
""")
seq_stmts = pg_cur.fetchall()
for stmt in seq_stmts:
    try:
        pg_cur.execute(stmt[0])
    except Exception as e:
        pass
pg_conn.commit()

print("Verifying migration counts in Neon:")
for table in TABLES_IN_ORDER:
    try:
        pg_cur.execute(f'SELECT COUNT(*) FROM "{table}";')
        count = pg_cur.fetchone()[0]
        print(f" - {table}: {count} rows")
    except Exception:
        pass

pg_cur.close()
pg_conn.close()
sl_cur.close()
sl_conn.close()
print("All data migrated to Neon successfully!")
