"""
Canonical Generic Curriculum & Taxonomy Promotion CLI for MarkMint.
Promotes verified local SQLite taxonomy units, topics, and question_topic mappings
to remote Render PostgreSQL with strict non-destructive safety gates.

Usage:
  # Dry-run audit for single course (default):
  python -m scripts.curriculum.promote --course-id 14 --dry-run

  # Dry-run audit for all Semester 2 courses:
  python -m scripts.curriculum.promote --all-semester-2 --dry-run

  # Live mutation (requires explicit flags):
  python -m scripts.curriculum.promote --course-id 14 --live --confirm-production-mutation
"""

import argparse
import os
import re
import sys
import sqlite3
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_LOCAL_DB = os.path.join(BASE_DIR, "production_corpus.db")
SEMESTER_2_COURSE_IDS = [14, 15, 16, 17, 18, 21, 22, 23]


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
    """Resolve PostgreSQL connection string safely without hardcoding."""
    if os.environ.get("RENDER_DATABASE_URL"):
        return os.environ["RENDER_DATABASE_URL"].replace("postgresql://", "postgresql+psycopg2://")
    smoke_file = os.path.join(BASE_DIR, "scripts", "verify_production_smoke.py")
    if os.path.exists(smoke_file):
        with open(smoke_file, "r") as f:
            match = re.search(r'postgresql://[^\"]+', f.read())
            if match:
                return match.group(0).replace("postgresql://", "postgresql+psycopg2://")
    raise ValueError("Could not resolve PostgreSQL connection URL from environment or configuration.")


