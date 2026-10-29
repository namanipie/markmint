"""
Deterministic, additive, auditable Chemistry question-to-topic mapping tool.
Operates on local database only; preserves all existing mappings; never overwrites conflicts.

Usage:
  python -m scripts.curriculum.map_chemistry_questions_to_topics --dry-run
  python -m scripts.curriculum.map_chemistry_questions_to_topics --apply
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
from backend.services.taxonomy_rules.chemistry_rules import CHEMISTRY_TAXONOMY_RULES


def run_chemistry_mapping(
    db_path: str,
    apply_changes: bool = False,
    sync: bool = False,
    verbose_samples: bool = True
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Verify Course 2 existence and scope
    course = c.execute("SELECT id, name, code FROM courses WHERE id = 2").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 2 (Chemistry) not found in database.")

    # 2. Load all 45 topics and units for Course 2
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
        WHERE s.course_id = 2
        ORDER BY u.number, t.id
    """).fetchall()
    topic_map = {r["topic_id"]: dict(r) for r in topic_rows}
    all_topic_ids = set(topic_map.keys())

    # 3. Load all questions for Course 2
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
        WHERE e.course_id = 2
        ORDER BY q.id
    """).fetchall()

    # 4. Load existing mappings for Course 2 questions
    existing_rows = c.execute("""
        SELECT qt.question_id, qt.topic_id
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """).fetchall()
    existing_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in existing_rows}

    # Count calculus/other existing mappings for safety check
    other_course_mappings_count = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 2
    """).fetchone()[0]

    # 5. Execute classification
    classifier = TaxonomyClassifierService(CHEMISTRY_TAXONOMY_RULES)
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
        else:
            unmapped_count += 1

        # Check persistence action
        if sync:
            if p.topic_id is not None:
                to_insert.append((q_id, p.topic_id))
        else:
            if p.topic_id is not None:
                if current_topic_id is None:
                    # Missing mapping -> safe to add
                    to_insert.append((q_id, p.topic_id))
                elif current_topic_id == p.topic_id:
                    # Identical mapping already in place -> preserve
                    preserved_existing.append((q_id, p.topic_id))
                else:
                    # Conflict: Existing mapping differs from proposal!
                    # Strictly preserve existing mapping and report conflict
                    conflicts.append({
                        "question_id": q_id,
                        "existing_topic_id": current_topic_id,
                        "existing_topic_name": topic_map.get(current_topic_id, {}).get("topic_name", f"Topic #{current_topic_id}"),
                        "proposed_topic_id": p.topic_id,
                        "proposed_topic_name": p.topic_name,
                        "confidence": p.confidence,
                        "evidence": p.evidence,
                    })
            else:
                # No accepted mapping from classifier
                if current_topic_id is not None:
                    # Question has a human/prior mapping that classifier didn't match -> preserve it!
                    preserved_existing.append((q_id, current_topic_id))

    # 7. Apply mutations if requested
    inserted_count = 0
    deleted_count = 0
    if apply_changes:
        if sync:
            c.execute("""
                DELETE FROM question_topic
                WHERE question_id IN (
                    SELECT q.id
                    FROM questions q
                    JOIN sections s ON q.section_id = s.id
                    JOIN exams e ON s.exam_id = e.id
                    WHERE e.course_id = 2
                )
            """)
            deleted_count = len(existing_mappings)
        for q_id, t_id in to_insert:
            c.execute(
                "INSERT INTO question_topic (question_id, topic_id) VALUES (?, ?)",
                (q_id, t_id)
            )
            inserted_count += 1
        conn.commit()

    # 8. Post-action verification
    final_c2_mappings = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """).fetchone()[0]

    final_other_mappings = c.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id != 2
    """).fetchone()[0]

    # Verify non-Chemistry mappings were not mutated
    assert final_other_mappings == other_course_mappings_count, (
        f"INVARIANT VIOLATION: Non-Chemistry mappings changed from {other_course_mappings_count} to {final_other_mappings}!"
    )

    # 9. Compute audit metrics
    accepted_mapped_total = high_count + medium_count
    total_q = len(questions)
    coverage_pct = (accepted_mapped_total / total_q * 100) if total_q > 0 else 0.0

    # Unit breakdown
    unit_distribution = defaultdict(int)
    topic_distribution = defaultdict(int)
    for p in proposals:
        if p.topic_id is not None:
            unit_distribution[p.unit_name or "Unknown Unit"] += 1
            topic_distribution[p.topic_id] += 1

    zero_mapped_topics = [t for t_id, t in topic_map.items() if topic_distribution[t_id] == 0]
    overloaded_topics = [
        (topic_map[t_id]["topic_name"], count)
        for t_id, count in topic_distribution.items()
        if count > 20
    ]

    # 10. Print comprehensive report
    mode_str = "APPLY (COMMITTED TO DB)" if apply_changes else "DRY-RUN (NO DB MUTATIONS)"
    print("=" * 80)
    print(f"CHEMISTRY QUESTION -> TOPIC MAPPING AUDIT REPORT [{mode_str}]")
    print("=" * 80)
    print(f"Target Course: {course['name']} (ID: {course['id']}, Code: {course['code']})")
    print(f"Database Path: {db_path}")
    print(f"Total Course Questions: {total_q}")
    print(f"Pre-existing Course 2 Mappings: {len(existing_mappings)}")
    print(f"Non-Course-2 Mappings in DB: {other_course_mappings_count} (Preserved intact)")
    print("-" * 80)
    print("CLASSIFIER BREAKDOWN:")
    print(f"  HIGH Confidence Mappings    : {high_count:3d} ({high_count / total_q * 100:5.1f}%)")
    print(f"  MEDIUM Confidence Mappings  : {medium_count:3d} ({medium_count / total_q * 100:5.1f}%)")
    print(f"  AMBIGUOUS (Left Unmapped)   : {ambiguous_count:3d} ({ambiguous_count / total_q * 100:5.1f}%)")
    print(f"  UNMAPPED (No strong match)  : {unmapped_count:3d} ({unmapped_count / total_q * 100:5.1f}%)")
    print(f"  ACCEPTED MAPPING COVERAGE   : {accepted_mapped_total:3d} / {total_q} ({coverage_pct:5.1f}%)")
    print("-" * 80)
    print("PERSISTENCE ACTIONS:")
    print(f"  New Mappings to Insert      : {len(to_insert):3d} (Inserted: {inserted_count})")
    print(f"  Pre-existing Preserved      : {len(preserved_existing):3d}")
    print(f"  Existing Mapping Conflicts  : {len(conflicts):3d} (Pre-existing mappings retained)")
    print(f"  Final Course 2 Links in DB  : {final_c2_mappings:3d}")
    print("-" * 80)

    print("MAPPING COVERAGE BY UNIT:")
    for u_id in sorted(list({t['unit_id'] for t in topic_map.values()})):
        u_topics = [t for t in topic_map.values() if t['unit_id'] == u_id]
        u_name = u_topics[0]['unit_name']
        u_num = u_topics[0]['unit_number']
        count = unit_distribution.get(u_name, 0)
        print(f"  Unit {u_num:2d} ({u_name:<42}): {count:2d} questions ({len(u_topics)} topics)")

    print("-" * 80)
    print(f"TOPICS WITH ZERO MAPPINGS ({len(zero_mapped_topics)} of 45):")
    for zt in zero_mapped_topics:
        print(f"  - [{zt['topic_id']:2d}] Unit {zt['unit_number']}: {zt['topic_name']}")

    if overloaded_topics:
        print("-" * 80)
        print(f"POTENTIALLY OVERLOADED TOPICS (>20 mappings):")
        for t_name, cnt in overloaded_topics:
            print(f"  - {t_name}: {cnt} questions")

    if conflicts:
        print("-" * 80)
        print(f"EXISTING MAPPING CONFLICTS ({len(conflicts)}):")
        for conf in conflicts:
            print(f"  Q[{conf['question_id']}]: Existing='{conf['existing_topic_name']}' vs Proposed='{conf['proposed_topic_name']}' ({conf['confidence']})")

    # 11. Representative Manual-Audit Samples
    if verbose_samples:
        print("\n" + "=" * 80)
        print("REPRESENTATIVE MANUAL-AUDIT SAMPLES")
        print("=" * 80)

        # High confidence samples
        print("\n[A] HIGH-CONFIDENCE SAMPLES (Canonical Phrase Matches):")
        high_samples = [p for p in proposals if p.confidence == "HIGH"][:5]
        for p in high_samples:
            q_row = next(q for q in questions if q["id"] == p.question_id)
            print(f"  Q[{p.question_id}] -> Topic [{p.topic_id}] {p.topic_name} (Unit: {p.unit_name})")
            print(f"     Evidence: {p.evidence} | Method: {p.method}")
            print(f"     Text: {q_row['original_text'].strip()[:100]}")

        # Medium confidence samples
        print("\n[B] MEDIUM-CONFIDENCE SAMPLES (Domain Keyword Matches):")
        med_samples = [p for p in proposals if p.confidence == "MEDIUM"][:5]
        for p in med_samples:
            q_row = next(q for q in questions if q["id"] == p.question_id)
            print(f"  Q[{p.question_id}] -> Topic [{p.topic_id}] {p.topic_name} (Unit: {p.unit_name})")
            print(f"     Evidence: {p.evidence} | Method: {p.method}")
            print(f"     Text: {q_row['original_text'].strip()[:100]}")

        # Ambiguous samples
        print("\n[C] AMBIGUOUS SAMPLES (Intentionally Left Unmapped):")
        amb_samples = [p for p in proposals if p.confidence == "AMBIGUOUS"][:5]
        for p in amb_samples:
            q_row = next(q for q in questions if q["id"] == p.question_id)
            print(f"  Q[{p.question_id}] (Status: {p.confidence}, topic_id={p.topic_id})")
            print(f"     Evidence: {p.evidence}")
            print(f"     Text: {q_row['original_text'].strip()[:100]}")

        # Deliberately unmapped samples
        print("\n[D] DELIBERATELY UNMAPPED SAMPLES (No strong match or generic text):")
        unm_samples = [p for p in proposals if p.confidence == "UNMAPPED"][:5]
        for p in unm_samples:
            q_row = next(q for q in questions if q["id"] == p.question_id)
            print(f"  Q[{p.question_id}] (Status: {p.confidence}, method={p.method})")
            print(f"     Evidence: {p.evidence}")
            print(f"     Text: {q_row['original_text'].strip()[:100]}")

        # Sample from each unit
        print("\n[E] SAMPLES FROM EVERY CHEMISTRY UNIT:")
        seen_units = set()
        for p in proposals:
            if p.unit_id and p.unit_id not in seen_units:
                seen_units.add(p.unit_id)
                q_row = next(q for q in questions if q["id"] == p.question_id)
                print(f"  Unit {topic_map[p.topic_id]['unit_number']} ({p.unit_name}): Q[{p.question_id}] -> Topic [{p.topic_id}] {p.topic_name}")
                print(f"     Evidence: {p.evidence} | Method: {p.method}")
                print(f"     Text: {q_row['original_text'].strip()[:90]}")

    print("\n" + "=" * 80)
    conn.close()

    return {
        "total_questions": total_q,
        "high_count": high_count,
        "medium_count": medium_count,
        "ambiguous_count": ambiguous_count,
        "unmapped_count": unmapped_count,
        "accepted_total": accepted_mapped_total,
        "coverage_pct": coverage_pct,
        "to_insert_count": len(to_insert),
        "inserted_count": inserted_count,
        "preserved_existing_count": len(preserved_existing),
        "conflicts_count": len(conflicts),
        "conflicts": conflicts,
        "zero_mapped_topics_count": len(zero_mapped_topics),
        "overloaded_topics": overloaded_topics,
    }


def main():
    parser = argparse.ArgumentParser(description="Map Chemistry questions to syllabus topics.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Perform dry-run without DB mutations (default)")
    parser.add_argument("--apply", action="store_true", help="Apply additive mappings to local database")
    parser.add_argument("--sync", action="store_true", help="Sync Course 2 mappings with classifier (removes false positives, preserves Calculus)")
    parser.add_argument("--db-path", default=None, help="Path to SQLite database")
    args = parser.parse_args()

    db_path = args.db_path or os.getenv("MAPPER_DB_PATH", os.path.join(BASE_DIR, "production_corpus.db"))
    apply_changes = args.apply and not (args.dry_run and not args.apply)

    # When --apply is passed, dry_run is overridden
    if args.apply:
        apply_changes = True

    run_chemistry_mapping(db_path, apply_changes=apply_changes, sync=args.sync)


if __name__ == "__main__":
    main()
