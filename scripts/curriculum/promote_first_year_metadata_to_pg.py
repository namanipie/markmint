"""
Surgical promotion script for First-Year course canonical metadata and curriculum mappings to Render PostgreSQL.
Promotes ONLY verified first-year metadata with strict atomic safeguards.
"""

import argparse
import os
import sys
import sqlite3
from typing import Dict, Any
from sqlalchemy import create_engine, text

BASE_DIR = r"c:\Users\ASUS\Desktop\system"
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


def promote_first_year_metadata(
    local_db_path: str,
    pg_url: str,
    live_mutation: bool = False,
    confirm_flag: bool = False,
) -> Dict[str, Any]:
    is_dry_run = not (live_mutation and confirm_flag)

    print("=" * 80)
    mode_str = "LIVE PRODUCTION MUTATION" if not is_dry_run else "DRY-RUN (NO REMOTE MUTATIONS)"
    print(f"FIRST-YEAR METADATA PROMOTION GATE [{mode_str}]")
    print("=" * 80)
    print(f"Local Database Path  : {local_db_path}")
    print(f"Target Remote Host   : {mask_url(pg_url)}")
    print(f"Live Mutation Flag   : {live_mutation}")
    print(f"Explicit Confirm Flag: {confirm_flag}")
    print("-" * 80)

    # 1. Load local verified course metadata
    if not os.path.exists(local_db_path):
        raise FileNotFoundError(f"Local database not found: {local_db_path}")

    s_conn = sqlite3.connect(local_db_path)
    s_conn.row_factory = sqlite3.Row
    s_cur = s_conn.cursor()

    local_courses = s_cur.execute("""
        SELECT id, name, code, canonical_code, regulation_year, department
        FROM courses
        WHERE id BETWEEN 1 AND 12
        ORDER BY id
    """).fetchall()

    local_compu_1_2 = s_cur.execute("""
        SELECT id, curriculum_id, course_id, status, notes
        FROM curriculum_mappings
        WHERE curriculum_id = 'compu-1-2'
    """).fetchone()

    s_conn.close()

    # 2. Connect to remote PostgreSQL
    connect_url = pg_url.strip()
    if connect_url.startswith("postgresql://"):
        connect_url = connect_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode" not in connect_url:
        delimiter = "&" if "?" in connect_url else "?"
        connect_url = f"{connect_url}{delimiter}sslmode=require"

    engine = create_engine(connect_url, pool_pre_ping=True)

    # Step A: Baseline audit
    with engine.connect() as b_conn:
        prod_total_qt = b_conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        prod_c1_cnt = b_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 1
        """)).fetchone()[0]
        prod_c2_cnt = b_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        """)).fetchone()[0]
        prod_c13_cnt = b_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 13
        """)).fetchone()[0]

        student_progress_cnt = b_conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        student_resource_cnt = b_conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]

    print("REMOTE POSTGRESQL BASELINE AUDIT:")
    print(f"  Total question_topic rows    : {prod_total_qt}")
    print(f"  Calculus (Course 1) mappings : {prod_c1_cnt}")
    print(f"  Chemistry (Course 2) mappings: {prod_c2_cnt}")
    print(f"  SPCM (Course 13) mappings    : {prod_c13_cnt}")
    print(f"  Student Topic Progress rows  : {student_progress_cnt}")
    print(f"  Student Resource Progress    : {student_resource_cnt}")
    print("-" * 80)

    # Step B: Execute Single Explicit Atomic Transaction
    courses_updated = 0
    curriculum_updated = 0

    with engine.connect() as conn:
        with conn.begin() as trans:
            try:
                for lc in local_courses:
                    cid = lc["id"]
                    can_code = lc["canonical_code"]
                    reg_year = lc["regulation_year"]
                    dept = lc["department"]

                    rc = conn.execute(
                        text("SELECT canonical_code, regulation_year, department FROM courses WHERE id = :id"),
                        {"id": cid}
                    ).fetchone()
                    if rc:
                        if rc[0] != can_code or rc[1] != reg_year or rc[2] != dept:
                            print(f"  Updating Course {cid} ({lc['name']}): canonical_code={can_code}, reg_year={reg_year}, dept={dept}")
                            conn.execute(text("""
                                UPDATE courses
                                SET canonical_code = :can_code, regulation_year = :reg_year, department = :dept
                                WHERE id = :id
                            """), {"id": cid, "can_code": can_code, "reg_year": reg_year, "dept": dept})
                            courses_updated += 1
                        else:
                            print(f"  Course {cid} ({lc['name']}) is already up to date: canonical_code={can_code}")

                # Specific verified first-year curriculum mapping repairs
                target_curriculum_updates = [
                    (745, 1, 'MATCHED', None),
                    (842, 1, 'MATCHED', None),
                    (891, 1, 'MATCHED', None),
                    (940, 1, 'MATCHED', None),
                    (988, 1, 'MATCHED', None),
                    (1036, 1, 'MATCHED', None),
                    (1085, 1, 'MATCHED', None),
                    (1282, 1, 'MATCHED', None),
                    (2659, 1, 'MATCHED', None),
                    (794, 13, 'MATCHED', None),
                    (1135, 13, 'MATCHED', None),
                    (1184, 13, 'MATCHED', None),
                    (1233, 6, 'MATCHED', 'Fundamentals of Economics matched to course 6 (18MSS101T)')
                ]
                curriculum_updated = 0
                for row_id, cid, status, notes in target_curriculum_updates:
                    rcm = conn.execute(
                        text("SELECT course_id, status, notes FROM curriculum_mappings WHERE id = :id"),
                        {"id": row_id}
                    ).fetchone()
                    if rcm and (rcm[0] != cid or rcm[1] != status or rcm[2] != notes):
                        print(f"  Updating curriculum_mappings id={row_id} -> course_id={cid}, status={status}")
                        conn.execute(text("""
                            UPDATE curriculum_mappings
                            SET course_id = :cid, status = :status, notes = :notes
                            WHERE id = :id
                        """), {"id": row_id, "cid": cid, "status": status, "notes": notes})
                        curriculum_updated += 1

                print("-" * 80)
                print("MUTATION PROPOSAL:")
                print(f"  Courses to update            : {courses_updated}")
                print(f"  Curriculum rows to update    : {curriculum_updated}")
                print("-" * 80)

                if not is_dry_run:
                    print("EXECUTING LIVE PRODUCTION COMMIT...")
                    print("TRANSACTION WILL COMMIT ON BLOCK EXIT.")
                else:
                    print("DRY-RUN COMPLETE: Performing explicit transaction ROLLBACK (0 mutations committed).")
                    trans.rollback()

            except Exception as e:
                trans.rollback()
                print(f"ERROR: Transaction aborted and rolled back. Exception: {e}")
                raise

    # Step C: Post-Audit on new connection
    with engine.connect() as p_conn:
        post_total = p_conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        post_c1 = p_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 1
        """)).fetchone()[0]
        post_c2 = p_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 2
        """)).fetchone()[0]
        post_c13 = p_conn.execute(text("""
            SELECT count(*) 
            FROM question_topic qt
            JOIN questions q ON qt.question_id = q.id
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            WHERE e.course_id = 13
        """)).fetchone()[0]
        post_student_progress = p_conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
        post_resource_progress = p_conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]

        print("-" * 80)
        print("POST-PROMOTION AUDIT:")
        print(f"  Calculus (Course 1) Mappings : {post_c1} (Expected: {prod_c1_cnt} | Invariant: {post_c1 == prod_c1_cnt})")
        print(f"  Chemistry (Course 2) Mappings: {post_c2} (Expected: {prod_c2_cnt} | Invariant: {post_c2 == prod_c2_cnt})")
        print(f"  SPCM (Course 13) Mappings    : {post_c13} (Expected: {prod_c13_cnt} | Invariant: {post_c13 == prod_c13_cnt})")
        print(f"  Total question_topic Rows    : {post_total} (Expected: {prod_total_qt} | Invariant: {post_total == prod_total_qt})")
        print(f"  Student Topic Progress Rows  : {post_student_progress} (Untouched: {post_student_progress == student_progress_cnt})")
        print(f"  Student Resource Progress    : {post_resource_progress} (Untouched: {post_resource_progress == student_resource_cnt})")

        cross_course = p_conn.execute(text("""
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

        if not is_dry_run:
            print("VERIFYING REMOTE VALUES POST-COMMIT:")
            for lc in local_courses:
                rc = p_conn.execute(
                    text("SELECT canonical_code, regulation_year FROM courses WHERE id = :id"),
                    {"id": lc["id"]}
                ).fetchone()
                print(f"  Course {lc['id']}: canonical_code={rc[0]} (local: {lc['canonical_code']})")
                assert rc[0] == lc["canonical_code"], f"Course {lc['id']} canonical_code mismatch!"
            
            rcm_1233 = p_conn.execute(
                text("SELECT course_id, status FROM curriculum_mappings WHERE id = 1233")
            ).fetchone()
            print(f"  Curriculum id=1233 (Economics): course_id={rcm_1233[0]}, status={rcm_1233[1]}")
            assert rcm_1233[0] == 6 and rcm_1233[1] == "MATCHED", "Curriculum mapping 1233 mismatch!"

            rcm_745 = p_conn.execute(
                text("SELECT course_id, status FROM curriculum_mappings WHERE id = 745")
            ).fetchone()
            print(f"  Curriculum id=745 (Calculus): course_id={rcm_745[0]}, status={rcm_745[1]}")
            assert rcm_745[0] == 1 and rcm_745[1] == "MATCHED", "Curriculum mapping 745 mismatch!"
            print("ALL REMOTE VALUES CONFIRMED.")
        else:
            assert post_total == prod_total_qt, "Dry run leaked total mappings"
            assert post_c1 == prod_c1_cnt, "Dry run leaked C1 mappings"
            print("DRY-RUN ROLLBACK VERIFIED: Remote PostgreSQL unchanged.")

    return {
        "is_dry_run": is_dry_run,
        "courses_updated": courses_updated,
        "curriculum_updated": curriculum_updated,
        "post_c1": post_c1,
        "post_c2": post_c2,
        "post_c13": post_c13,
        "post_total": post_total,
    }


def main():
    parser = argparse.ArgumentParser(description="Promote verified First-Year metadata to PostgreSQL.")
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

    promote_first_year_metadata(
        local_db_path=local_db,
        pg_url=pg_url,
        live_mutation=live_mutation,
        confirm_flag=args.confirm_production_mutation,
    )


if __name__ == "__main__":
    main()
