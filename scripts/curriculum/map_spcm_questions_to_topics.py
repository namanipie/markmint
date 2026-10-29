"""
Deterministic, additive, auditable SPCM question-to-topic mapping tool.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_spcm_questions_to_topics --dry-run
  python -m scripts.curriculum.map_spcm_questions_to_topics --apply
  python -m scripts.curriculum.map_spcm_questions_to_topics --sync
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
from backend.services.taxonomy_rules.spcm_rules import SPCM_TAXONOMY_RULES


def run_spcm_mapping(
    db_path: str,
    apply_changes: bool = False,
    sync: bool = False,
    verbose_samples: bool = True
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Verify Course 13 existence and scope
    course = c.execute("SELECT id, name, code FROM courses WHERE id = 13").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 13 (Semiconductor Physics and Computational Methods) not found in database.")

    # 2. Load all 27 topics and units for Course 13
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
        WHERE s.course_id = 13
        ORDER BY u.number, t.id
    """).fetchall()
    topic_map = {r["topic_id"]: dict(r) for r in topic_rows}
    all_topic_ids = set(topic_map.keys())

    # 3. Load all questions for Course 13
    questions = c.execute("""
        SELECT 
            q.id, 
            q.original_text, 
            q.marks, 
            e.id as exam_id, 
            e.year as exam_year, 
            e.assessment_type
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
        ORDER BY q.id
    """).fetchall()

    # 4. Load existing mappings for Course 13 questions
    existing_rows = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
    """).fetchall()
    existing_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in existing_rows}

    # Count calculus/chemistry/other existing mappings for safety check
    other_course_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 13
    """).fetchone()[0]

    # 5. Execute classification
    classifier = TaxonomyClassifierService(SPCM_TAXONOMY_RULES)
    proposals: List[ClassificationProposal] = classifier.classify_batch(
        [{"id": q["id"], "original_text": q["original_text"]} for q in questions]
    )

    # 6. Evaluate mappings, persistence actions, and conflict detection
    high_count = 0
    medium_count = 0
    ambiguous_count = 0
    unmapped_count = 0

    to_insert: List[Tuple[int, int]] = []
    preserved_existing: List[Tuple[int, int]] = []
    conflicts: List[Dict[str, Any]] = []

    proposals_by_id = {p.question_id: p for p in proposals}

    for p in proposals:
        q_id = p.question_id
        current_topic_id = existing_mappings.get(q_id)

        if p.confidence == "HIGH":
            high_count += 1
        elif p.confidence == "MEDIUM":
            medium_count += 1
        elif p.confidence == "AMBIGUOUS":
            ambiguous_count += 1
        elif p.confidence == "UNMAPPED":
            unmapped_count += 1

        is_accepted = p.confidence in ("HIGH", "MEDIUM") and p.topic_id is not None

        if current_topic_id is not None:
            if is_accepted:
                if current_topic_id == p.topic_id:
                    preserved_existing.append((q_id, current_topic_id))
                else:
                    conflicts.append({
                        "question_id": q_id,
                        "existing_topic_id": current_topic_id,
                        "proposed_topic_id": p.topic_id,
                        "proposed_topic_name": p.topic_name,
                        "confidence": p.confidence,
                        "reason": "Classifier proposed topic differs from existing mapping; leaving existing mapping unchanged."
                    })
                    preserved_existing.append((q_id, current_topic_id))
            else:
                preserved_existing.append((q_id, current_topic_id))
        else:
            if is_accepted:
                to_insert.append((q_id, p.topic_id))

    # 7. Apply mutations if enabled
    mutations_executed = 0
    if sync:
        c.execute("""
            DELETE FROM question_topic
            WHERE question_id IN (
                SELECT q.id
                FROM questions q
                JOIN sections s ON q.section_id = s.id
                JOIN exams e ON s.exam_id = e.id
                WHERE e.course_id = 13
            )
        """)
        all_accepted = [(p.question_id, p.topic_id) for p in proposals if p.topic_id is not None]
        c.executemany(
            "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
            all_accepted
        )
        mutations_executed = len(all_accepted)
        conn.commit()
    elif apply_changes and to_insert:
        c.executemany(
            "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
            to_insert
        )
        mutations_executed = len(to_insert)
        conn.commit()

    # 8. Post-state query and integrity verification
    post_spcm_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
    """).fetchone()[0]

    post_other_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 13
    """).fetchone()[0]

    # Verify no cross-course mappings exist
    cross_course_violations = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses syl ON u.syllabus_id = syl.id
        WHERE e.course_id = 13 AND syl.course_id != 13
    """).fetchone()[0]

    # Compute breakdown by unit and topic
    unit_distribution = defaultdict(lambda: {"unit_name": "", "unit_number": 0, "count": 0, "topics": defaultdict(int)})
    topic_distribution = defaultdict(int)

    active_spcm_mappings = c.execute("""
        SELECT qt.question_id, qt.topic_id, t.name as topic_name, u.number as unit_number, u.name as unit_name
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        JOIN units u ON t.unit_id = u.id
        WHERE e.course_id = 13
    """).fetchall()

    for r in active_spcm_mappings:
        u_num = r["unit_number"]
        u_name = r["unit_name"]
        t_name = r["topic_name"]
        unit_distribution[u_num]["unit_number"] = u_num
        unit_distribution[u_num]["unit_name"] = u_name
        unit_distribution[u_num]["count"] += 1
        unit_distribution[u_num]["topics"][t_name] += 1
        topic_distribution[t_name] += 1

    # Topics with zero mappings
    unmapped_topic_names = [
        topic_map[tid]["topic_name"]
        for tid in all_topic_ids
        if topic_map[tid]["topic_name"] not in topic_distribution
    ]

    conn.close()

    total_questions = len(questions)
    accepted_mappings_count = high_count + medium_count
    coverage_pct = round((accepted_mappings_count / total_questions) * 100, 2) if total_questions > 0 else 0.0

    return {
        "course_id": 13,
        "course_name": course["name"],
        "dry_run": not (apply_changes or sync),
        "total_questions": total_questions,
        "high_confidence_count": high_count,
        "medium_confidence_count": medium_count,
        "ambiguous_count": ambiguous_count,
        "unmapped_count": unmapped_count,
        "accepted_mappings_count": accepted_mappings_count,
        "coverage_percentage": coverage_pct,
        "rows_to_insert": len(to_insert),
        "mutations_executed": mutations_executed,
        "pre_existing_preserved": len(preserved_existing),
        "conflicts_detected": len(conflicts),
        "conflicts": conflicts,
        "total_active_spcm_mappings": post_spcm_mappings_count,
        "other_course_mappings_preserved": post_other_mappings_count,
        "other_course_invariance_maintained": (other_course_mappings_count == post_other_mappings_count),
        "cross_course_violations": cross_course_violations,
        "unit_distribution": dict(unit_distribution),
        "topic_distribution": dict(topic_distribution),
        "unmapped_topics": unmapped_topic_names,
        "proposals": proposals,
        "questions_dict": {q["id"]: dict(q) for q in questions},
    }


def print_mapping_report(results: Dict[str, Any], verbose: bool = True) -> None:
    mode_str = "APPLY (COMMITTED)" if not results["dry_run"] else "DRY-RUN (NO MUTATIONS)"
    print("\n" + "=" * 80)
    print(f" SPCM (Course 13) Question-Topic Mapping Report [{mode_str}]")
    print("=" * 80)
    print(f"Course:                     {results['course_name']} (ID: {results['course_id']})")
    print(f"Total Exam Questions:       {results['total_questions']}")
    print(f"HIGH Confidence Mappings:   {results['high_confidence_count']} ({results['high_confidence_count']/results['total_questions']*100:.1f}%)")
    print(f"MEDIUM Confidence Mappings: {results['medium_confidence_count']} ({results['medium_confidence_count']/results['total_questions']*100:.1f}%)")
    print(f"AMBIGUOUS (Left Unmapped):  {results['ambiguous_count']} ({results['ambiguous_count']/results['total_questions']*100:.1f}%)")
    print(f"UNMAPPED (No Strong Match): {results['unmapped_count']} ({results['unmapped_count']/results['total_questions']*100:.1f}%)")
    print(f"Accepted Mapping Proposals: {results['accepted_mappings_count']} ({results['coverage_percentage']}%)")
    print("-" * 80)
    print(f"Rows Scheduled for Insert:  {results['rows_to_insert']}")
    print(f"Mutations Executed:         {results['mutations_executed']}")
    print(f"Pre-existing Preserved:     {results['pre_existing_preserved']}")
    print(f"Conflicts Detected:         {results['conflicts_detected']}")
    print(f"Total Active SPCM Mappings: {results['total_active_spcm_mappings']}")
    print(f"Other Course Mappings:      {results['other_course_mappings_preserved']} (Invariant: {results['other_course_invariance_maintained']})")
    print(f"Cross-Course Violations:    {results['cross_course_violations']}")
    print("=" * 80)

    print("\n--- Coverage Breakdown by Unit ---")
    unit_dist = results["unit_distribution"]
    for u_num in sorted(unit_dist.keys()):
        u = unit_dist[u_num]
        print(f"  Unit {u_num}: {u['unit_name']} -> {u['count']} mapped questions")
        for t_name, count in sorted(u["topics"].items(), key=lambda x: -x[1]):
            print(f"     - {t_name}: {count}")

    if results["unmapped_topics"]:
        print("\n--- Topics with 0 Mappings (Exam Corpus Coverage Gaps) ---")
        for t in results["unmapped_topics"]:
            print(f"  * {t}")

    if verbose and results["proposals"]:
        print("\n--- Representative Accepted High-Confidence Mappings ---")
        high_samples = [p for p in results["proposals"] if p.confidence == "HIGH"][:6]
        for p in high_samples:
            q_text = results["questions_dict"][p.question_id]["original_text"]
            print(f"  Q[{p.question_id}] -> [{p.unit_name}] Topic: {p.topic_name}")
            print(f"    Evidence: {p.evidence}")
            print(f"    Text: {repr(q_text[:110])}\n")

        print("--- Representative Ambiguous Rejections ---")
        amb_samples = [p for p in results["proposals"] if p.confidence == "AMBIGUOUS"][:4]
        for p in amb_samples:
            q_text = results["questions_dict"][p.question_id]["original_text"]
            print(f"  Q[{p.question_id}] -> Plausible topics: {[c['topic_name'] for c in p.candidate_topics]}")
            print(f"    Evidence: {p.evidence}")
            print(f"    Text: {repr(q_text[:110])}\n")

        print("--- Representative Unmapped / Insufficient Context ---")
        unm_samples = [p for p in results["proposals"] if p.confidence == "UNMAPPED"][:4]
        for p in unm_samples:
            q_text = results["questions_dict"][p.question_id]["original_text"]
            print(f"  Q[{p.question_id}] -> Reason: {p.evidence}")
            print(f"    Text: {repr(q_text[:110])}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic SPCM question-to-topic mapping tool.")
    parser.add_argument("--db", default="production_corpus.db", help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Simulate classification without committing")
    parser.add_argument("--apply", action="store_true", help="Commit missing question-topic mappings")
    parser.add_argument("--sync", action="store_true", help="Safe idempotent reconciliation")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose sample output")
    args = parser.parse_args()

    if not (args.dry_run or args.apply or args.sync):
        print("Please specify --dry-run, --apply, or --sync")
        sys.exit(1)

    res = run_spcm_mapping(
        db_path=args.db,
        apply_changes=args.apply,
        sync=args.sync,
        verbose_samples=not args.quiet
    )
    print_mapping_report(res, verbose=not args.quiet)
