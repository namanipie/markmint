"""
Deterministic, additive, auditable Probability and Statistics question-to-topic mapping CLI.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_prob_questions_to_topics --dry-run
  python -m scripts.curriculum.map_prob_questions_to_topics --apply
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
from backend.services.taxonomy_rules.prob_rules import PROB_TAXONOMY_RULES

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")


def run_prob_mapping(
    db_path: str = DEFAULT_DB_PATH,
    apply_changes: bool = False,
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    course = c.execute("SELECT id, name, code FROM courses WHERE id = 22").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 22 (Probability and Statistics) not found.")

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
        WHERE s.course_id = 22
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
        WHERE e.course_id = 22
        ORDER BY q.id
    """).fetchall()

    existing_rows = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 22
    """).fetchall()
    existing_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in existing_rows}

    other_course_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 22
    """).fetchone()[0]

    classifier = TaxonomyClassifierService(PROB_TAXONOMY_RULES)
    proposals: List[ClassificationProposal] = classifier.classify_batch(
        [{"id": q["id"], "original_text": q["original_text"]} for q in questions]
    )

    high_count = sum(1 for p in proposals if p.confidence == "HIGH")
    medium_count = sum(1 for p in proposals if p.confidence == "MEDIUM")
    ambiguous_count = sum(1 for p in proposals if p.confidence == "AMBIGUOUS")
    unmapped_count = sum(1 for p in proposals if p.confidence == "UNMAPPED")

    # Mutation plan
    new_insertions: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    already_mapped = 0

    for p in proposals:
        if p.confidence not in ("HIGH", "MEDIUM") or p.topic_id is None:
            continue

        qid = p.question_id
        tid = p.topic_id

        assert tid in all_topic_ids, f"Topic {tid} does not belong to Course 22!"

        if qid in existing_mappings:
            curr_tid = existing_mappings[qid]
            if curr_tid == tid:
                already_mapped += 1
            else:
                conflicts.append({
                    "question_id": qid,
                    "existing_topic_id": curr_tid,
                    "proposed_topic_id": tid,
                    "confidence": p.confidence,
                })
        else:
            new_insertions.append({
                "question_id": qid,
                "topic_id": tid,
                "confidence": p.confidence,
                "evidence": p.evidence,
            })

    inserted_count = 0
    if apply_changes and new_insertions:
        conn.execute("BEGIN TRANSACTION")
        try:
            for item in new_insertions:
                c.execute(
                    "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
                    (item["question_id"], item["topic_id"])
                )
            conn.commit()
            inserted_count = len(new_insertions)
        except Exception as e:
            conn.rollback()
            conn.close()
            raise RuntimeError(f"Database mutation failed, rolled back: {e}")

    # Verify zero cross-course leakage
    post_other_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 22
    """).fetchone()[0]
    assert other_course_mappings_count == post_other_count, "Cross-course leakage detected!"

    # Distribution stats
    unit_distribution = defaultdict(int)
    topic_distribution = defaultdict(int)
    for p in proposals:
        if p.confidence in ("HIGH", "MEDIUM") and p.topic_id:
            tinfo = topic_map[p.topic_id]
            unit_distribution[tinfo["unit_name"]] += 1
            topic_distribution[p.topic_id] += 1

    zero_mapping_topics = [
        {"id": tid, "name": tinfo["topic_name"], "unit": tinfo["unit_name"]}
        for tid, tinfo in topic_map.items()
        if topic_distribution[tid] == 0
    ]

    total_mappable = high_count + medium_count
    overloaded_topics = [
        {"id": tid, "name": topic_map[tid]["topic_name"], "count": cnt, "pct": (cnt / total_mappable * 100) if total_mappable else 0}
        for tid, cnt in topic_distribution.items()
        if total_mappable > 0 and (cnt / total_mappable) > 0.20
    ]

    conn.close()

    return {
        "course_id": 22,
        "course_name": course["name"],
        "total_questions": len(questions),
        "total_mappable": total_mappable,
        "high_confidence": high_count,
        "medium_confidence": medium_count,
        "ambiguous_count": ambiguous_count,
        "unmapped_count": unmapped_count,
        "new_insertions": len(new_insertions),
        "rows_inserted": inserted_count,
        "already_mapped": already_mapped,
        "conflicts": len(conflicts),
        "unit_distribution": dict(unit_distribution),
        "topic_distribution": dict(topic_distribution),
        "zero_mapping_topics": zero_mapping_topics,
        "overloaded_topics": overloaded_topics,
        "proposals": proposals,
        "apply_changes": apply_changes,
    }


def print_audit_report(results: Dict[str, Any]):
    print("=" * 78)
    print(" COURSE 22 (PROB) QUESTION-TO-TOPIC MAPPING QUALITY AUDIT")
    print("=" * 78)
    total = results["total_questions"]
    mappable = results["total_mappable"]
    pct = (mappable / total * 100) if total else 0
    print(f"Total Historical Questions: {total}")
    print(f"Total Mappable Questions:   {mappable} ({pct:.2f}%)")
    print(f"  - HIGH Confidence:        {results['high_confidence']}")
    print(f"  - MEDIUM Confidence:      {results['medium_confidence']}")
    print(f"  - AMBIGUOUS (Unassigned): {results['ambiguous_count']}")
    print(f"  - UNMAPPED (Insufficient):{results['unmapped_count']}")
    print("-" * 78)
    print("Mutation Plan:")
    print(f"  - New Mappings to Insert: {results['new_insertions']}")
    print(f"  - Rows Actually Inserted: {results['rows_inserted']} (Apply={results['apply_changes']})")
    print(f"  - Already Mapped:         {results['already_mapped']}")
    print(f"  - Conflicts Detected:     {results['conflicts']}")
    print("-" * 78)
    print("Per-Unit Mapping Distribution:")
    for uname, cnt in results["unit_distribution"].items():
        upct = (cnt / mappable * 100) if mappable else 0
        print(f"  {uname:<45}: {cnt:>4} ({upct:>5.1f}%)")
    print("-" * 78)
    print(f"Zero-Mapping Topics ({len(results['zero_mapping_topics'])}):")
    for zt in results["zero_mapping_topics"]:
        print(f"  - Topic {zt['id']}: {zt['name']} ({zt['unit']})")
    print("-" * 78)
    print("Overloaded Topics (>20% total):")
    if results["overloaded_topics"]:
        for ot in results["overloaded_topics"]:
            print(f"  - Topic {ot['id']}: {ot['name']} ({ot['count']} questions, {ot['pct']:.1f}%)")
    else:
        print("  None! Topic distribution is healthy and balanced.")
    print("=" * 78)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Course 22 (PROB) Question-to-Topic Mapping CLI")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate mapping without mutating DB")
    parser.add_argument("--apply", action="store_true", help="Execute atomic insertion into question_topic")
    args = parser.parse_args()

    apply = args.apply
    res = run_prob_mapping(apply_changes=apply)
    print_audit_report(res)
