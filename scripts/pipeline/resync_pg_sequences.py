"""
Transaction-safe PostgreSQL Sequence Resynchronization Tool for MarkMint.
Finds all sequence-backed tables in the public schema and synchronizes their
sequences to COALESCE(MAX(id), 1), preventing primary-key collision errors.
"""

import os
import sys
import argparse
import urllib.parse
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def mask_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        return url
    except Exception:
        return "<DATABASE_URL masked>"

def normalize_target_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url and "?" in url:
        url = f"{url}&sslmode=require"
    elif "sslmode=" not in url and not url.startswith("sqlite"):
        url = f"{url}?sslmode=require"
    return url

def resync_sequences(db_url: str):
    print(f"Connecting to database: {mask_url(db_url)}")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        tables_with_id = conn.execute(text("""
            SELECT c.table_name 
            FROM information_schema.columns c
            JOIN information_schema.tables t ON c.table_name = t.table_name AND c.table_schema = t.table_schema
            WHERE c.table_schema = 'public' 
              AND t.table_type = 'BASE TABLE' 
              AND c.column_name = 'id'
            ORDER BY c.table_name
        """)).fetchall()

        print("\n" + "=" * 65)
        print(f"  {'TABLE':<30} {'SEQUENCE':<24} {'MAX_ID'}")
        print("=" * 65)

        resynced = 0
        for (tbl,) in tables_with_id:
            seq = conn.execute(text(f"SELECT pg_get_serial_sequence('{tbl}', 'id')")).scalar()
            if seq:
                max_id = conn.execute(text(f'SELECT COALESCE(MAX(id), 1) FROM "{tbl}"')).scalar()
                conn.execute(text(f"SELECT setval('{seq}', {max_id})"))
                print(f"  {tbl:<30} {seq:<24} {max_id}")
                resynced += 1
            else:
                print(f"  {tbl:<30} (no sequence owned)")

        conn.commit()
        print("=" * 65)
        print(f"[OK] Successfully resynchronized {resynced} PostgreSQL sequences.\n")

def main():
    parser = argparse.ArgumentParser(description="Resynchronize PostgreSQL Sequences")
    parser.add_argument("--db-url", type=str, default=None)
    parser.add_argument("--use-env", action="store_true")
    args = parser.parse_args()

    if args.use_env:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        env_url = os.environ.get("DATABASE_URL")
        if not env_url:
            raise ValueError("DATABASE_URL not found in environment or .env")
        db_url = normalize_target_url(env_url)
    elif args.db_url:
        db_url = normalize_target_url(args.db_url)
    else:
        raise ValueError("Either --use-env or --db-url must be provided.")

    resync_sequences(db_url)

if __name__ == "__main__":
    main()
