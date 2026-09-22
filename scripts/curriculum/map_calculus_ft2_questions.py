"""
Deterministic mapping tool for Calculus 2025 FT2 / CT2 exam questions (Exams 17 and 18).
Maps questions 456-462 (Exam 17) and 463-469 (Exam 18) to canonical syllabus topics.

Usage:
    python scripts/curriculum/map_calculus_ft2_questions.py --dry-run
    python scripts/curriculum/map_calculus_ft2_questions.py --apply
"""

import sys
import os
import sqlite3
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Deterministic mappings with topic evidence
CALCULUS_FT2_MAPPINGS = [
    # Exam 17 (2025 FT2 Set A)
    {
        "exam_id": 17,
        "question_id": 456,
        "question_number": "1",
        "topic_id": 1,
        "topic_name": "Eigenvalues and Eigenvectors",
        "unit_number": 1,
        "evidence": "Find the eigenvalues and eigenvectors of the matrix."
    },
    {
        "exam_id": 17,
        "question_id": 457,
        "question_number": "2",
        "topic_id": 33,
        "topic_name": "Quadratic Forms",
        "unit_number": 1,
        "evidence": "Find the eigenvalues and nature of the quadratic form."
    },
    {
        "exam_id": 17,
        "question_id": 458,
        "question_number": "3",
        "topic_id": 35,
        "topic_name": "Taylor Series",
        "unit_number": 5,
        "evidence": "Expand f(x,y) using Taylor's theorem."
    },
    {
        "exam_id": 17,
        "question_id": 459,
        "question_number": "4",
        "topic_id": 14,
        "topic_name": "Partial Derivatives",
        "unit_number": 6,
        "evidence": "Find dy/dx and Jacobian partial derivatives."
    },
    {
        "exam_id": 17,
        "question_id": 460,
        "question_number": "5",
        "topic_id": 33,
        "topic_name": "Quadratic Forms",
        "unit_number": 1,
        "evidence": "Reduce the quadratic form to canonical form and find rank, signature, and nature."
    },
    {
        "exam_id": 17,
        "question_id": 461,
        "question_number": "6",
        "topic_id": 32,
        "topic_name": "Cayley-Hamilton Theorem",
        "unit_number": 1,
        "evidence": "Verify Cayley-Hamilton theorem for the matrix and find its inverse."
    },
    {
        "exam_id": 17,
        "question_id": 462,
        "question_number": "7",
        "topic_id": 34,
        "topic_name": "Extrema and Optimization",
        "unit_number": 6,
        "evidence": "Using Lagrange's multiplier method, find maximum and minimum values."
    },
    # Exam 18 (2025 FT-II Set B)
    {
        "exam_id": 18,
        "question_id": 463,
        "question_number": "1",
        "topic_id": 1,
        "topic_name": "Eigenvalues and Eigenvectors",
        "unit_number": 1,
        "evidence": "Find the eigenvalues and eigenvectors of the matrix."
    },
    {
        "exam_id": 18,
        "question_id": 464,
        "question_number": "2",
        "topic_id": 1,
        "topic_name": "Eigenvalues and Eigenvectors",
        "unit_number": 1,
        "evidence": "Find the eigenvalues and corresponding properties of Matrix A."
    },
    {
        "exam_id": 18,
        "question_id": 465,
        "question_number": "3",
        "topic_id": 35,
        "topic_name": "Taylor Series",
        "unit_number": 5,
        "evidence": "Expand f(x,y) using Taylor's theorem."
    },
    {
        "exam_id": 18,
        "question_id": 466,
        "question_number": "4",
        "topic_id": 14,
        "topic_name": "Partial Derivatives",
        "unit_number": 6,
        "evidence": "Find derivative using partial differentiation and Jacobian."
    },
    {
        "exam_id": 18,
        "question_id": 467,
        "question_number": "5",
        "topic_id": 33,
        "topic_name": "Quadratic Forms",
        "unit_number": 1,
        "evidence": "Reduce the quadratic form to canonical form for Matrix A."
    },
    {
        "exam_id": 18,
        "question_id": 468,
        "question_number": "6",
        "topic_id": 32,
        "topic_name": "Cayley-Hamilton Theorem",
        "unit_number": 1,
        "evidence": "Verify Cayley-Hamilton theorem for the matrix and find A^4."
    },
    {
        "exam_id": 18,
        "question_id": 469,
        "question_number": "7",
        "topic_id": 34,
        "topic_name": "Extrema and Optimization",
        "unit_number": 6,
        "evidence": "Find maximum volume of rectangular box inscribed in ellipsoid using Lagrange multipliers."
    },
]


