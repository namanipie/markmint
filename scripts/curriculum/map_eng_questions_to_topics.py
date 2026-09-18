"""
Deterministic, additive, auditable Communicative English question-to-topic mapping CLI.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_eng_questions_to_topics --dry-run
  python -m scripts.curriculum.map_eng_questions_to_topics --apply
"""
import argparse
import os
import sys
import sqlite3
from typing import Dict, List, Any
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.taxonomy_classifier import TaxonomyClassifierService, ClassificationProposal
from backend.services.taxonomy_rules.eng_rules import ENG_TAXONOMY_RULES

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")


def run_eng_mapping(
    db_path: str = DEFAULT_DB_PATH,
    apply_changes: bool = False,
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    course = c.execute("SELECT id, name, code FROM courses WHERE id = 15").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 15 (Communicative English) not found.")

    topic_rows = c.execute("""
        SELECT 
            t.id as topic_id, 
            t.name as topic_name, 
            u.id as unit_id, 
            u.number as unit_number, 
            u.name as unit_name
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id = 15
        ORDER BY u.number, t.id
    """).fetchall()
    topic_map = {r["topic_id"]: dict(r) for r in topic_rows}
    all_topic_ids = set(topic_map.keys())

    questions = c.execute("""
        SELECT 
            q.id, 
            q.original_text, 
            e.id as exam_id, 
            e.year as exam_year
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 15
        ORDER BY q.id
    """).fetchall()

    existing_rows = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 15
    """).fetchall()
    existing_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in existing_rows}

    other_course_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 15
    """).fetchone()[0]

    classifier = TaxonomyClassifierService(ENG_TAXONOMY_RULES)
    proposals: List[ClassificationProposal] = classifier.classify_batch(
        [{"id": q["id"], "original_text": q["original_text"]} for q in questions]
    )

    confidence_counts = defaultdict(int)
    method_counts = defaultdict(int)

    for proposal in proposals:
        confidence_counts[proposal.confidence] += 1
        method_counts[proposal.method] += 1

    to_insert: List[Dict[str, Any]] = []
    already_correct = 0
    conflicts: List[Dict[str, Any]] = []
    unmapped_or_ambiguous = 0

    for prop in proposals:
        qid = prop.question_id
        mapped_tid = prop.topic_id

        if prop.confidence in ("HIGH", "MEDIUM") and mapped_tid:
            if mapped_tid not in all_topic_ids:
                raise ValueError(f"Topic {mapped_tid} does not belong to Course 15!")

            if qid in existing_mappings:
                current_tid = existing_mappings[qid]
                if current_tid == mapped_tid:
                    already_correct += 1
                else:
                    conflicts.append({
                        "question_id": qid,
                        "existing_topic_id": current_tid,
                        "proposed_topic_id": mapped_tid,
                        "confidence": prop.confidence,
                        "evidence": prop.evidence,
                    })
            else:
                to_insert.append({
                    "question_id": qid,
                    "topic_id": mapped_tid,
                    "confidence": prop.confidence,
                    "method": prop.method,
                    "evidence": prop.evidence,
                })
        else:
            unmapped_or_ambiguous += 1

    coverage_pct = round(
        (len(to_insert) + already_correct) / len(questions) * 100, 2
    ) if questions else 0.0

    print("=" * 70)
    print("COURSE 15: COMMUNICATIVE ENGLISH QUESTION-TOPIC MAPPING AUDIT")
    print("=" * 70)
    print(f"Total questions in Course 15:        {len(questions)}")
    print(f"Topics available in Course 15:       {len(all_topic_ids)}")
    print(f"Existing mappings in DB:             {len(existing_mappings)}")
    print(f"High confidence proposals:           {confidence_counts['HIGH']}")
    print(f"Medium confidence proposals:         {confidence_counts['MEDIUM']}")
    print(f"Ambiguous (rejected) proposals:      {confidence_counts['AMBIGUOUS']}")
    print(f"Unmapped proposals:                  {confidence_counts['UNMAPPED']}")
    print(f"New rows to insert:                  {len(to_insert)}")
    print(f"Already mapped and matching:         {already_correct}")
    print(f"Conflicting existing mappings:       {len(conflicts)}")
    print(f"Projected total coverage:            {coverage_pct}%")
    print("=" * 70)

    if conflicts:
        print(f"WARNING: {len(conflicts)} conflicting mappings found! These will NOT be overwritten.")
        for conf in conflicts[:5]:
            print(f"  Q{conf['question_id']}: existing={conf['existing_topic_id']} vs proposed={conf['proposed_topic_id']}")

    if apply_changes:
        if conflicts:
            print("Preserving conflicting rows without modification.")
        if to_insert:
            print(f"Applying {len(to_insert)} new mappings inside an atomic transaction...")
            try:
                c.execute("BEGIN TRANSACTION")
                for item in to_insert:
                    c.execute(
                        "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
                        (item["question_id"], item["topic_id"]),
                    )
                conn.commit()
                print(f"Successfully committed {len(to_insert)} question_topic rows.")
            except Exception as e:
                conn.rollback()
                print(f"Transaction failed and was rolled back: {e}")
                raise
        else:
            print("No new mappings to insert.")

        post_check_other = c.execute("""
            SELECT count(*)
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id != 15
        """).fetchone()[0]
        assert post_check_other == other_course_mappings_count, (
            f"Cross-course contamination! Other course mappings changed from "
            f"{other_course_mappings_count} to {post_check_other}"
        )

        total_mapped = c.execute("""
            SELECT count(*)
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 15
        """).fetchone()[0]
        print(f"Post-apply total mapped questions for Course 15: {total_mapped}")

    conn.close()

    return {
        "total_questions": len(questions),
        "high_confidence": confidence_counts["HIGH"],
        "medium_confidence": confidence_counts["MEDIUM"],
        "ambiguous": confidence_counts["AMBIGUOUS"],
        "unmapped": confidence_counts["UNMAPPED"],
        "to_insert": len(to_insert),
        "already_correct": already_correct,
        "conflicts": len(conflicts),
        "coverage_pct": coverage_pct,
    }


def main():
    parser = argparse.ArgumentParser(description="Map Communicative English questions to topics.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite database")
    parser.add_argument("--apply", action="store_true", help="Apply changes to the database")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without mutating database")
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        print("Specify either --dry-run or --apply.")
        sys.exit(1)

    run_eng_mapping(db_path=args.db_path, apply_changes=args.apply)


if __name__ == "__main__":
    main()
