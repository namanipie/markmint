"""
Dedicated surgical promotion script for SPCM (Course 13) question_topic mappings to Render PostgreSQL.
Promotes ONLY audited Course 13 mappings with strict safety gates.

Requirements:
- dry-run first
- explicit production confirmation required for live mutation (--live --confirm-production-mutation)
- insert only missing SPCM mappings
- never delete existing mappings
- never overwrite conflicts
- verify every question belongs to Course 13
- verify every topic belongs to Course 13
- one transaction
- rollback on failure
- no credential printing
"""

import argparse
import os
import sys
import sqlite3
from typing import Dict, List, Tuple, Any
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def mask_url(url: str) -> str:
    """Mask credentials in database URL for safe logging."""
    if not url:
        return "None"
    if "@" in url:
        prefix, host_part = url.rsplit("@", 1)
        scheme = prefix.split("://")[0]
        return f"{scheme}://***:***@{host_part}"
    return url


def promote_spcm_mappings(
    local_db_path: str,
    pg_url: str,
    live_mutation: bool = False,
    confirm_flag: bool = False,
) -> Dict[str, Any]:
    # 0. Safety gate on live mutation
    is_dry_run = not (live_mutation and confirm_flag)

    print("=" * 80)
    mode_str = "LIVE PRODUCTION MUTATION" if not is_dry_run else "DRY-RUN (NO REMOTE MUTATIONS)"
    print(f"SPCM MAPPING PROMOTION GATE [{mode_str}]")
    print("=" * 80)
    print(f"Local Database Path  : {local_db_path}")
    print(f"Target Remote Host   : {mask_url(pg_url)}")
    print(f"Live Mutation Flag   : {live_mutation}")
    print(f"Explicit Confirm Flag: {confirm_flag}")
    print("-" * 80)

    # 1. Load local audited SPCM mappings
    if not os.path.exists(local_db_path):
        raise FileNotFoundError(f"Local database not found at {local_db_path}")

    s_conn = sqlite3.connect(local_db_path)
    s_conn.row_factory = sqlite3.Row
    s_cur = s_conn.cursor()

    local_rows = s_cur.execute("""
        SELECT 
            qt.question_id, 
            qt.topic_id, 
            t.name as topic_name, 
            u.id as unit_id, 
            u.number as unit_number, 
            u.name as unit_name
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        JOIN units u ON t.unit_id = u.id
        WHERE e.course_id = 13
        ORDER BY qt.question_id
    """).fetchall()

    local_spcm_count = len(local_rows)
    local_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in local_rows}

    # Also check local Calculus & Chemistry mappings for invariant tracking
    local_calculus_count = s_cur.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 1
    """).fetchone()[0]

    local_chemistry_count = s_cur.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """).fetchone()[0]

    # Load local SPCM units, topics, concepts to ensure PG has identical taxonomy
    local_spcm_units = s_cur.execute("""
        SELECT u.id, u.syllabus_id, u.number, u.name
        FROM units u
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id = 13 AND u.number IN (1, 2, 3, 4, 5)
        ORDER BY u.number
    """).fetchall()

    local_spcm_topics = s_cur.execute("""
        SELECT t.id, t.unit_id, t.name
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id = 13
        ORDER BY t.id
    """).fetchall()

    local_spcm_concepts = s_cur.execute("""
        SELECT c.id, c.canonical_name, c.description, c.subject, c.status, c.unit_id
        FROM concepts c
        WHERE c.subject LIKE '%Semiconductor%'
        ORDER BY c.id
    """).fetchall()

    s_conn.close()

    print(f"Local SPCM Mappings Count      : {local_spcm_count}")
    print(f"Local Calculus Mappings Count  : {local_calculus_count} (Must be preserved invariant)")
    print(f"Local Chemistry Mappings Count : {local_chemistry_count} (Must be preserved invariant)")
    print("-" * 80)

    # 2. Connect to PostgreSQL
    clean_pg_url = pg_url.replace("postgresql://", "postgresql+psycopg2://")
    engine = create_engine(clean_pg_url, pool_pre_ping=True)

    with engine.connect() as conn:
        # 3. Read-only Baseline on PostgreSQL
        prod_total_qt = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]

        prod_c1_cnt = conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 1
        """)).fetchone()[0]

        prod_c2_cnt = conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        """)).fetchone()[0]

        prod_c13_cnt = conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 13
        """)).fetchone()[0]

        student_progress_cnt = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        student_resource_cnt = conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]

        print("REMOTE POSTGRESQL BASELINE AUDIT:")
        print(f"  Total question_topic rows    : {prod_total_qt}")
        print(f"  Calculus (Course 1) mappings : {prod_c1_cnt}")
        print(f"  Chemistry (Course 2) mappings: {prod_c2_cnt}")
        print(f"  SPCM (Course 13) mappings    : {prod_c13_cnt}")
        print(f"  Student Topic Progress rows  : {student_progress_cnt}")
        print(f"  Student Resource Progress    : {student_resource_cnt}")
        print("-" * 80)

        # Existing PG Course 13 mappings
        existing_pg_c13_rows = conn.execute(text("""
            SELECT qt.question_id, qt.topic_id
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 13
        """)).fetchall()
        existing_pg_c13_map = {r[0]: r[1] for r in existing_pg_c13_rows}

        # 4. Check & Prepare SPCM Taxonomy in PostgreSQL
        # Ensure Syllabus 13 has units 45..49, topics 73..99, and concepts 73..99
        pg_c13_topics_cnt = conn.execute(text("""
            SELECT count(t.id)
            FROM topics t
            JOIN units u ON t.unit_id = u.id
            JOIN syllabuses s ON u.syllabus_id = s.id
            WHERE s.course_id = 13
        """)).fetchone()[0]

        print(f"Remote SPCM Topics Count: {pg_c13_topics_cnt}")

        # 8. Single Transaction Execution
        conn.rollback()  # Reset any autobegun read-only transaction from prior SELECT statements
        with conn.begin() as trans:
            try:
                # Seed SPCM taxonomy if missing
                if pg_c13_topics_cnt == 0:
                    print("SPCM canonical taxonomy missing on remote PG. Seeding 5 units, 27 topics, 27 concepts...")
                    
                    # Check Syllabus ID for Course 13
                    syl_id = conn.execute(text("SELECT id FROM syllabuses WHERE course_id = 13")).fetchone()[0]

                    # Insert 5 canonical units
                    for u in local_spcm_units:
                        conn.execute(text("""
                            INSERT INTO units (id, syllabus_id, number, name)
                            VALUES (:id, :syl_id, :number, :name)
                            ON CONFLICT (id) DO NOTHING
                        """), {"id": u["id"], "syl_id": syl_id, "number": u["number"], "name": u["name"]})

                    # Insert 27 canonical topics
                    for t in local_spcm_topics:
                        conn.execute(text("""
                            INSERT INTO topics (id, unit_id, name)
                            VALUES (:id, :unit_id, :name)
                            ON CONFLICT (id) DO NOTHING
                        """), {"id": t["id"], "unit_id": t["unit_id"], "name": t["name"]})

                    # Insert 27 canonical concepts
                    for c in local_spcm_concepts:
                        conn.execute(text("""
                            INSERT INTO concepts (id, canonical_name, description, subject, status, unit_id)
                            VALUES (:id, :name, :desc, :subject, :status, :unit_id)
                            ON CONFLICT (id) DO NOTHING
                        """), {"id": c["id"], "name": c["canonical_name"], "desc": c["description"], "subject": c["subject"], "status": c["status"], "unit_id": c["unit_id"]})

                    # Sync sequences
                    conn.execute(text("SELECT setval('units_id_seq', (SELECT GREATEST(MAX(id), 49) FROM units))"))
                    conn.execute(text("SELECT setval('topics_id_seq', (SELECT GREATEST(MAX(id), 99) FROM topics))"))
                    conn.execute(text("SELECT setval('concepts_id_seq', (SELECT GREATEST(MAX(id), 99) FROM concepts))"))
                    print("SPCM canonical taxonomy successfully seeded into transaction context.")

                # 5. Verify question ownership (every question belongs to Course 13)
                q_ids = list(local_mappings.keys())
                q_rows = conn.execute(text("""
                    SELECT q.id, e.course_id
                    FROM questions q
                    JOIN sections s ON q.section_id = s.id
                    JOIN exams e ON s.exam_id = e.id
                    WHERE q.id = ANY(:q_ids)
                """), {"q_ids": q_ids}).fetchall()

                pg_question_course = {r[0]: r[1] for r in q_rows}
                missing_q = set(q_ids) - set(pg_question_course.keys())
                wrong_course_q = {qid: cid for qid, cid in pg_question_course.items() if cid != 13}

                if missing_q:
                    raise ValueError(f"Integrity Violation: {len(missing_q)} candidate questions do not exist in PG: {sorted(list(missing_q))[:5]}")
                if wrong_course_q:
                    raise ValueError(f"Integrity Violation: Candidate questions do not belong to Course 13: {wrong_course_q}")

                print(f"VERIFICATION PASSED: All {len(q_ids)} candidate questions exist and belong to Course 13.")

                # 6. Verify topic ownership (every topic belongs to Course 13)
                topic_ids = list(set(local_mappings.values()))
                t_rows = conn.execute(text("""
                    SELECT t.id, s.course_id
                    FROM topics t
                    JOIN units u ON t.unit_id = u.id
                    JOIN syllabuses s ON u.syllabus_id = s.id
                    WHERE t.id = ANY(:t_ids)
                """), {"t_ids": topic_ids}).fetchall()

                pg_topic_course = {r[0]: r[1] for r in t_rows}
                missing_t = set(topic_ids) - set(pg_topic_course.keys())
                wrong_course_t = {tid: cid for tid, cid in pg_topic_course.items() if cid != 13}

                if missing_t:
                    raise ValueError(f"Integrity Violation: {len(missing_t)} candidate topics do not exist in PG: {sorted(list(missing_t))}")
                if wrong_course_t:
                    raise ValueError(f"Integrity Violation: Candidate topics do not belong to Course 13: {wrong_course_t}")

                print(f"VERIFICATION PASSED: All {len(topic_ids)} candidate topics exist and belong to Course 13.")

                # 7. Reconcile with existing mappings
                identical_existing: List[Tuple[int, int]] = []
                conflicts: List[Dict[str, Any]] = []
                to_insert: List[Tuple[int, int]] = []

                for q_id, target_t_id in local_mappings.items():
                    if q_id in existing_pg_c13_map:
                        current_t_id = existing_pg_c13_map[q_id]
                        if current_t_id == target_t_id:
                            identical_existing.append((q_id, target_t_id))
                        else:
                            conflicts.append({
                                "question_id": q_id,
                                "existing_topic_id": current_t_id,
                                "target_topic_id": target_t_id,
                                "action": "PRESERVED_EXISTING"
                            })
                    else:
                        to_insert.append((q_id, target_t_id))

                expected_final_c13 = prod_c13_cnt + len(to_insert)
                expected_final_total = prod_total_qt + len(to_insert)

                print("-" * 80)
                print("PRE-MUTATION RECONCILIATION SUMMARY:")
                print(f"  Local Audited SPCM Mappings  : {local_spcm_count}")
                print(f"  Production SPCM Mappings     : {prod_c13_cnt}")
                print(f"  Identical Existing Rows      : {len(identical_existing)}")
                print(f"  Conflicts (Will be PRESERVED): {len(conflicts)}")
                print(f"  Rows to INSERT               : {len(to_insert)}")
                print(f"  Expected Final SPCM Mappings : {expected_final_c13}")
                print(f"  Expected Final Total Rows    : {expected_final_total}")
                print("-" * 80)

                if conflicts:
                    print("CONFLICT AUDIT:")
                    for cf in conflicts[:5]:
                        print(f"    Q {cf['question_id']}: PG has topic {cf['existing_topic_id']}, candidate has {cf['target_topic_id']} -> PRESERVING EXISTING")

                # 8. Execution Gate
                if not is_dry_run:
                    print(f"EXECUTING LIVE PROMOTION OF {len(to_insert)} SPCM MAPPINGS...")
                    if to_insert:
                        insert_tuples = [{"qid": qid, "tid": tid} for qid, tid in to_insert]
                        conn.execute(
                            text("INSERT INTO question_topic (question_id, topic_id) VALUES (:qid, :tid)"),
                            insert_tuples
                        )
                    
                    print("TRANSACTION COMMITTED CLEANLY.")
                else:
                    print("DRY-RUN COMPLETE: Performing explicit transaction ROLLBACK (0 mutations committed).")
                    trans.rollback()

            except Exception as e:
                trans.rollback()
                print(f"ERROR: Transaction aborted and rolled back. Exception: {e}")
                raise

        # 9. Post-Mutation / Post-Rollback Auditing
        post_total = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        post_c1 = conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 1
        """)).fetchone()[0]
        post_c2 = conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        """)).fetchone()[0]
        post_c13 = conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 13
        """)).fetchone()[0]

        post_student_progress = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        post_resource_progress = conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]

        print("-" * 80)
        print("POST-PROMOTION AUDIT:")
        print(f"  Calculus (Course 1) Mappings : {post_c1} (Expected: {prod_c1_cnt} | Invariant: {post_c1 == prod_c1_cnt})")
        print(f"  Chemistry (Course 2) Mappings: {post_c2} (Expected: {prod_c2_cnt} | Invariant: {post_c2 == prod_c2_cnt})")
        print(f"  SPCM (Course 13) Mappings    : {post_c13} (Expected: {expected_final_c13 if not is_dry_run else prod_c13_cnt})")
        print(f"  Total question_topic Rows    : {post_total} (Expected: {expected_final_total if not is_dry_run else prod_total_qt})")
        print(f"  Student Topic Progress Rows  : {post_student_progress} (Untouched: {post_student_progress == student_progress_cnt})")
        print(f"  Student Resource Progress    : {post_resource_progress} (Untouched: {post_resource_progress == student_resource_cnt})")

        # Cross-course check
        cross_course = conn.execute(text("""
            SELECT count(*)
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            JOIN topics t ON qt.topic_id = t.id
            JOIN units u ON t.unit_id = u.id
            JOIN syllabuses syl ON u.syllabus_id = syl.id
            WHERE e.course_id != syl.course_id
        """)).fetchone()[0]
        print(f"  Cross-Course Violations      : {cross_course} (Must be 0)")
        assert cross_course == 0, f"Cross-course violations detected: {cross_course}"

        if is_dry_run:
            assert post_c1 == prod_c1_cnt, f"Dry-run baseline leaked C1: {post_c1} != {prod_c1_cnt}"
            assert post_c2 == prod_c2_cnt, f"Dry-run baseline leaked C2: {post_c2} != {prod_c2_cnt}"
            assert post_c13 == prod_c13_cnt, f"Dry-run baseline leaked C13: {post_c13} != {prod_c13_cnt}"
            assert post_total == prod_total_qt, f"Dry-run baseline leaked Total: {post_total} != {prod_total_qt}"
            print("DRY-RUN ROLLBACK VERIFIED: Database returned exactly to baseline.")

    return {
        "is_dry_run": is_dry_run,
        "prod_spcm_count_before": prod_c13_cnt,
        "prod_calculus_count_before": prod_c1_cnt,
        "prod_chemistry_count_before": prod_c2_cnt,
        "local_spcm_count": local_spcm_count,
        "identical_existing_count": len(identical_existing),
        "conflicts_count": len(conflicts),
        "rows_to_insert": len(to_insert),
        "expected_final_spcm": expected_final_c13,
        "expected_final_total": expected_final_total,
        "post_spcm_count": post_c13,
        "post_calculus_count": post_c1,
        "post_chemistry_count": post_c2,
        "post_total_count": post_total,
    }


