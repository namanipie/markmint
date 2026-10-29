"""
Deterministic, additive, auditable Physical and Analytical Chemistry (Course 11) question-to-topic mapping tool.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_pac_questions_to_topics --dry-run
  python -m scripts.curriculum.map_pac_questions_to_topics --apply
"""
import argparse
import os
import sys
import sqlite3
from typing import Dict, List, Any, Tuple
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.taxonomy_classifier import TaxonomyClassifierService, ClassificationProposal
from backend.services.taxonomy_rules.pac_rules import PAC_TAXONOMY_RULES


def run_pac_mapping(
    db_path: str,
    apply_changes: bool = False,
    verbose_samples: bool = True
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Verify Course 11 existence and scope
    course = c.execute("SELECT id, name, code, canonical_code FROM courses WHERE id = 11").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 11 (Physical And Analytical Chemistry) not found in database.")

    # 2. Load all 20 topics and units for Course 11
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
        WHERE s.course_id = 11
        ORDER BY u.number, t.id
    """).fetchall()
    topic_map = {r["topic_id"]: dict(r) for r in topic_rows}
    all_topic_ids = set(topic_map.keys())

    # 3. Load all questions for Course 11
    questions = c.execute("""
        SELECT 
            q.id as question_id,
            q.question_number,
            q.original_text,
            q.normalized_text,
            q.family_id,
            e.assessment_type,
            e.year
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 11
        ORDER BY q.id
    """).fetchall()

    # 4. Check existing mappings in question_topic
    existing_q_topics = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 11
    """).fetchall()
    existing_map = defaultdict(set)
    for r in existing_q_topics:
        existing_map[r["question_id"]].add(r["topic_id"])

    # 5. Initialize Classifier with Course 11 Rules
    classifier = TaxonomyClassifierService(rules=PAC_TAXONOMY_RULES)

    classified_count = 0
    already_mapped_count = 0
    unmapped_count = 0
    new_mappings: List[Tuple[int, int]] = []
    audit_log = []

    for q in questions:
        q_id = q["question_id"]
        raw_text = q["original_text"] or q["normalized_text"] or ""
        
        proposal = classifier.classify(q_id, raw_text)

        if proposal.confidence not in ("HIGH", "MEDIUM") or not proposal.topic_id or proposal.topic_id not in all_topic_ids:
            unmapped_count += 1
            audit_log.append({
                "question_id": q_id,
                "text": raw_text[:120].strip(),
                "status": "UNMAPPED",
                "reason": proposal.method,
                "confidence": proposal.confidence
            })
            continue

        classified_count += 1
        tid = proposal.topic_id

        # Check if already mapped
        already_has = existing_map.get(q_id, set())

        if tid in already_has:
            already_mapped_count += 1
            audit_log.append({
                "question_id": q_id,
                "text": raw_text[:120].strip(),
                "status": "ALREADY_MAPPED",
                "proposed_topic": topic_map[tid]["topic_name"]
            })
        else:
            new_mappings.append((q_id, tid))
            audit_log.append({
                "question_id": q_id,
                "text": raw_text[:120].strip(),
                "status": "NEW_MAPPING",
                "proposed_topic": topic_map[tid]["topic_name"],
                "confidence": proposal.confidence
            })

    # 6. Apply changes if requested (Additive, Idempotent)
    applied_count = 0
    if apply_changes and new_mappings:
        c.executemany(
            "INSERT OR IGNORE INTO question_topic (question_id, topic_id) VALUES (?, ?)",
            new_mappings
        )
        conn.commit()
        applied_count = len(new_mappings)

    # 7. Coverage calculations
    c.execute("""
        SELECT COUNT(DISTINCT q.id)
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN question_topic qt ON q.id = qt.question_id
        WHERE e.course_id = 11
    """)
    total_distinct_mapped = c.fetchone()[0]

    # Topics with at least one question mapped
    c.execute("""
        SELECT COUNT(DISTINCT qt.topic_id)
        FROM question_topic qt
        WHERE qt.topic_id IN ({})
    """.format(",".join(str(tid) for tid in all_topic_ids)))
    active_topics_count = c.fetchone()[0]

    conn.close()

    return {
        "course_id": 11,
        "course_name": course["name"],
        "total_questions": len(questions),
        "classified_in_run": classified_count,
        "unmapped_questions": unmapped_count,
        "new_mappings_found": len(new_mappings),
        "applied_mappings": applied_count,
        "total_distinct_questions_mapped": total_distinct_mapped,
        "active_topics_with_questions": f"{active_topics_count}/{len(all_topic_ids)}",
        "audit_log_sample": audit_log[:15] if verbose_samples else []
    }


def main():
    parser = argparse.ArgumentParser(description="Map Course 11 Physical and Analytical Chemistry questions to canonical syllabus topics.")
    parser.add_argument("--db", default="production_corpus.db", help="Path to SQLite database")
    parser.add_argument("--apply", action="store_true", help="Apply changes idempotently to the database")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without applying changes")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    print(f"Running PAC Question Mapping (apply={apply})...")
    res = run_pac_mapping(args.db, apply_changes=apply)
    print("\n--- Summary ---")
    for k, v in res.items():
        if k != "audit_log_sample":
            print(f"  {k}: {v}")
    
    if res.get("audit_log_sample"):
        print("\n--- Sample Classifications ---")
        for item in res["audit_log_sample"]:
            print(f"  [{item['status']}] Q{item['question_id']}: {item['text']}")
            if item.get("proposed_topic"):
                print(f"      -> Topic: {item['proposed_topic']}")


if __name__ == "__main__":
    main()