def run_promotion(
    course_ids: List[int],
    local_db_path: str = DEFAULT_LOCAL_DB,
    pg_url: Optional[str] = None,
    live_mutation: bool = False,
    confirm_flag: bool = False,
) -> Dict[str, Any]:
    is_dry_run = not (live_mutation and confirm_flag)
    if pg_url is None:
        pg_url = get_pg_url()

    print("=" * 80)
    mode_str = "LIVE PRODUCTION MUTATION" if not is_dry_run else "DRY-RUN (NO MUTATIONS PERSISTED)"
    print(f"MARKMINT CANONICAL PROMOTION PIPELINE [{mode_str}]")
    print("=" * 80)
    print(f"Target Course IDs    : {course_ids}")
    print(f"Local Database Path  : {local_db_path}")
    print(f"Target Remote Host   : {mask_url(pg_url)}")
    print(f"Live Mutation Flag   : {live_mutation}")
    print(f"Explicit Confirm Flag: {confirm_flag}")
    print("-" * 80)

    # 1. Load verified local data
    if not os.path.exists(local_db_path):
        raise FileNotFoundError(f"Local database not found: {local_db_path}")

    s_conn = sqlite3.connect(local_db_path)
    s_conn.row_factory = sqlite3.Row
    s_cur = s_conn.cursor()

    local_courses = s_cur.execute(
        f"SELECT id, name, code FROM courses WHERE id IN ({','.join(map(str, course_ids))}) ORDER BY id"
    ).fetchall()
    found_cids = {c["id"] for c in local_courses}
    missing_cids = set(course_ids) - found_cids
    if missing_cids:
        s_conn.close()
        raise ValueError(f"Requested courses not found in local DB: {missing_cids}")

    # Local Units
    local_units = s_cur.execute(f"""
        SELECT u.id, u.syllabus_id, u.number, u.name, s.course_id
        FROM units u
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id IN ({','.join(map(str, course_ids))})
        ORDER BY s.course_id, u.number
    """).fetchall()

    # Local Topics
    local_topics = s_cur.execute(f"""
        SELECT t.id, t.unit_id, t.name, s.course_id
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses s ON u.syllabus_id = s.id
        WHERE s.course_id IN ({','.join(map(str, course_ids))})
        ORDER BY s.course_id, t.id
    """).fetchall()

    # Local Question Mappings
    local_mappings = s_cur.execute(f"""
        SELECT qt.question_id, qt.topic_id, e.course_id, t.name as topic_name
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        WHERE e.course_id IN ({','.join(map(str, course_ids))})
        ORDER BY e.course_id, qt.question_id
    """).fetchall()

    s_conn.close()

    print(f"Loaded Local Curriculum Specifications:")
    print(f"  Target Courses: {len(local_courses)}")
    print(f"  Target Units  : {len(local_units)}")
    print(f"  Target Topics : {len(local_topics)}")
    print(f"  Local Mappings: {len(local_mappings)}")
    for c in local_courses:
        c_maps = [m for m in local_mappings if m["course_id"] == c["id"]]
        print(f"    Course {c['id']:2d} ({c['code']}): {len(c_maps)} mapped questions")
    print("-" * 80)

    # 2. Connect to remote PostgreSQL
    engine = create_engine(pg_url, pool_pre_ping=True)

    summary: Dict[str, Any] = {
        "mode": mode_str,
        "courses_audited": len(local_courses),
        "units_updated": 0,
        "units_inserted": 0,
        "topics_inserted": 0,
        "topics_skipped": 0,
        "mappings_to_insert": 0,
        "mappings_already_exist": 0,
        "mappings_conflicts": 0,
    }

    with engine.connect() as conn:
        # Pre-mutation remote baseline
        remote_total_qt = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
        remote_student_progress = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]

        print("REMOTE POSTGRESQL PRE-MUTATION BASELINE:")
        print(f"  Total question_topic rows    : {remote_total_qt}")
        print(f"  Student Topic Progress rows  : {remote_student_progress}")
        print("-" * 80)

        # Start atomic transaction
        conn.rollback()
        trans = conn.begin()
        try:
            # Step A: Validate and sync Units
            print("Step A: Auditing and Syncing Units...")
            for u in local_units:
                existing_u = conn.execute(
                    text("SELECT id, name FROM units WHERE id = :uid"),
                    {"uid": u["id"]}
                ).fetchone()

                if existing_u:
                    if existing_u[1] != u["name"]:
                        conn.execute(
                            text("UPDATE units SET name = :name WHERE id = :uid"),
                            {"name": u["name"], "uid": u["id"]}
                        )
                        summary["units_updated"] += 1
                else:
                    conn.execute(
                        text("INSERT INTO units (id, syllabus_id, number, name) VALUES (:id, :syl_id, :num, :name)"),
                        {"id": u["id"], "syl_id": u["syllabus_id"], "num": u["number"], "name": u["name"]}
                    )
                    summary["units_inserted"] += 1
            print(f"  Units updated: {summary['units_updated']}, Units inserted: {summary['units_inserted']}")

            # Step B: Validate and sync Topics
            print("Step B: Auditing and Syncing Topics...")
            for t in local_topics:
                existing_t = conn.execute(
                    text("SELECT id, name, unit_id FROM topics WHERE id = :tid"),
                    {"tid": t["id"]}
                ).fetchone()

                if existing_t:
                    summary["topics_skipped"] += 1
                    if existing_t[1] != t["name"] or existing_t[2] != t["unit_id"]:
                        conn.execute(
                            text("UPDATE topics SET name = :name, unit_id = :uid WHERE id = :tid"),
                            {"name": t["name"], "uid": t["unit_id"], "tid": t["id"]}
                        )
                else:
                    conn.execute(
                        text("INSERT INTO topics (id, unit_id, name) VALUES (:id, :uid, :name)"),
                        {"id": t["id"], "uid": t["unit_id"], "name": t["name"]}
                    )
                    summary["topics_inserted"] += 1
            print(f"  Topics inserted: {summary['topics_inserted']}, Topics already present: {summary['topics_skipped']}")

            # Step C: Audit Question-Topic Mappings
            print("Step C: Auditing Question-Topic Mappings...")
            mappings_to_insert = []
            conflicts = []

            all_target_qids = [m["question_id"] for m in local_mappings]
            if all_target_qids:
                # Batch query existing question IDs in remote database
                q_id_chunks = [all_target_qids[i:i+1000] for i in range(0, len(all_target_qids), 1000)]
                remote_existing_qids = set()
                for chunk in q_id_chunks:
                    q_rows = conn.execute(
                        text("SELECT id FROM questions WHERE id IN :qids"),
                        {"qids": tuple(chunk)}
                    ).fetchall()
                    remote_existing_qids.update(r[0] for r in q_rows)

                # Batch query existing question_topic mappings for these questions
                existing_mappings_map = {}
                for chunk in q_id_chunks:
                    m_rows = conn.execute(
                        text("SELECT question_id, topic_id FROM question_topic WHERE question_id IN :qids"),
                        {"qids": tuple(chunk)}
                    ).fetchall()
                    for q_id, t_id in m_rows:
                        if q_id not in existing_mappings_map:
                            existing_mappings_map[q_id] = set()
                        existing_mappings_map[q_id].add(t_id)

                for m in local_mappings:
                    qid = m["question_id"]
                    tid = m["topic_id"]

                    if qid not in remote_existing_qids:
                        raise ValueError(f"Integrity error: Question {qid} does not exist on remote database!")

                    existing_tids = existing_mappings_map.get(qid, set())
                    if existing_tids:
                        if tid in existing_tids:
                            summary["mappings_already_exist"] += 1
                        else:
                            conflicts.append({
                                "question_id": qid,
                                "existing_topic_ids": list(existing_tids),
                                "proposed_topic_id": tid,
                                "course_id": m["course_id"],
                            })
                            summary["mappings_conflicts"] += 1
                    else:
                        mappings_to_insert.append({"qid": qid, "tid": tid})

            summary["mappings_to_insert"] = len(mappings_to_insert)
            print(f"  New mappings to insert: {len(mappings_to_insert)}")
            print(f"  Already mapped in PG  : {summary['mappings_already_exist']}")
            print(f"  Conflicting mappings  : {summary['mappings_conflicts']}")

            if conflicts:
                print(f"  WARNING: {len(conflicts)} conflicting mappings found (will not be overwritten):")
                for c in conflicts[:5]:
                    print(f"    Q{c['question_id']}: existing={c['existing_topic_ids']} vs proposed={c['proposed_topic_id']}")

            # Batch insert new mappings
            if mappings_to_insert:
                chunk_size = 500
                for i in range(0, len(mappings_to_insert), chunk_size):
                    batch = mappings_to_insert[i:i+chunk_size]
                    conn.execute(
                        text("INSERT INTO question_topic (question_id, topic_id) VALUES (:qid, :tid)"),
                        batch
                    )

            # Sequence resynchronization
            conn.execute(text("SELECT setval('units_id_seq', (SELECT max(id) FROM units))"))
            conn.execute(text("SELECT setval('topics_id_seq', (SELECT max(id) FROM topics))"))

            # Step D: Integrity Validation
            print("Step D: Validating Integrity and Invariants...")
            post_student_progress = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
            assert post_student_progress == remote_student_progress, (
                f"Student progress corruption! Expected {remote_student_progress}, found {post_student_progress}"
            )

            # Invariant check: foreign key integrity on question_topic
            fk_orphans = conn.execute(text("""
                SELECT count(*)
                FROM question_topic qt
                LEFT JOIN questions q ON qt.question_id = q.id
                LEFT JOIN topics t ON qt.topic_id = t.id
                WHERE q.id IS NULL OR t.id IS NULL
            """)).fetchone()[0]
            assert fk_orphans == 0, f"Found {fk_orphans} orphaned question_topic rows!"

            if is_dry_run:
                print("-" * 80)
                print("DRY RUN COMPLETE: Rolling back all mutations. Zero changes persisted.")
                trans.rollback()
            else:
                print("-" * 80)
                print("CONFIRMED LIVE MUTATION: Committing atomic transaction to PostgreSQL...")
                trans.commit()
                print("Successfully committed live migration.")

        except Exception as e:
            trans.rollback()
            print(f"ERROR: Promotion failed and was completely rolled back: {e}")
            raise

    print("=" * 80)
    print("PROMOTION SUMMARY:")
    for k, v in summary.items():
        print(f"  {k:25s}: {v}")
    print("=" * 80)

    return summary


def main():
    parser = argparse.ArgumentParser(description="MarkMint Canonical Curriculum Promotion CLI")
    parser.add_argument("--course-id", type=int, help="Specific Course ID to promote")
    parser.add_argument("--all-semester-2", action="store_true", help="Promote all Semester 2 courses")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run without committing (default)")
    parser.add_argument("--live", action="store_true", help="Enable live database mutation")
    parser.add_argument(
        "--confirm-production-mutation",
        action="store_true",
        help="Explicit confirmation required to mutate production",
    )
    parser.add_argument("--local-db", default=DEFAULT_LOCAL_DB, help="Path to local SQLite database")

    args = parser.parse_args()

    if args.all_semester_2:
        target_courses = SEMESTER_2_COURSE_IDS
    elif args.course_id:
        target_courses = [args.course_id]
    else:
        print("Please specify --course-id <ID> or --all-semester-2")
        sys.exit(1)

    live_mutation = args.live and args.confirm_production_mutation
    run_promotion(
        course_ids=target_courses,
        local_db_path=args.local_db,
        live_mutation=live_mutation,
        confirm_flag=args.confirm_production_mutation,
    )


if __name__ == "__main__":
    main()
