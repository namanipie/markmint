"""
Database Backfill Migration: Clean Question Numbers from Question Text

Strips leading question numbers (e.g., '1.', '2)', 'Q1.', '21(a)', '(a)')
from `original_text`, `normalized_text`, and `classification_input` in Neon PostgreSQL.

Uses high-speed psycopg2 `execute_values` to batch updates into single multi-row SQL statements.

Usage:
    # Dry run (inspection only, zero DB writes):
    python scripts/db/clean_question_numbers.py --dry-run

    # Apply changes with ultra-fast bulk execution:
    python scripts/db/clean_question_numbers.py --apply
"""

import sys
import os
import re
import time
import argparse
from typing import Optional
from psycopg2.extras import execute_values

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv("backend/.env")

from backend.core.database import SessionLocal
from backend.models.core import Question
from backend.services.extraction.cleaner import strip_question_prefix


def clean_normalized_text(norm_text: Optional[str]) -> Optional[str]:
    """Cleans normalized text by stripping leading numeric tokens."""
    if not norm_text:
        return norm_text
    cleaned = re.sub(r'^\s*\d{1,3}[a-z]?\s+', '', norm_text, flags=re.IGNORECASE)
    return cleaned.strip() if cleaned.strip() else norm_text


def run_migration(apply_changes: bool = False, batch_size: int = 1000):
    db = SessionLocal()
    print("=" * 65, flush=True)
    print("  QUESTION NUMBER SANITIZATION MIGRATION (EXECUTE_VALUES)", flush=True)
    print(f"  Mode: {'APPLY (COMMITTING TO DB)' if apply_changes else 'DRY RUN (NO DB WRITES)'}", flush=True)
    print("=" * 65, flush=True)

    try:
        t0 = time.time()
        print("Querying question records from Neon PostgreSQL...", flush=True)
        rows = (
            db.query(
                Question.id,
                Question.question_number,
                Question.original_text,
                Question.normalized_text,
                Question.classification_input
            )
            .filter(Question.original_text.isnot(None))
            .order_by(Question.id)
            .all()
        )
        print(f"Loaded {len(rows)} question records in {time.time() - t0:.2f}s.", flush=True)

        update_tuples = []
        samples = []

        for q_id, q_num, orig, norm, clas in rows:
            orig_str = orig or ""
            cleaned = strip_question_prefix(orig_str, str(q_num or ""))

            if cleaned != orig_str:
                new_norm = clean_normalized_text(norm) if norm else None
                new_clas = strip_question_prefix(clas, str(q_num or "")) if clas else None
                update_tuples.append((q_id, cleaned, new_norm, new_clas))

                if len(samples) < 15:
                    samples.append({
                        "id": q_id,
                        "q_num": q_num,
                        "before": orig_str[:60].replace("\n", " "),
                        "after": cleaned[:60].replace("\n", " "),
                    })

        print("-" * 65, flush=True)
        print("MIGRATION SUMMARY:", flush=True)
        print(f"  Total records evaluated: {len(rows)}", flush=True)
        print(f"  Total records to update: {len(update_tuples)} ({len(update_tuples) / len(rows) * 100:.1f}%)", flush=True)
        print("-" * 65, flush=True)

        print("\nSample Transformations (First 15):", flush=True)
        for s in samples:
            print(f"  [ID {s['id']} | Q#{s['q_num']}]", flush=True)
            print(f"    BEFORE: {repr(s['before'])}", flush=True)
            print(f"    AFTER:  {repr(s['after'])}", flush=True)

        if apply_changes and update_tuples:
            t_update = time.time()
            print(f"\nExecuting ultra-fast bulk updates in batches of {batch_size}...", flush=True)
            conn = db.connection().connection
            cur = conn.cursor()

            sql = """
            UPDATE questions AS q
            SET original_text = v.orig,
                normalized_text = COALESCE(v.norm, q.normalized_text),
                classification_input = COALESCE(v.clas, q.classification_input)
            FROM (VALUES %s) AS v(id, orig, norm, clas)
            WHERE q.id = v.id;
            """

            total_batches = (len(update_tuples) + batch_size - 1) // batch_size
            for i in range(0, len(update_tuples), batch_size):
                batch = update_tuples[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                execute_values(cur, sql, batch, template="(%s, %s, %s, %s)")
                conn.commit()
                print(f"  [Batch {batch_num}/{total_batches}] Committed {len(batch)} rows (Total: {min(i + batch_size, len(update_tuples))}/{len(update_tuples)})", flush=True)

            cur.close()
            print(f"\n[SUCCESS] Successfully migrated {len(update_tuples)} records on Neon PostgreSQL in {time.time() - t_update:.2f}s!", flush=True)
        elif not apply_changes:
            print("\n  [INFO] Dry run complete. Zero modifications written to database.", flush=True)
            print("  To execute real migration, run with: python scripts/db/clean_question_numbers.py --apply", flush=True)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration failed and rolled back: {e}", flush=True)
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean question numbers from question text in Neon PostgreSQL")
    parser.add_argument("--apply", action="store_true", help="Apply updates to database (defaults to dry-run)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Transaction batch size")
    args = parser.parse_args()

    run_migration(apply_changes=args.apply, batch_size=args.batch_size)
