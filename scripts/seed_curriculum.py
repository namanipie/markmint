"""
Idempotent migration and seeding script for MarkMint Canonical Academic Data Layer.

1. Ensures nullable canonical columns exist on courses table.
2. Ensures curriculum_mappings table and indexes exist.
3. Seeds all 2,810 curriculum entries across 54 branches.
4. Maps verified courses (Calculus, Chemistry, etc.) to existing Course records.
5. Tags ambiguous courses with notes, preserving raw integrity.
6. Enriches Courses 1 and 2 with validated SRM canonical codes and metadata.
"""

import os
import sys
import json
import sqlite3
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")
JSON_PATH = os.path.join(BASE_DIR, "data", "curriculum_catalog.json")


def normalize(text: str) -> str:
    """Normalize a string to lowercase alphanumeric characters only."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()


def migrate_schema(conn: sqlite3.Connection):
    """Add new columns to courses and create curriculum_mappings table idempotently."""
    cur = conn.cursor()

    # 1. Add nullable columns to courses if missing
    cur.execute("PRAGMA table_info(courses)")
    existing_cols = [row[1] for row in cur.fetchall()]

    new_cols = [
        ("canonical_code", "VARCHAR(32)"),
        ("regulation_year", "INTEGER"),
        ("department", "VARCHAR(120)")
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"[Schema] Adding column '{col_name}' ({col_type}) to courses table...")
            cur.execute(f"ALTER TABLE courses ADD COLUMN {col_name} {col_type}")

    # 2. Create curriculum_mappings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS curriculum_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_name VARCHAR(120) NOT NULL,
            semester INTEGER NOT NULL,
            curriculum_id VARCHAR(64) NOT NULL,
            subject_name VARCHAR(255) NOT NULL,
            credits INTEGER DEFAULT 3,
            course_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'UNMATCHED',
            notes VARCHAR(255),
            created_at DATETIME
        )
    """)

    # 3. Create indexes
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_branch_sem_curr_id 
        ON curriculum_mappings(branch_name, semester, curriculum_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_branch_sem_status 
        ON curriculum_mappings(branch_name, semester, status)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_curr_course_id 
        ON curriculum_mappings(course_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_curr_subject_name 
        ON curriculum_mappings(subject_name)
    """)

    conn.commit()
    print("[Schema] Schema migration complete.")


def seed_curriculum(conn: sqlite3.Connection):
    """Seed the 2,810 curriculum entries and link verified courses."""
    cur = conn.cursor()

    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"Curriculum catalog not found at {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"[Seed] Loaded {len(catalog)} curriculum entries from {JSON_PATH}")

    # Load existing courses
    cur.execute("SELECT id, code, name FROM courses")
    db_courses = cur.fetchall()
    
    # Map normalized course name -> course_id
    course_map = {}
    for c_id, code, name in db_courses:
        course_map[normalize(name)] = c_id

    # Ambiguous subject specifications (do NOT force map)
    ambiguous_notes = {
        "biology": "General Biology: Multiple candidates (Intro to Comp Bio, Cell Bio, Microbiology)",
        "biochemistrylaboratory": "Practical laboratory course: Not a direct match for theory Biochemistry",
        "cellandmicrobiologylaboratory": "Practical laboratory course: Multiple candidates (Cell Bio, Microbiology)",
        "electrochemistryandcorrosion": "Specialized course: Substring contains Chemistry but is separate discipline",
        "nanoscalematerialschemistry": "Specialized course: Upper-semester Nanotechnology course",
        "fundamentals of economics": "Naming variant of Fundamental Of Economics (FOE)",
    }

    # Tracking counters
    counts = {
        "matched": 0,
        "unmatched": 0,
        "ambiguous": 0,
        "total": len(catalog)
    }

    now_iso = datetime.utcnow().isoformat()

    for entry in catalog:
        branch = entry["branch"]
        sem = int(entry["semester"])
        curr_id = entry["id"]
        subj_name = entry["name"]
        credits = entry.get("credits", 3)

        norm_name = normalize(subj_name)

        course_id = None
        status = "UNMATCHED"
        notes = None

        if norm_name in course_map:
            course_id = course_map[norm_name]
            status = "MATCHED"
            counts["matched"] += 1
        elif norm_name in ambiguous_notes:
            status = "AMBIGUOUS"
            notes = ambiguous_notes[norm_name]
            counts["ambiguous"] += 1
        else:
            status = "UNMATCHED"
            counts["unmatched"] += 1

        # Upsert entry
        cur.execute("""
            INSERT INTO curriculum_mappings (
                branch_name, semester, curriculum_id, subject_name, credits, course_id, status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(branch_name, semester, curriculum_id) DO UPDATE SET
                subject_name = excluded.subject_name,
                credits = excluded.credits,
                course_id = excluded.course_id,
                status = excluded.status,
                notes = excluded.notes
        """, (branch, sem, curr_id, subj_name, credits, course_id, status, notes, now_iso))

    # Enrich validated SRM canonical metadata for Courses 1 and 2
    cur.execute("""
        UPDATE courses 
        SET canonical_code = '21MAB101T', regulation_year = 2021, department = 'Mathematics' 
        WHERE id = 1
    """)
    cur.execute("""
        UPDATE courses 
        SET canonical_code = '21CYB101J', regulation_year = 2021, department = 'Chemistry' 
        WHERE id = 2
    """)

    conn.commit()

    print("[Seed] Seeding completed:")
    print(f"  - Total entries processed: {counts['total']}")
    print(f"  - Verified MATCHED:       {counts['matched']}")
    print(f"  - Tagged AMBIGUOUS:       {counts['ambiguous']}")
    print(f"  - UNMATCHED (catalog):    {counts['unmatched']}")


def verify_integrity(conn: sqlite3.Connection):
    """Verify database invariants."""
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM curriculum_mappings")
    total_mappings = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM courses")
    total_courses = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM exams")
    total_exams = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM questions")
    total_questions = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM question_families")
    total_families = cur.fetchone()[0]

    print("\n[Integrity Verification]")
    print(f"  - curriculum_mappings: {total_mappings} (expected 2810)")
    print(f"  - courses:             {total_courses} (expected 12)")
    print(f"  - exams:               {total_exams} (expected 8)")
    print(f"  - questions:           {total_questions} (expected 223)")
    print(f"  - question_families:   {total_families} (expected 548)")

    assert total_mappings == 2810, f"Expected 2810 mappings, got {total_mappings}"
    assert total_courses == 12, f"Expected 12 courses, got {total_courses}"
    assert total_exams == 8, f"Expected 8 exams, got {total_exams}"
    assert total_questions == 223, f"Expected 223 questions, got {total_questions}"
    assert total_families == 548, f"Expected 548 question families, got {total_families}"

    print("[Integrity] ALL INVARIANTS SATISFIED!")


def main():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    try:
        migrate_schema(conn)
        seed_curriculum(conn)
        verify_integrity(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