def main():
    parser = argparse.ArgumentParser(description="Promote audited SPCM question_topic mappings to PostgreSQL.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Perform dry-run with rollback (default)")
    parser.add_argument("--live", action="store_true", help="Request live mutation mode (requires --confirm-production-mutation)")
    parser.add_argument("--confirm-production-mutation", action="store_true", help="Explicit confirmation gate to mutate production")
    parser.add_argument("--local-db", default=None, help="Path to local SQLite database (default: production_corpus.db)")
    parser.add_argument("--pg-url", default=None, help="PostgreSQL connection string (default: $env:RENDER_DATABASE_URL)")
    args = parser.parse_args()

    local_db = args.local_db or os.path.join(BASE_DIR, "production_corpus.db")
    pg_url = args.pg_url or os.environ.get("RENDER_DATABASE_URL")

    if not pg_url:
        print("ERROR: RENDER_DATABASE_URL environment variable is not set and --pg-url was not provided.")
        sys.exit(1)

    live_mutation = args.live and args.confirm_production_mutation
    if args.live and not args.confirm_production_mutation:
        print("REFUSING MUTATION: --live was specified without --confirm-production-mutation. Running in dry-run mode.")
        live_mutation = False

    promote_spcm_mappings(
        local_db_path=local_db,
        pg_url=pg_url,
        live_mutation=live_mutation,
        confirm_flag=args.confirm_production_mutation,
    )


if __name__ == "__main__":
    main()
