"""
Safe, Staged, Idempotent Backfill for Historical Question Types.

Updates Question.question_type in production_corpus.db in two controlled stages:
  - Stage 1: High-confidence deterministic predictions only (>= 0.85 conf).
  - Stage 2: Remaining sufficiently reliable predictions (medium conf) + explicit 'Other / Unclassified' fallback.

Invariants strictly preserved:
  - Idempotent: WHERE question_type IS NULL (never overwrites curated or existing values).
  - Never modifies question text, marks, family_id, topic mappings, or exam headers.
"""

import sys
import os
import argparse
import sqlite3
from collections import Counter
from typing import Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.services.question_type_classifier import (
    DeterministicQuestionTypeClassifier,
    QuestionType,
    ClassificationConfidence,
)

DB_PATH = "production_corpus.db"


def compute_safety_checksums(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Computes safety checksums to ensure zero unintended mutations."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*),
            TOTAL(COALESCE(marks, 0.0)),
            TOTAL(LENGTH(COALESCE(original_text, ''))),
            COUNT(family_id),
            COUNT(DISTINCT section_id)
        FROM questions
    """)
    row = cursor.fetchone()
    return {
        "count": row[0],
        "total_marks": round(row[1], 4),
        "total_text_len": row[2],
        "count_with_family": row[3],
        "distinct_sections": row[4]
    }


def execute_backfill(
    stage: int,
    dry_run: bool = False,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    Executes staged question_type backfill.
    """
    if stage not in (1, 2):
        raise ValueError(f"Invalid stage {stage}. Must be 1 or 2.")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    before_checksums = compute_safety_checksums(conn)

    # Fetch all questions where question_type IS NULL (or check total)
    cursor.execute("""
        SELECT 
            q.id,
            q.original_text,
            q.marks,
            q.question_type,
            s.name AS section_name
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        ORDER BY q.id ASC
    """)
    all_rows = cursor.fetchall()
    total_questions = len(all_rows)

    updates = []
    skipped_already_classified = 0
    stage_category_counts = Counter()
    unclassified_count = 0

    for row in all_rows:
        q_id = row["id"]
        existing_type = row["question_type"]

        if existing_type is not None:
            skipped_already_classified += 1
            continue

        text = row["original_text"] or ""
        marks = row["marks"]
        sec_name = row["section_name"] or ""

        proposal = DeterministicQuestionTypeClassifier.classify(
            text=text,
            marks=marks,
            section_name=sec_name
        )

        p_type = proposal.question_type.value
        conf = proposal.confidence.value

        should_update = False
        target_value = None

        if stage == 1:
            # Stage 1: High-confidence non-unclassified only
            if conf == "high" and proposal.question_type != QuestionType.UNCLASSIFIED:
                should_update = True
                target_value = p_type
        elif stage == 2:
            # Stage 2: Medium confidence OR explicit Unclassified fallback
            if conf == "medium" and proposal.question_type != QuestionType.UNCLASSIFIED:
                should_update = True
                target_value = p_type
            elif conf == "low" or proposal.question_type == QuestionType.UNCLASSIFIED:
                should_update = True
                target_value = QuestionType.UNCLASSIFIED.value
                unclassified_count += 1

        if should_update:
            updates.append((target_value, q_id))
            stage_category_counts[target_value] += 1

    if not dry_run and updates:
        cursor.executemany(
            "UPDATE questions SET question_type = ? WHERE id = ? AND question_type IS NULL",
            updates
        )
        conn.commit()

    after_checksums = compute_safety_checksums(conn)

    # Verify database safety invariants
    assert before_checksums["count"] == after_checksums["count"], "Invariant violated: Question count changed!"
    assert before_checksums["total_marks"] == after_checksums["total_marks"], "Invariant violated: Marks modified!"
    assert before_checksums["total_text_len"] == after_checksums["total_text_len"], "Invariant violated: Question text modified!"
    assert before_checksums["count_with_family"] == after_checksums["count_with_family"], "Invariant violated: Families modified!"
    assert before_checksums["distinct_sections"] == after_checksums["distinct_sections"], "Invariant violated: Sections modified!"

    # Get current DB status
    cursor.execute("SELECT COUNT(question_type) FROM questions WHERE question_type IS NOT NULL")
    now_classified = cursor.fetchone()[0]

    conn.close()

    summary = {
        "stage": stage,
        "dry_run": dry_run,
        "total_questions": total_questions,
        "updated_count": len(updates),
        "skipped_already_classified": skipped_already_classified,
        "unclassified_count": unclassified_count,
        "category_counts": dict(stage_category_counts),
        "total_classified_now": now_classified,
        "total_null_now": total_questions - now_classified,
        "invariants_verified": True
    }

    return summary


def main():
    parser = argparse.ArgumentParser(description="Backfill Question Types into Corpus DB")
    parser.add_argument("--stage", type=int, choices=[1, 2], required=True, help="Stage 1 (High conf) or Stage 2 (Remaining + Unclassified)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing to DB")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Path to database")

    args = parser.parse_args()

    print(f"Executing Stage {args.stage} Backfill (dry_run={args.dry_run}) on {args.db}...")
    summary = execute_backfill(stage=args.stage, dry_run=args.dry_run, db_path=args.db)

    print("\n" + "="*60)
    print(f"BACKFILL SUMMARY (STAGE {summary['stage']})")
    print("="*60)
    print(f"Dry Run: {summary['dry_run']}")
    print(f"Total Questions: {summary['total_questions']}")
    print(f"Updated in this run: {summary['updated_count']}")
    print(f"Skipped (already classified): {summary['skipped_already_classified']}")
    print(f"Explicitly set to Unclassified: {summary['unclassified_count']}")
    print(f"Total classified in DB now: {summary['total_classified_now']}")
    print(f"Total NULL in DB now: {summary['total_null_now']}")
    print(f"Safety Invariants Verified: {summary['invariants_verified']}")
    print("\nCategories Updated:")
    for cat, count in summary["category_counts"].items():
        print(f"  {cat:<35}: {count}")


if __name__ == "__main__":
    main()
