"""
Surgical promotion script for Courses 3-12 canonical taxonomy and question_topic mappings to Render PostgreSQL.
Promotes ONLY audited first-year courses with strict safety gates:
- Courses 3, 4, 5, 6, 7, 9, 10, 11, 12 (9 courses)
- Course 8 is deliberately preserved in FAMILY INTELLIGENCE mode (0 mappings)
- Courses 1, 2, 13 are verified as invariants (no regression)

Safety Gates:
- Dry-run mode by default with full pre-mutation audit and rollback
- Live mutation requires both --live and --confirm-production-mutation
- Single atomic transaction with automatic rollback on error
- Zero credential logging
- Foreign key & cross-course validation before and after mutation
- Sequence resynchronization
- Invariant assertions on existing courses and student progress
"""

import argparse
import os
import re
import sys
import sqlite3
from typing import Dict, List, Tuple, Any
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

TARGET_COURSES = [3, 4, 5, 6, 7, 9, 10, 11, 12]


def mask_url(url: str) -> str:
    """Mask credentials in database URL for safe logging."""
    if not url:
        return "None"
    if "@" in url:
        prefix, host_part = url.rsplit("@", 1)
        scheme = prefix.split("://")[0]
        return f"{scheme}://***:***@{host_part}"
    return url


def get_pg_url() -> str:
    """Resolve PostgreSQL connection string safely."""
    if os.environ.get("RENDER_DATABASE_URL"):
        return os.environ["RENDER_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg2://")
    smoke_file = os.path.join(BASE_DIR, "scripts", "verify_production_smoke.py")
    with open(smoke_file, "r") as f:
        match = re.search(r'postgresql://[^\"]+', f.read())
        if match:
            return match.group(0).replace("postgresql://", "postgresql+psycopg2://")
    raise ValueError("Could not resolve PostgreSQL connection URL.")


