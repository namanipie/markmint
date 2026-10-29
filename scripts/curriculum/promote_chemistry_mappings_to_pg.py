"""
Dedicated surgical promotion script for Chemistry question_topic mappings to Render PostgreSQL.
Promotes ONLY audited Course 2 mappings with strict safety gates.

Requirements:
- dry-run first
- explicit production confirmation required for live mutation (--confirm-production-mutation)
- INSERT ONLY missing Chemistry mappings
- never delete existing mappings
- never overwrite conflicts
- verify question belongs to course_id=2
- verify topic belongs to Chemistry
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


def promote_chemistry_mappings(
    local_db_path: str,
    pg_url: str,
    live_mutation: bool = False,
    confirm_flag: bool = False,
) -> Dict[str, Any]:
    # 0. Safety gate on live mutation
    is_dry_run = not (live_mutation and confirm_flag)

    print("=" * 80)
    mode_str = "LIVE PRODUCTION MUTATION" if not is_dry_run else "DRY-RUN (NO REMOTE MUTATIONS)"
    print(f"CHEMISTRY MAPPING PROMOTION GATE [{mode_str}]")
    print("=" * 80)
    print(f"Local Database Path  : {local_db_path}")
    print(f"Target Remote Host   : {mask_url(pg_url)}")
    print(f"Live Mutation Flag   : {live_mutation}")
    print(f"Explicit Confirm Flag: {confirm_flag}")
    print("-" * 80)

    # 1. Load local audited Chemistry mappings
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
        WHERE e.course_id = 2
        ORDER BY qt.question_id
    """).fetchall()

    local_chemistry_count = len(local_rows)
    local_mappings: Dict[int, int] = {r["question_id"]: r["topic_id"] for r in local_rows}

    # Also check local Calculus mappings
    local_calculus_count = s_cur.execute("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 1
    """).fetchone()[0]

    s_conn.close()

    print(f"Local Chemistry Mappings Count : {local_chemistry_count}")
    print(f"Local Calculus Mappings Count  : {local_calculus_count} (Must be preserved invariant)")
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

        prod_other_cnt = prod_total_qt - prod_c1_cnt - prod_c2_cnt

        student_progress_cnt = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        student_resource_cnt = conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]

        # Existing PG Course 2 mappings
        existing_pg_c2_rows = conn.execute(text("""
            SELECT qt.question_id, qt.topic_id
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        """)).fetchall()
        existing_pg_c2_map = {r[0]: r[1] for r in existing_pg_c2_rows}

        # 4. Verify question ownership (every proposed question must exist and belong to course_id=2)
        q_ids = list(local_mappings.keys())
        q_rows = conn.execute(text("""
            SELECT q.id, e.course_id
            FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE q.id = ANY(:qids)
        """), {"qids": q_ids}).fetchall()
        pg_question_map = {r[0]: r[1] for r in q_rows}

        missing_q = set(q_ids) - set(pg_question_map.keys())
        if missing_q:
            raise ValueError(f"SAFETY ERROR: {len(missing_q)} local questions missing from PG: {list(missing_q)[:5]}")

        wrong_course_q = [qid for qid, cid in pg_question_map.items() if cid != 2]
        if wrong_course_q:
            raise ValueError(f"SAFETY ERROR: Questions do not belong to course_id=2 in PG: {wrong_course_q[:5]}")

        # 5. Verify topic ownership (every proposed topic must exist and belong to Chemistry syllabus)
        t_ids = list(set(local_mappings.values()))
        t_rows = conn.execute(text("""
            SELECT t.id, s.course_id
            FROM topics t
            JOIN units u ON t.unit_id = u.id
            JOIN syllabuses s ON u.syllabus_id = s.id
            WHERE t.id = ANY(:tids)
        """), {"tids": t_ids}).fetchall()
        pg_topic_map = {r[0]: r[1] for r in t_rows}

        missing_t = set(t_ids) - set(pg_topic_map.keys())
        if missing_t:
            raise ValueError(f"SAFETY ERROR: {len(missing_t)} local topics missing from PG: {list(missing_t)[:5]}")

        wrong_course_t = [tid for tid, cid in pg_topic_map.items() if cid != 2]
        if wrong_course_t:
            raise ValueError(f"SAFETY ERROR: Topics do not belong to Chemistry in PG: {wrong_course_t[:5]}")

        # 6. Evaluate additions, identical, and conflicts
        to_insert: List[Tuple[int, int]] = []
        identical_existing: List[Tuple[int, int]] = []
        conflicts: List[Dict[str, Any]] = []

        for q_id, proposed_t_id in local_mappings.items():
            if q_id not in existing_pg_c2_map:
                to_insert.append((q_id, proposed_t_id))
            else:
                existing_t_id = existing_pg_c2_map[q_id]
                if existing_t_id == proposed_t_id:
                    identical_existing.append((q_id, proposed_t_id))
                else:
                    conflicts.append({
                        "question_id": q_id,
                        "existing_topic_id": existing_t_id,
                        "proposed_topic_id": proposed_t_id,
                    })

        expected_final_c2 = prod_c2_cnt + len(to_insert)
        expected_final_total = prod_total_qt + len(to_insert)

        # 7. Print pre-mutation audit report
        print("PRE-MUTATION REMOTE AUDIT:")
        print(f"  Production Chemistry Mapping Count : {prod_c2_cnt}")
        print(f"  Production Calculus Mapping Count  : {prod_c1_cnt} (Must remain exactly 17)")
        print(f"  Production Other Courses Mapping   : {prod_other_cnt} (Must remain 0)")
        print(f"  Production Total question_topic    : {prod_total_qt}")
        print(f"  Local Audited Chemistry Mappings   : {local_chemistry_count}")
        print(f"  Identical Existing Rows in PG      : {len(identical_existing)}")
        print(f"  Conflicts in PG                    : {len(conflicts)} (Will NOT be overwritten)")
        print(f"  Rows to Insert                     : {len(to_insert)}")
        print(f"  Expected Final Chemistry in PG     : {expected_final_c2}")
        print(f"  Expected Final Total in PG         : {expected_final_total}")
        print(f"  Production student_topic_progress  : {student_progress_cnt} (Must remain untouched)")
        print(f"  Production student_resource_prog   : {student_resource_cnt} (Must remain untouched)")
        print("-" * 80)

        if conflicts:
            print(f"WARNING: {len(conflicts)} conflicts detected:")
            for conf in conflicts[:5]:
                print(f"  Q[{conf['question_id']}]: existing={conf['existing_topic_id']} vs proposed={conf['proposed_topic_id']}")

        # 8. Single Transaction Execution
        conn.rollback()  # Reset any autobegun read-only transaction from prior SELECT statements
        with conn.begin() as trans:
            inserted_count = 0
            if to_insert and not is_dry_run:
                # INSERT ONLY missing mappings
                for q_id, t_id in to_insert:
                    conn.execute(
                        text("INSERT INTO question_topic (question_id, topic_id) VALUES (:qid, :tid)"),
                        {"qid": q_id, "tid": t_id}
                    )
                    inserted_count += 1
                print(f"Successfully executed {inserted_count} INSERT statements within transaction.")
            elif to_insert and is_dry_run:
                # In dry run, test insertion inside transaction to catch any foreign key or constraint issue
                for q_id, t_id in to_insert:
                    conn.execute(
                        text("INSERT INTO question_topic (question_id, topic_id) VALUES (:qid, :tid)"),
                        {"qid": q_id, "tid": t_id}
                    )
                    inserted_count += 1
                print(f"Dry-run executed {inserted_count} test INSERT statements in transaction.")

            # In-transaction integrity verification
            tx_c1_cnt = conn.execute(text("""
                SELECT count(*) 
                FROM question_topic qt
                JOIN questions q ON qt.question_id = q.id
                JOIN sections s ON q.section_id = s.id
                JOIN exams e ON s.exam_id = e.id
                WHERE e.course_id = 1
            """)).fetchone()[0]

            tx_c2_cnt = conn.execute(text("""
                SELECT count(*) 
                FROM question_topic qt
                JOIN questions q ON qt.question_id = q.id
                JOIN sections s ON q.section_id = s.id
                JOIN exams e ON s.exam_id = e.id
                WHERE e.course_id = 2
            """)).fetchone()[0]

            tx_total_qt = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]

            # Invariant: Calculus mappings unchanged
            assert tx_c1_cnt == 17, f"SAFETY INVARIANT VIOLATION: Calculus mappings changed from 17 to {tx_c1_cnt}!"

            # Check zero cross-course mappings
            cross_course_rows = conn.execute(text("""
                SELECT qt.question_id, e.course_id as q_course, qt.topic_id, s.course_id as t_course
                FROM question_topic qt
                JOIN questions q ON qt.question_id = q.id
                JOIN sections sec ON q.section_id = sec.id
                JOIN exams e ON sec.exam_id = e.id
                JOIN topics t ON qt.topic_id = t.id
                JOIN units u ON t.unit_id = u.id
                JOIN syllabuses s ON u.syllabus_id = s.id
                WHERE e.course_id != s.course_id
            """)).fetchall()
            assert len(cross_course_rows) == 0, f"SAFETY INVARIANT VIOLATION: Cross-course mappings found: {cross_course_rows}"

            # Check zero orphan mappings
            orphan_q = conn.execute(text("""
                SELECT count(*) FROM question_topic qt
                LEFT JOIN questions q ON qt.question_id = q.id
                WHERE q.id IS NULL
            """)).fetchone()[0]
            assert orphan_q == 0, f"SAFETY INVARIANT VIOLATION: Orphan question mappings: {orphan_q}"

            orphan_t = conn.execute(text("""
                SELECT count(*) FROM question_topic qt
                LEFT JOIN topics t ON qt.topic_id = t.id
                WHERE t.id IS NULL
            """)).fetchone()[0]
            assert orphan_t == 0, f"SAFETY INVARIANT VIOLATION: Orphan topic mappings: {orphan_t}"

            # Check student progress untouched
            tx_prog_cnt = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
            assert tx_prog_cnt == student_progress_cnt, "SAFETY INVARIANT VIOLATION: student_topic_progress modified!"

            if is_dry_run:
                trans.rollback()
                print("-" * 80)
                print("TRANSACTION ROLLED BACK (Dry-Run Mode). Zero persistent mutations applied to Render PostgreSQL.")
                print("=" * 80)
            else:
                trans.commit()
                print("-" * 80)
                print("TRANSACTION COMMITTED (Live Mutation Mode). Changes persisted to Render PostgreSQL.")
                print("=" * 80)

    # 9. Fresh connection post-verification
    with engine.connect() as post_conn:
        post_total = post_conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        post_c1 = post_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 1
        """)).fetchone()[0]
        post_c2 = post_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        """)).fetchone()[0]

        print("POST-TRANSACTION VERIFICATION (Fresh Connection):")
        print(f"  Final Calculus (C1) Count    : {post_c1} (Must be 17)")
        print(f"  Final Chemistry (C2) Count   : {post_c2}")
        print(f"  Final Total question_topic   : {post_total}")

        if not is_dry_run:
            assert post_c1 == 17, f"Post-mutation Calculus violation: {post_c1} != 17"
            assert post_c2 == expected_final_c2, f"Post-mutation Chemistry violation: {post_c2} != {expected_final_c2}"
            assert post_total == expected_final_total, f"Post-mutation Total violation: {post_total} != {expected_final_total}"
            print("ALL PRODUCTION INTEGRITY ASSERTIONS PASSED!")
        else:
            assert post_c1 == prod_c1_cnt, f"Dry-run baseline leaked C1: {post_c1} != {prod_c1_cnt}"
            assert post_c2 == prod_c2_cnt, f"Dry-run baseline leaked C2: {post_c2} != {prod_c2_cnt}"
            assert post_total == prod_total_qt, f"Dry-run baseline leaked Total: {post_total} != {prod_total_qt}"
            print("DRY-RUN ROLLBACK VERIFIED: Database returned exactly to baseline.")

    return {
        "is_dry_run": is_dry_run,
        "prod_chemistry_count_before": prod_c2_cnt,
        "prod_calculus_count_before": prod_c1_cnt,
        "local_chemistry_count": local_chemistry_count,
        "identical_existing_count": len(identical_existing),
        "conflicts_count": len(conflicts),
        "rows_to_insert": len(to_insert),
        "expected_final_chemistry": expected_final_c2,
        "expected_final_total": expected_final_total,
        "post_chemistry_count": post_c2,
        "post_calculus_count": post_c1,
        "post_total_count": post_total,
    }


def main():
    parser = argparse.ArgumentParser(description="Promote audited Chemistry question_topic mappings to PostgreSQL.")
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

    promote_chemistry_mappings(
        local_db_path=local_db,
        pg_url=pg_url,
        live_mutation=live_mutation,
        confirm_flag=args.confirm_production_mutation,
    )


if __name__ == "__main__":
    main()
