"""
Deterministic, additive, auditable EEE question-to-topic mapping CLI.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_eee_questions_to_topics --dry-run
  python -m scripts.curriculum.map_eee_questions_to_topics --apply
  python -m scripts.curriculum.map_eee_questions_to_topics --sync
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
from backend.services.taxonomy_rules.eee_rules import EEE_TAXONOMY_RULES

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")


def run_eee_mapping(
    db_path: str = DEFAULT_DB_PATH,
    apply_changes: bool = False,
    sync: bool = False,
    verbose_samples: bool = True
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Verify Course 14 existence and scope
    course = c.execute("SELECT id, name, code FROM courses WHERE id = 14").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 14 (Electrical and Electronics Engineering) not found in database.")

    # 2. Load all 35 topics and units for Course 14
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
        WHERE s.course_id = 14
        ORDER BY u.number, t.id
    """).fetchall()
    topic_map = {r["topic_id"]: dict(r) for r in topic_rows}
    all_topic_ids = set(topic_map.keys())

    # 3. Load all questions for Course 14
    questions = c.execute("""
        SELECT 
            q.id, 
            q.original_text, 
            e.id as exam_id, 
            e.year as exam_year, 
            e.assessment_type
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 14
        ORDER BY q.id
    """).fetchall()

    # 4. Load existing mappings for Course 14 questions
    existing_rows = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 14
    """).fetchall()
    existing_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in existing_rows}

    # Count other course mappings for safety check
    other_course_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 14
    """).fetchone()[0]

    # 5. Execute classification
    classifier = TaxonomyClassifierService(EEE_TAXONOMY_RULES)
    proposals: List[ClassificationProposal] = classifier.classify_batch(
        [{"id": q["id"], "original_text": q["original_text"]} for q in questions]
    )

    # 6. Audit classification results
    high_count = sum(1 for p in proposals if p.confidence == "HIGH")
    medium_count = sum(1 for p in proposals if p.confidence == "MEDIUM")
    ambiguous_count = sum(1 for p in proposals if p.confidence == "AMBIGUOUS")
    unmapped_count = sum(1 for p in proposals if p.confidence == "UNMAPPED")
    mappable_proposals = [p for p in proposals if p.confidence in ("HIGH", "MEDIUM") and p.topic_id is not None]

    # Check for cross-course foreign key safety
    for p in mappable_proposals:
        if p.topic_id not in all_topic_ids:
            conn.close()
            raise ValueError(f"Safety Violation: Proposed topic_id {p.topic_id} does not belong to Course 14!")

    # 7. Plan insertions and conflict detection
    inserted_candidates = []
    already_mapped = []
    conflict_candidates = []

    for p in mappable_proposals:
        qid = p.question_id
        tid = p.topic_id
        if qid in existing_mappings:
            if existing_mappings[qid] == tid:
                already_mapped.append((qid, tid))
            else:
                conflict_candidates.append({
                    "question_id": qid,
                    "existing_topic_id": existing_mappings[qid],
                    "proposed_topic_id": tid,
                    "evidence": p.evidence,
                })
        else:
            inserted_candidates.append((qid, tid))

    # 8. Apply changes if requested
    rows_inserted = 0
    if apply_changes and inserted_candidates:
        c.executemany(
            "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
            inserted_candidates
        )
        conn.commit()
        rows_inserted = len(inserted_candidates)

    # Verify other courses were not touched
    post_other_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 14
    """).fetchone()[0]
    if post_other_count != other_course_mappings_count:
        conn.rollback()
        conn.close()
        raise RuntimeError("FATAL: Cross-course mutation detected! Rollback executed.")

    # 9. Aggregate unit and topic distributions
    unit_distribution = defaultdict(int)
    topic_distribution = defaultdict(int)
    unit_samples = defaultdict(list)

    total_mapped_now = len(existing_mappings) + rows_inserted if apply_changes else len(mappable_proposals)
    
    for p in mappable_proposals:
        topic_info = topic_map.get(p.topic_id, {})
        u_num = topic_info.get("unit_number", 0)
        u_name = topic_info.get("unit_name", "Unknown Unit")
        t_name = topic_info.get("topic_name", "Unknown Topic")
        unit_distribution[f"Unit {u_num}: {u_name}"] += 1
        topic_distribution[f"Topic {p.topic_id}: {t_name}"] += 1
        if len(unit_samples[u_num]) < 3:
            # Find question text
            q_text = next((q["original_text"] for q in questions if q["id"] == p.question_id), "")
            unit_samples[u_num].append({
                "question_id": p.question_id,
                "topic_id": p.topic_id,
                "topic_name": t_name,
                "confidence": p.confidence,
                "evidence": p.evidence,
                "sample_text": q_text[:140] + "..." if len(q_text) > 140 else q_text
            })

    zero_mapping_topics = [
        f"Topic {tid}: {t['topic_name']} (Unit {t['unit_number']})"
        for tid, t in topic_map.items()
        if f"Topic {tid}: {t['topic_name']}" not in topic_distribution
    ]

    overloaded_topics = [
        (k, count, f"{count / len(mappable_proposals) * 100:.1f}%")
        for k, count in topic_distribution.items()
        if len(mappable_proposals) > 0 and (count / len(mappable_proposals)) > 0.20
    ]

    conn.close()

    result = {
        "apply_changes": apply_changes,
        "sync_mode": sync,
        "total_questions": len(questions),
        "total_mappable": len(mappable_proposals),
        "high_confidence": high_count,
        "medium_confidence": medium_count,
        "ambiguous_count": ambiguous_count,
        "unmapped_count": unmapped_count,
        "coverage_pct": round(len(mappable_proposals) / len(questions) * 100, 2) if questions else 0.0,
        "new_insertions": len(inserted_candidates),
        "rows_inserted": rows_inserted,
        "already_mapped": len(already_mapped),
        "conflicts": len(conflict_candidates),
        "conflict_details": conflict_candidates[:5],
        "zero_mapping_topics_count": len(zero_mapping_topics),
        "zero_mapping_topics": zero_mapping_topics,
        "overloaded_topics": overloaded_topics,
        "unit_distribution": dict(sorted(unit_distribution.items())),
        "topic_distribution": dict(sorted(topic_distribution.items(), key=lambda x: x[1], reverse=True)),
        "unit_samples": dict(sorted(unit_samples.items())),
    }
    return result


def print_audit_report(res: Dict[str, Any]):
    print("=" * 78)
    print(" COURSE 14 (EEE) QUESTION-TO-TOPIC MAPPING QUALITY AUDIT")
    print("=" * 78)
    print(f"Total Historical Questions: {res['total_questions']}")
    print(f"Total Mappable Questions:   {res['total_mappable']} ({res['coverage_pct']}%)")
    print(f"  - HIGH Confidence:        {res['high_confidence']}")
    print(f"  - MEDIUM Confidence:      {res['medium_confidence']}")
    print(f"  - AMBIGUOUS (Unassigned): {res['ambiguous_count']}")
    print(f"  - UNMAPPED (Insufficient):{res['unmapped_count']}")
    print("-" * 78)
    print(f"Mutation Plan:")
    print(f"  - New Mappings to Insert: {res['new_insertions']}")
    print(f"  - Rows Actually Inserted: {res['rows_inserted']} (Apply={res['apply_changes']})")
    print(f"  - Already Mapped:         {res['already_mapped']}")
    print(f"  - Conflicts Detected:     {res['conflicts']}")
    print("-" * 78)
    print("Per-Unit Mapping Distribution:")
    for u_label, count in res["unit_distribution"].items():
        pct = count / res["total_mappable"] * 100 if res["total_mappable"] else 0
        print(f"  {u_label:45s}: {count:4d} ({pct:5.1f}%)")
    print("-" * 78)
    print(f"Zero-Mapping Topics ({res['zero_mapping_topics_count']}):")
    if res["zero_mapping_topics"]:
        for zt in res["zero_mapping_topics"]:
            print(f"  - {zt}")
    else:
        print("  None! All topics received coverage.")
    print("-" * 78)
    print(f"Overloaded Topics (>20% total):")
    if res["overloaded_topics"]:
        for ot, cnt, pct in res["overloaded_topics"]:
            print(f"  - {ot}: {cnt} ({pct})")
    else:
        print("  None! Topic distribution is healthy and balanced.")
    print("-" * 78)
    print("Representative Mappings per Unit:")
    for u_num, samples in res["unit_samples"].items():
        print(f"\n[Unit {u_num}]")
        for s in samples:
            print(f"  Q{s['question_id']} -> [{s['confidence']}] {s['topic_name']} (tid={s['topic_id']})")
            print(f"     Evidence: {s['evidence']}")
            print(f"     Text: {s['sample_text']}")
    print("=" * 78)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map Course 14 EEE questions to canonical topics.")
    parser.add_argument("--dry-run", action="store_true", help="Run audit without writing changes.")
    parser.add_argument("--apply", action="store_true", help="Apply proposed mappings to database.")
    parser.add_argument("--sync", action="store_true", help="Synchronize / audit mapping delta.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to database.")
    args = parser.parse_args()

    apply_flag = args.apply and not args.dry_run
    report = run_eee_mapping(db_path=args.db_path, apply_changes=apply_flag, sync=args.sync)
    print_audit_report(report)
