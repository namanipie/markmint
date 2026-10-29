"""
Deterministic, additive, auditable Programming For Problem Solving (Course 5) question-to-topic mapping tool.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_pps_questions_to_topics --dry-run
  python -m scripts.curriculum.map_pps_questions_to_topics --apply
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
from backend.services.taxonomy_rules.pps_rules import PPS_TAXONOMY_RULES


def run_pps_mapping(
    db_path: str,
    apply_changes: bool = False,
    verbose_samples: bool = True
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Verify Course 5 existence and scope
    course = c.execute("SELECT id, name, code, canonical_code FROM courses WHERE id = 5").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 5 (Programming For Problem Solving) not found in database.")

    # 2. Load all 20 topics and units for Course 5
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
        WHERE s.course_id = 5
        ORDER BY u.number, t.id
    """).fetchall()
    topic_map = {r["topic_id"]: dict(r) for r in topic_rows}
    all_topic_ids = set(topic_map.keys())

    # 3. Load all questions for Course 5
    questions = c.execute("""
        SELECT 
            q.id as question_id,
            q.question_number,
            q.original_text,
            q.marks,
            e.id as exam_id,
            e.year as exam_year,
            e.term as exam_term,
            s.name as section_name
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 5
        ORDER BY e.year ASC, q.id ASC
    """).fetchall()
    total_q_count = len(questions)

    # 4. Load existing question_topic mappings for Course 5
    existing_rows = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 5
    """).fetchall()
    existing_mappings = {(r["question_id"], r["topic_id"]) for r in existing_rows}
    questions_already_mapped = {r["question_id"] for r in existing_rows}

    # 5. Initialize classifier
    classifier = TaxonomyClassifierService(PPS_TAXONOMY_RULES)

    # Track classification outcomes
    high_proposals: List[ClassificationProposal] = []
    med_proposals: List[ClassificationProposal] = []
    ambiguous_proposals: List[ClassificationProposal] = []
    unmapped_proposals: List[ClassificationProposal] = []

    proposals_by_qid: Dict[int, ClassificationProposal] = {}

    for q in questions:
        qid = q["question_id"]
        text = q["original_text"] or ""
        proposal = classifier.classify(qid, text)
        proposals_by_qid[qid] = proposal

        if proposal.confidence == "HIGH":
            high_proposals.append(proposal)
        elif proposal.confidence == "MEDIUM":
            med_proposals.append(proposal)
        elif proposal.confidence == "AMBIGUOUS":
            ambiguous_proposals.append(proposal)
        else:
            unmapped_proposals.append(proposal)

    # Filter accepted mappings (HIGH and MEDIUM only)
    accepted_proposals = [p for p in high_proposals + med_proposals if p.topic_id in all_topic_ids]

    # Partition into inserts vs existing
    to_insert: List[Tuple[int, int]] = []
    already_identical = 0
    conflicts = 0

    for p in accepted_proposals:
        pair = (p.question_id, p.topic_id)
        if pair in existing_mappings:
            already_identical += 1
        elif p.question_id in questions_already_mapped:
            conflicts += 1
        else:
            to_insert.append(pair)

    # Calculate statistics
    accepted_count = len(accepted_proposals)
    coverage_pct = round((accepted_count / total_q_count * 100), 2) if total_q_count > 0 else 0.0

    by_unit: Dict[int, int] = defaultdict(int)
    by_topic: Dict[str, int] = defaultdict(int)

    for p in accepted_proposals:
        u_num = topic_map[p.topic_id]["unit_number"]
        t_name = p.topic_name or topic_map[p.topic_id]["topic_name"]
        by_unit[u_num] += 1
        by_topic[t_name] += 1

    zero_mapping_topics = [
        t["topic_name"] for tid, t in topic_map.items() if by_topic[t["topic_name"]] == 0
    ]

    print("\n" + "=" * 80)
    print("COURSE 5 (Programming For Problem Solving) TAXONOMY CLASSIFICATION AUDIT")
    print("=" * 80)
    print(f"Total Course 5 Questions     : {total_q_count}")
    print(f"HIGH Confidence Candidates   : {len(high_proposals)} ({round(len(high_proposals)/total_q_count*100, 1)}%)")
    print(f"MEDIUM Confidence Candidates : {len(med_proposals)} ({round(len(med_proposals)/total_q_count*100, 1)}%)")
    print(f"AMBIGUOUS (Preserved Unmapped): {len(ambiguous_proposals)} ({round(len(ambiguous_proposals)/total_q_count*100, 1)}%)")
    print(f"UNMAPPED                     : {len(unmapped_proposals)} ({round(len(unmapped_proposals)/total_q_count*100, 1)}%)")
    print("-" * 80)
    print(f"Accepted Question Mappings   : {accepted_count} / {total_q_count} ({coverage_pct}% coverage)")
    print(f"Already Mapped (Identical)   : {already_identical}")
    print(f"Mapping Conflicts            : {conflicts}")
    print(f"New Rows to Insert           : {len(to_insert)}")
    print("-" * 80)
    print("MAPPINGS BY UNIT:")
    for u_num in sorted(by_unit.keys()):
        print(f"  Unit {u_num}: {by_unit[u_num]} questions")
    print("-" * 80)
    print(f"Zero-Mapping Topics ({len(zero_mapping_topics)}):")
    for z in zero_mapping_topics:
        print(f"  - {z}")

    if verbose_samples:
        print("\n" + "-" * 80)
        print("REPRESENTATIVE ACCEPTED SAMPLES:")
        samples_shown = 0
        for p in accepted_proposals:
            if samples_shown >= 8:
                break
            q_row = next(q for q in questions if q["question_id"] == p.question_id)
            snippet = (q_row["original_text"] or "")[:120].strip()
            print(f"  [Q{p.question_id} -> {p.topic_name} ({p.confidence}/{p.method})]: {snippet}...")
            samples_shown += 1

        if ambiguous_proposals:
            print("\nREPRESENTATIVE AMBIGUOUS SAMPLES:")
            for p in ambiguous_proposals[:3]:
                q_row = next(q for q in questions if q["question_id"] == p.question_id)
                snippet = (q_row["original_text"] or "")[:120].strip()
                print(f"  [Q{p.question_id} (AMBIGUOUS - {p.evidence})]: {snippet}...")

    if apply_changes and to_insert:
        print("\n" + "=" * 80)
        print(f"APPLYING {len(to_insert)} NEW QUESTION_TOPIC MAPPINGS...")
        c.executemany(
            "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
            to_insert
        )
        conn.commit()
        print(f"[SUCCESS] Inserted {len(to_insert)} rows into question_topic.")
    elif apply_changes and not to_insert:
        print("\n[INFO] No new rows to insert. Database already up to date.")

    conn.close()

    return {
        "total_questions": total_q_count,
        "high_count": len(high_proposals),
        "med_count": len(med_proposals),
        "ambiguous_count": len(ambiguous_proposals),
        "unmapped_count": len(unmapped_proposals),
        "accepted_count": accepted_count,
        "coverage_pct": coverage_pct,
        "to_insert_count": len(to_insert),
        "zero_mapping_topics": zero_mapping_topics,
        "by_unit": dict(by_unit),
    }


def main():
    parser = argparse.ArgumentParser(description="Map Programming For Problem Solving questions to canonical topics.")
    parser.add_argument("--apply", action="store_true", help="Apply proposed mappings to SQLite database.")
    parser.add_argument("--db", default="production_corpus.db", help="Path to SQLite database.")
    args = parser.parse_args()

    run_pps_mapping(args.db, apply_changes=args.apply)


if __name__ == "__main__":
    main()