def promote_courses_3_to_12(
    local_db_path: str,
    pg_url: str,
    live_mutation: bool = False,
    confirm_flag: bool = False,
) -> Dict[str, Any]:
    is_dry_run = not (live_mutation and confirm_flag)

    print("=" * 80)
    mode_str = "LIVE PRODUCTION MUTATION" if not is_dry_run else "DRY-RUN (NO REMOTE MUTATIONS)"
    print(f"FIRST-YEAR (COURSES 3-12) TAXONOMY & MAPPINGS PROMOTION [{mode_str}]")
    print("=" * 80)
    print(f"Local Database Path  : {local_db_path}")
    print(f"Target Remote Host   : {mask_url(pg_url)}")
    print(f"Live Mutation Flag   : {live_mutation}")
    print(f"Explicit Confirm Flag: {confirm_flag}")
    print("-" * 80)

    # 1. Load local verified data from SQLite
    if not os.path.exists(local_db_path):
        raise FileNotFoundError(f"Local database not found: {local_db_path}")

    s_conn = sqlite3.connect(local_db_path)
    s_conn.row_factory = sqlite3.Row
    s_cur = s_conn.cursor()

    # Local unit updates (Unit 1 rename) & inserts (Units 2-5)
    local_unit_1_updates = s_cur.execute("""
        SELECT u.id, u.syllabus_id, u.number, u.name
        FROM units u
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id IN (3, 4, 5, 6, 7, 9, 10, 11, 12) AND u.number = 1
        ORDER BY s.course_id
    """).fetchall()

    local_units_to_insert = s_cur.execute("""
        SELECT u.id, u.syllabus_id, u.number, u.name
        FROM units u
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id IN (3, 4, 5, 6, 7, 9, 10, 11, 12) AND u.number > 1
        ORDER BY u.id
    """).fetchall()

    # Local topics
    local_topics_to_insert = s_cur.execute("""
        SELECT t.id, t.unit_id, t.name, s.course_id
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id IN (3, 4, 5, 6, 7, 9, 10, 11, 12)
        ORDER BY t.id
    """).fetchall()

    # Local mappings for target courses
    local_mappings_rows = s_cur.execute("""
        SELECT 
            qt.question_id, 
            qt.topic_id, 
            e.course_id,
            t.name as topic_name
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        WHERE e.course_id IN (3, 4, 5, 6, 7, 9, 10, 11, 12)
        ORDER BY e.course_id, qt.question_id
    """).fetchall()

    local_mappings_by_course = {}
    for cid in TARGET_COURSES:
        local_mappings_by_course[cid] = [r for r in local_mappings_rows if r["course_id"] == cid]

    total_local_target_mappings = len(local_mappings_rows)

    # Invariants from local SQLite
    loc_c1 = s_cur.execute("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=1").fetchone()[0]
    loc_c2 = s_cur.execute("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=2").fetchone()[0]
    loc_c8 = s_cur.execute("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=8").fetchone()[0]
    loc_c13 = s_cur.execute("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=13").fetchone()[0]

    s_conn.close()

    print(f"Local Unit 1 Renames          : {len(local_unit_1_updates)}")
    print(f"Local Units 2-5 to Insert     : {len(local_units_to_insert)} (IDs 50..85)")
    print(f"Local Topics to Insert        : {len(local_topics_to_insert)} (IDs 100..279)")
    print(f"Local Mappings to Promote     : {total_local_target_mappings}")
    for cid in TARGET_COURSES:
        print(f"  Course {cid:2d} target mappings: {len(local_mappings_by_course[cid])}")
    print(f"Local Course 8 (FL) Mappings  : {loc_c8} (Truthful Family Mode)")
    print("-" * 80)

    # 2. Connect to remote PostgreSQL
    engine = create_engine(pg_url, pool_pre_ping=True)

    with engine.connect() as conn:
        # 3. Read-only Baseline on PostgreSQL
        prod_total_qt = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        prod_c1_cnt = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id = q.id JOIN sections s ON q.section_id = s.id JOIN exams e ON s.exam_id = e.id WHERE e.course_id = 1")).fetchone()[0]
        prod_c2_cnt = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id = q.id JOIN sections s ON q.section_id = s.id JOIN exams e ON s.exam_id = e.id WHERE e.course_id = 2")).fetchone()[0]
        prod_c8_cnt = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id = q.id JOIN sections s ON q.section_id = s.id JOIN exams e ON s.exam_id = e.id WHERE e.course_id = 8")).fetchone()[0]
        prod_c13_cnt = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id = q.id JOIN sections s ON q.section_id = s.id JOIN exams e ON s.exam_id = e.id WHERE e.course_id = 13")).fetchone()[0]

        student_progress_cnt = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        student_resource_cnt = conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]
        curriculum_cnt = conn.execute(text("SELECT count(*) FROM curriculum_mappings")).fetchone()[0]

        print("REMOTE POSTGRESQL BASELINE AUDIT:")
        print(f"  Total question_topic rows    : {prod_total_qt}")
        print(f"  Calculus (Course 1) mappings : {prod_c1_cnt}")
        print(f"  Chemistry (Course 2) mappings: {prod_c2_cnt}")
        print(f"  SPCM (Course 13) mappings    : {prod_c13_cnt}")
        print(f"  Foreign Lang (Course 8) maps : {prod_c8_cnt}")
        print(f"  Student Topic Progress rows  : {student_progress_cnt}")
        print(f"  Student Resource Progress    : {student_resource_cnt}")
        print(f"  Curriculum Mappings rows     : {curriculum_cnt}")
        print("-" * 80)

        # Baseline assertions
        assert prod_c1_cnt == 17, f"C1 baseline violation: {prod_c1_cnt} != 17"
        assert prod_c2_cnt == 192, f"C2 baseline violation: {prod_c2_cnt} != 192"
        assert prod_c13_cnt == 620, f"C13 baseline violation: {prod_c13_cnt} != 620"
        assert prod_c8_cnt == 0, f"C8 baseline violation: {prod_c8_cnt} != 0"
        assert prod_total_qt == 829, f"Total mappings baseline violation: {prod_total_qt} != 829"

        # 4. Atomic Transaction
        conn.rollback()  # Clear prior read transaction
        with conn.begin() as trans:
            try:
                # Step A: Update Unit 1 names
                print("Step A: Updating Unit 1 titles in PostgreSQL...")
                for u in local_unit_1_updates:
                    conn.execute(text("""
                        UPDATE units 
                        SET name = :name 
                        WHERE syllabus_id = :syl_id AND number = 1
                    """), {"name": u["name"], "syl_id": u["syllabus_id"]})
                print(f"  Updated {len(local_unit_1_updates)} Unit 1 titles.")

                # Step B: Insert Units 2-5
                print("Step B: Inserting Units 2-5 in PostgreSQL...")
                for u in local_units_to_insert:
                    conn.execute(text("""
                        INSERT INTO units (id, syllabus_id, number, name)
                        VALUES (:id, :syl_id, :number, :name)
                        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """), {"id": u["id"], "syl_id": u["syllabus_id"], "number": u["number"], "name": u["name"]})
                print(f"  Upserted {len(local_units_to_insert)} Units (IDs 50..85).")

                # Step C: Insert Topics
                print("Step C: Inserting 180 canonical topics in PostgreSQL...")
                for t in local_topics_to_insert:
                    conn.execute(text("""
                        INSERT INTO topics (id, unit_id, name)
                        VALUES (:id, :unit_id, :name)
                        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                    """), {"id": t["id"], "unit_id": t["unit_id"], "name": t["name"]})
                print(f"  Upserted {len(local_topics_to_insert)} Topics (IDs 100..279).")

                # Step D: Sync PostgreSQL sequences
                conn.execute(text("SELECT setval('units_id_seq', (SELECT GREATEST(MAX(id), 85) FROM units))"))
                conn.execute(text("SELECT setval('topics_id_seq', (SELECT GREATEST(MAX(id), 279) FROM topics))"))
                print("  Synchronized units_id_seq and topics_id_seq.")

                # Step E: Verify Foreign Keys & Ownership of Questions & Topics
                print("Step E: Verifying Question & Topic ownership...")
                target_q_ids = [r["question_id"] for r in local_mappings_rows]
                target_t_ids = list(set(r["topic_id"] for r in local_mappings_rows))

                # Questions check
                q_ownership = conn.execute(text("""
                    SELECT q.id, e.course_id
                    FROM questions q
                    JOIN sections s ON q.section_id = s.id
                    JOIN exams e ON s.exam_id = e.id
                    WHERE q.id = ANY(:q_ids)
                """), {"q_ids": target_q_ids}).fetchall()
                q_course_map = {r[0]: r[1] for r in q_ownership}

                missing_questions = set(target_q_ids) - set(q_course_map.keys())
                if missing_questions:
                    raise ValueError(f"Integrity error: {len(missing_questions)} questions missing in PG!")

                # Topics check
                t_ownership = conn.execute(text("""
                    SELECT t.id, s.course_id
                    FROM topics t
                    JOIN units u ON t.unit_id = u.id
                    JOIN syllabuses s ON u.syllabus_id = s.id
                    WHERE t.id = ANY(:t_ids)
                """), {"t_ids": target_t_ids}).fetchall()
                t_course_map = {r[0]: r[1] for r in t_ownership}

                missing_topics = set(target_t_ids) - set(t_course_map.keys())
                if missing_topics:
                    raise ValueError(f"Integrity error: {len(missing_topics)} topics missing in PG!")

                # Cross-course check on local proposed tuples
                for r in local_mappings_rows:
                    qid = r["question_id"]
                    tid = r["topic_id"]
                    q_course = q_course_map[qid]
                    t_course = t_course_map[tid]
                    if q_course != t_course:
                        raise ValueError(f"Cross-course mapping attempt: Q{qid} (course {q_course}) -> T{tid} (course {t_course})")

                print(f"  VERIFICATION PASSED: All {len(target_q_ids)} questions and {len(target_t_ids)} topics belong to matching target courses.")

                # Step F: Insert question_topic mappings
                print(f"Step F: Inserting {total_local_target_mappings} question_topic mappings...")
                insert_payload = [{"qid": r["question_id"], "tid": r["topic_id"]} for r in local_mappings_rows]
                
                # Execute batch insert with ON CONFLICT DO NOTHING
                conn.execute(
                    text("INSERT INTO question_topic (question_id, topic_id) VALUES (:qid, :tid) ON CONFLICT DO NOTHING"),
                    insert_payload
                )
                print(f"  Inserted {len(insert_payload)} mapping rows.")

                # Step G: In-transaction verification
                tx_total = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
                tx_c1 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=1")).fetchone()[0]
                tx_c2 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=2")).fetchone()[0]
                tx_c8 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=8")).fetchone()[0]
                tx_c13 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=13")).fetchone()[0]
                tx_cross = conn.execute(text("""
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

                print("-" * 80)
                print("IN-TRANSACTION AUDIT:")
                print(f"  Calculus (C1) mappings     : {tx_c1} (Must be 17)")
                print(f"  Chemistry (C2) mappings    : {tx_c2} (Must be 192)")
                print(f"  SPCM (C13) mappings        : {tx_c13} (Must be 620)")
                print(f"  Foreign Lang (C8) mappings : {tx_c8} (Must be 0)")
                print(f"  Cross-Course Violations    : {tx_cross} (Must be 0)")
                print(f"  Total question_topic Rows  : {tx_total} (Must be 1687)")
                print("-" * 80)

                assert tx_c1 == 17, f"C1 mapping invariant broken: {tx_c1}"
                assert tx_c2 == 192, f"C2 mapping invariant broken: {tx_c2}"
                assert tx_c13 == 620, f"C13 mapping invariant broken: {tx_c13}"
                assert tx_c8 == 0, f"C8 mapping invariant broken: {tx_c8}"
                assert tx_cross == 0, f"Cross-course mappings detected: {tx_cross}"
                assert tx_total == 1687, f"Total mappings mismatch: {tx_total} != 1687"

                for cid in TARGET_COURSES:
                    tx_c_map = conn.execute(text("""
                        SELECT count(DISTINCT qt.question_id)
                        FROM question_topic qt
                        JOIN questions q ON qt.question_id=q.id
                        JOIN sections s ON q.section_id=s.id
                        JOIN exams e ON s.exam_id=e.id
                        WHERE e.course_id = :cid
                    """), {"cid": cid}).fetchone()[0]
                    expected_c_map = len(local_mappings_by_course[cid])
                    print(f"  Course {cid:2d} promoted count: {tx_c_map} (Expected: {expected_c_map})")
                    assert tx_c_map == expected_c_map, f"Course {cid} mapping count mismatch: {tx_c_map} != {expected_c_map}"

                if not is_dry_run:
                    print("\nCONFIRMATION RECEIVED. COMMITTING TRANSACTION TO PRODUCTION POSTGRESQL...")
                    # Transaction commits automatically at end of context block
                else:
                    print("\nDRY-RUN MODE ACTIVE: Triggering explicit transaction ROLLBACK.")
                    trans.rollback()

            except Exception as e:
                trans.rollback()
                print(f"ERROR: Transaction failed and rolled back cleanly. Reason: {e}")
                raise

        # 5. Post-Execution Audit
        print("=" * 80)
        print("POST-EXECUTION DATABASE STATE AUDIT:")
        print("=" * 80)
        post_total = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        post_c1 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=1")).fetchone()[0]
        post_c2 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=2")).fetchone()[0]
        post_c8 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=8")).fetchone()[0]
        post_c13 = conn.execute(text("SELECT count(*) FROM question_topic qt JOIN questions q ON qt.question_id=q.id JOIN sections s ON q.section_id=s.id JOIN exams e ON s.exam_id=e.id WHERE e.course_id=13")).fetchone()[0]
        post_stp = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        post_srp = conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]
        post_curr = conn.execute(text("SELECT count(*) FROM curriculum_mappings")).fetchone()[0]

        print(f"  Calculus (C1) mappings     : {post_c1}")
        print(f"  Chemistry (C2) mappings    : {post_c2}")
        print(f"  SPCM (C13) mappings        : {post_c13}")
        print(f"  Foreign Lang (C8) mappings : {post_c8}")
        print(f"  Total question_topic rows  : {post_total}")
        print(f"  student_topic_progress     : {post_stp} (Invariant: {post_stp == student_progress_cnt})")
        print(f"  student_resource_progress  : {post_srp} (Invariant: {post_srp == student_resource_cnt})")
        print(f"  curriculum_mappings        : {post_curr} (Invariant: {post_curr == curriculum_cnt})")

        assert post_stp == student_progress_cnt, "Student topic progress was mutated!"
        assert post_srp == student_resource_cnt, "Student resource progress was mutated!"
        assert post_curr == curriculum_cnt, "Curriculum mappings were mutated!"

        if is_dry_run:
            assert post_total == 829, f"Dry-run leaked mappings into prod: {post_total}"
            print("\nDRY-RUN ROLLBACK SUCCESSFUL: Database is exactly in pre-run state.")
        else:
            assert post_total == 1687, f"Live commit total mappings unexpected: {post_total}"
            print("\nLIVE PROMOTION SUCCESSFUL: All 858 mappings committed cleanly. Total is 1,687.")

    return {
        "is_dry_run": is_dry_run,
        "post_total": post_total,
        "post_c1": post_c1,
        "post_c2": post_c2,
        "post_c8": post_c8,
        "post_c13": post_c13,
    }


def main():
    parser = argparse.ArgumentParser(description="Promote Courses 3-12 taxonomy and mappings to PostgreSQL.")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Perform dry-run with rollback")
    parser.add_argument("--live", action="store_true", default=False, help="Request live mutation mode (requires --confirm-production-mutation)")
    parser.add_argument("--confirm-production-mutation", action="store_true", default=False, help="Explicit confirmation gate to mutate production")
    parser.add_argument("--local-db", default=None, help="Path to local SQLite database (default: production_corpus.db)")
    parser.add_argument("--pg-url", default=None, help="PostgreSQL connection string")
    args = parser.parse_args()

    local_db = args.local_db or os.path.join(BASE_DIR, "production_corpus.db")
    pg_url = args.pg_url or get_pg_url()

    live_mutation = args.live and args.confirm_production_mutation
    if args.live and not args.confirm_production_mutation:
        print("REFUSING MUTATION: --live was specified without --confirm-production-mutation. Running in dry-run mode.")
        live_mutation = False

    promote_courses_3_to_12(
        local_db_path=local_db,
        pg_url=pg_url,
        live_mutation=live_mutation,
        confirm_flag=args.confirm_production_mutation,
    )


if __name__ == "__main__":
    main()
