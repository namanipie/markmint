"""
Idempotent migration and seeding script for MarkMint Canonical Academic Data Layer.
Database-agnostic: supports both PostgreSQL (via DATABASE_URL / Render) and SQLite.

1. Ensures curriculum_mappings table and indexes exist.
2. Seeds all 2,810 curriculum entries across 54 branches idempotently.
3. Maps verified courses (Calculus, Chemistry, etc.) to existing Course records.
4. Tags ambiguous courses with notes, preserving raw integrity.
5. Enriches Courses 1 and 2 with validated SRM canonical codes and metadata.
"""

import os
import sys
import json
import re
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal, engine, Base
from backend.models.core import Course, CurriculumMapping

JSON_PATH = os.path.join(BASE_DIR, "data", "curriculum_catalog.json")


def normalize(text_val: str) -> str:
    """Normalize a string to lowercase alphanumeric characters only."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text_val)).lower()


def ensure_schema():
    """Ensure tables exist using SQLAlchemy metadata."""
    Base.metadata.create_all(bind=engine)


def seed_curriculum(db):
    """Seed the 2,810 curriculum entries and link verified courses idempotently."""
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"Curriculum catalog not found at {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"[Seed] Loaded {len(catalog)} curriculum entries from {JSON_PATH}")

    # Check existing count
    existing_count = db.query(CurriculumMapping).count()
    print(f"[Seed] Existing curriculum mappings count: {existing_count}")

    # Load existing courses
    db_courses = db.query(Course).all()
    course_map = {}
    for c in db_courses:
        course_map[normalize(c.name)] = c.id
        if c.code:
            course_map[normalize(c.code)] = c.id

    # Ambiguous subject specifications (do NOT force map)
    ambiguous_notes = {
        "biology": "General Biology: Multiple candidates (Intro to Comp Bio, Cell Bio, Microbiology)",
        "biochemistrylaboratory": "Practical laboratory course: Not a direct match for theory Biochemistry",
        "cellandmicrobiologylaboratory": "Practical laboratory course: Multiple candidates (Cell Bio, Microbiology)",
        "electrochemistryandcorrosion": "Specialized course: Substring contains Chemistry but is separate discipline",
        "nanoscalematerialschemistry": "Specialized course: Upper-semester Nanotechnology course",
        "fundamentals of economics": "Naming variant of Fundamental Of Economics (FOE)",
    }

    if existing_count < len(catalog):
        print("[Seed] Populating curriculum mappings...")
        existing_keys = {
            (m.branch_name, m.semester, m.curriculum_id)
            for m in db.query(CurriculumMapping.branch_name, CurriculumMapping.semester, CurriculumMapping.curriculum_id).all()
        }

        now_dt = datetime.utcnow()
        new_records = []
        for entry in catalog:
            branch = entry["branch"]
            sem = int(entry["semester"])
            curr_id = entry["id"]
            subj_name = entry["name"]
            credits = entry.get("credits", 3)

            if (branch, sem, curr_id) in existing_keys:
                continue

            norm_name = normalize(subj_name)
            course_id = None
            status = "UNMATCHED"
            notes = None

            if norm_name in course_map:
                course_id = course_map[norm_name]
                status = "MATCHED"
            elif norm_name in ambiguous_notes:
                status = "AMBIGUOUS"
                notes = ambiguous_notes[norm_name]
            else:
                status = "UNMATCHED"

            new_records.append(CurriculumMapping(
                branch_name=branch,
                semester=sem,
                curriculum_id=curr_id,
                subject_name=subj_name,
                credits=credits,
                course_id=course_id,
                status=status,
                notes=notes,
                created_at=now_dt
            ))

        if new_records:
            db.bulk_save_objects(new_records)
            db.commit()
            print(f"[Seed] Inserted {len(new_records)} curriculum mapping records.")

    # Enrich validated SRM canonical metadata for Courses 1 and 2
    c1 = db.query(Course).filter(Course.id == 1).first()
    if c1:
        c1.canonical_code = "21MAB101T"
        c1.regulation_year = 2021
        c1.department = "Mathematics"

    c2 = db.query(Course).filter(Course.id == 2).first()
    if c2:
        c2.canonical_code = "21CYB101J"
        c2.regulation_year = 2021
        c2.department = "Chemistry"

    db.commit()
    print("[Seed] Enriched Courses 1 & 2 canonical metadata.")


def verify_integrity(db):
    """Verify database invariants."""
    total_mappings = db.query(CurriculumMapping).count()
    matched = db.query(CurriculumMapping).filter(CurriculumMapping.status == "MATCHED").count()
    ambiguous = db.query(CurriculumMapping).filter(CurriculumMapping.status == "AMBIGUOUS").count()
    unmatched = db.query(CurriculumMapping).filter(CurriculumMapping.status == "UNMATCHED").count()

    total_courses = db.query(Course).count()

    print("\n[Integrity Verification]")
    print(f"  - curriculum_mappings: {total_mappings} (expected 2810)")
    print(f"    * MATCHED:   {matched} (expected 250)")
    print(f"    * AMBIGUOUS: {ambiguous} (expected 40)")
    print(f"    * UNMATCHED: {unmatched} (expected 2520)")
    print(f"  - courses:             {total_courses} (expected >= 12)")

    assert total_mappings == 2810, f"Expected 2810 mappings, got {total_mappings}"
    assert matched >= 250, f"Expected at least 250 matched, got {matched}"
    assert ambiguous == 40, f"Expected 40 ambiguous, got {ambiguous}"
    assert matched + ambiguous + unmatched == 2810, f"Expected sum of statuses to equal 2810, got {matched + ambiguous + unmatched}"
    assert total_courses >= 12, f"Expected >= 12 courses, got {total_courses}"

    print("[Integrity] ALL CURRICULUM INVARIANTS SATISFIED!")


def main():
    print(f"Connecting to database via SessionLocal()...")
    ensure_schema()
    db = SessionLocal()
    try:
        seed_curriculum(db)
        verify_integrity(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

