"""
Safe Staged Migration Script for Exam Chronology Metadata Backfill.

Migrates the 45 explicitly verified exams in production_corpus.db.
Guaranteed:
- Idempotent and transactional.
- Strict NULL-only updates for year.
- Preserves all question text, marks, question types, families, units, topics, and courses.
- Immediate rollback on any assertion failure.
- Full verification of database invariants before and after.
"""

import hashlib
import os
import sqlite3
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.abspath("."))
from backend.services.exam_chronology_resolver import ExamChronologyResolver, ResolutionCategory
from scripts.audit_resolver_dry_run import run_dry_run


def compute_invariants(conn: sqlite3.Connection) -> Dict[str, any]:
    c = conn.cursor()
    c.execute("SELECT count(*) FROM exams")
    total_exams = c.fetchone()[0]

    c.execute("SELECT count(*) FROM exams WHERE year IS NOT NULL")
    exams_with_year = c.fetchone()[0]

    c.execute("SELECT count(*) FROM exams WHERE year IS NULL")
    exams_without_year = c.fetchone()[0]

    c.execute("SELECT count(*) FROM sections")
    total_sections = c.fetchone()[0]

    c.execute("SELECT count(*) FROM questions")
    total_questions = c.fetchone()[0]

    c.execute("SELECT sum(marks) FROM questions")
    sum_marks = round(c.fetchone()[0], 4)

    c.execute("SELECT count(*) FROM courses")
    total_courses = c.fetchone()[0]

    c.execute("SELECT count(*) FROM question_families")
    total_families = c.fetchone()[0]

    c.execute("SELECT question_type, count(*) FROM questions GROUP BY question_type ORDER BY question_type")
    qtype_counts = c.fetchall()

    # Questions integrity hash
    c.execute("SELECT id, section_id, family_id, question_number, marks, question_type, original_text FROM questions ORDER BY id")
    q_rows = c.fetchall()
    hasher = hashlib.sha256()
    for r in q_rows:
        hasher.update(f"{r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}".encode("utf-8"))
    q_hash = hasher.hexdigest()

    return {
        "total_exams": total_exams,
        "exams_with_year": exams_with_year,
        "exams_without_year": exams_without_year,
        "total_sections": total_sections,
        "total_questions": total_questions,
        "sum_marks": sum_marks,
        "total_courses": total_courses,
        "total_families": total_families,
        "qtype_counts": qtype_counts,
        "q_hash": q_hash,
    }


def migrate():
    # 1. Verify backup exists
    backup_path = "production_corpus.db.pre_exam_metadata_backfill_backup"
    if not os.path.exists(backup_path):
        raise RuntimeError(f"Safety check failed: backup file '{backup_path}' does not exist!")

    # 2. Compute dry run to get approved updates
    dry_run_summary = run_dry_run()
    approved_candidates = [
        r for r in dry_run_summary["proposed_resolutions"]
        if r["is_mutation_candidate"] and r["resolution_category"] == ResolutionCategory.RESOLVED_EXPLICIT.value
    ]

    print(f"Candidates approved for migration: {len(approved_candidates)}")
    if len(approved_candidates) != 45:
        raise RuntimeError(f"Expected exactly 45 approved candidates, got {len(approved_candidates)}")

    db_path = "production_corpus.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        # Pre-invariants
        pre_inv = compute_invariants(conn)
        print("Pre-migration invariants:")
        print(f"  Exams: {pre_inv['total_exams']} (with year: {pre_inv['exams_with_year']}, without year: {pre_inv['exams_without_year']})")
        print(f"  Questions: {pre_inv['total_questions']} (Marks sum: {pre_inv['sum_marks']})")
        print(f"  Questions Hash: {pre_inv['q_hash']}")

        # Ensure no target exam already has a year
        target_ids = [cand["exam_id"] for cand in approved_candidates]
        placeholders = ",".join("?" * len(target_ids))
        c.execute(f"SELECT id, year FROM exams WHERE id IN ({placeholders}) AND year IS NOT NULL", target_ids)
        existing_yeared = c.fetchall()
        if existing_yeared:
            raise RuntimeError(f"Safety violation: target exams already have non-null year: {existing_yeared}")

        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        updated_exams = 0
        updated_docs = 0

        for cand in approved_candidates:
            eid = cand["exam_id"]
            prop_year = cand["proposed_year"]
            prop_atype = cand["proposed_assessment_type"]

            # Update exam: strictly when year IS NULL
            c.execute("""
                UPDATE exams
                SET year = ?,
                    assessment_type = COALESCE(?, assessment_type)
                WHERE id = ? AND year IS NULL
            """, (prop_year, prop_atype, eid))
            if c.rowcount != 1:
                raise RuntimeError(f"Failed to update exam {eid}: rowcount={c.rowcount}")
            updated_exams += c.rowcount

            # Update corresponding document year & exam_type if NULL
            c.execute("""
                UPDATE documents
                SET year = ?,
                    exam_type = COALESCE(?, exam_type)
                WHERE id = (SELECT document_id FROM exams WHERE id = ?)
                  AND year IS NULL
            """, (prop_year, prop_atype, eid))
            updated_docs += c.rowcount

        print(f"Updated {updated_exams} exams and {updated_docs} documents.")

        # Post-invariants before commit
        post_inv = compute_invariants(conn)

        # Assert non-negotiable invariants
        assert post_inv["total_exams"] == pre_inv["total_exams"], "Total exams count changed!"
        assert post_inv["total_questions"] == pre_inv["total_questions"], "Total questions count changed!"
        assert post_inv["sum_marks"] == pre_inv["sum_marks"], "Sum of marks changed!"
        assert post_inv["q_hash"] == pre_inv["q_hash"], "Questions table integrity hash changed!"
        assert post_inv["total_sections"] == pre_inv["total_sections"], "Sections count changed!"
        assert post_inv["total_courses"] == pre_inv["total_courses"], "Courses count changed!"
        assert post_inv["total_families"] == pre_inv["total_families"], "Question families count changed!"
        assert post_inv["qtype_counts"] == pre_inv["qtype_counts"], "Question type counts changed!"
        assert post_inv["exams_with_year"] == pre_inv["exams_with_year"] + 45, "Exams with year did not increase by 45!"
        assert post_inv["exams_without_year"] == pre_inv["exams_without_year"] - 45, "Exams without year did not decrease by 45!"

        # Commit
        conn.commit()
        print("Migration committed successfully!")

        print("\n=== POST-MIGRATION INVARIANTS ===")
        print(f"Total Exams: {post_inv['total_exams']}")
        print(f"Exams with Year: {post_inv['exams_with_year']} (was {pre_inv['exams_with_year']})")
        print(f"Exams without Year: {post_inv['exams_without_year']} (was {pre_inv['exams_without_year']})")
        print(f"Questions Integrity Hash (UNCHANGED): {post_inv['q_hash']}")

    except Exception as ex:
        conn.rollback()
        print(f"ERROR: Migration failed and was rolled back! Reason: {ex}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