def run_mapping(db_path: str, apply_changes: bool = False):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=" * 80)
    print("CALCULUS 2025 FT2 / CT2 QUESTION-TO-TOPIC MAPPING TOOL")
    print(f"Database: {db_path}")
    print(f"Mode: {'APPLY (Mutating DB)' if apply_changes else 'DRY RUN (No mutations)'}")
    print("=" * 80)

    # 1. Verify existence of Course 1 and canonical topics
    calc = c.execute("SELECT id, name FROM courses WHERE id = 1").fetchone()
    if not calc:
        print("[ERROR] Course 1 not found!")
        conn.close()
        return

    # Verify topics exist
    topic_ids = [m["topic_id"] for m in CALCULUS_FT2_MAPPINGS]
    existing_topics = dict(c.execute(
        f"SELECT id, name FROM topics WHERE id IN ({','.join('?' for _ in topic_ids)})",
        topic_ids
    ).fetchall())

    for m in CALCULUS_FT2_MAPPINGS:
        assert m["topic_id"] in existing_topics, f"Topic id {m['topic_id']} missing in DB!"

    # 2. Check existing mappings for these questions
    q_ids = [m["question_id"] for m in CALCULUS_FT2_MAPPINGS]
    existing_q_topics = c.execute(
        f"SELECT question_id, topic_id FROM question_topic WHERE question_id IN ({','.join('?' for _ in q_ids)})",
        q_ids
    ).fetchall()
    existing_map = {row[0]: row[1] for row in existing_q_topics}

    to_insert = []
    already_mapped = []

    for m in CALCULUS_FT2_MAPPINGS:
        qid = m["question_id"]
        tid = m["topic_id"]
        if qid in existing_map:
            already_mapped.append(m)
        else:
            to_insert.append(m)

    print(f"\nTotal candidate questions: {len(CALCULUS_FT2_MAPPINGS)}")
    print(f"Already mapped: {len(already_mapped)}")
    print(f"To insert: {len(to_insert)}")

    print("\nMapping Details:")
    for m in CALCULUS_FT2_MAPPINGS:
        status = "ALREADY_MAPPED" if m["question_id"] in existing_map else "PENDING_INSERT"
        print(f"  Exam {m['exam_id']} | Q#{m['question_number']} (ID={m['question_id']}) -> Topic {m['topic_id']} ({m['topic_name']}, Unit {m['unit_number']}) [{status}]")
        print(f"    Evidence: {m['evidence']}")

    if apply_changes and to_insert:
        for m in to_insert:
            c.execute(
                "INSERT OR IGNORE INTO question_topic (question_id, topic_id) VALUES (?, ?)",
                (m["question_id"], m["topic_id"])
            )
        conn.commit()
        print(f"\n[SUCCESS] Successfully applied {len(to_insert)} mappings to database.")
    elif not apply_changes:
        print(f"\n[DRY RUN] {len(to_insert)} rows would be inserted. Run with --apply to commit.")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map Calculus FT2 questions to canonical topics.")
    parser.add_argument("--apply", action="store_true", help="Apply mutations to the database.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without applying mutations.")
    parser.add_argument("--db", default=os.path.join(BASE_DIR, "production_corpus.db"), help="Path to database.")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    run_mapping(args.db, apply_changes=apply)
