"""
Canonical curriculum seeding service for MarkMint.
Provides self-healing automatic seeding for SQLite and PostgreSQL.
Ensures curriculum_mappings is never empty at runtime.
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.core import Course, CurriculumMapping

logger = logging.getLogger("markmint.curriculum_seeder")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CANDIDATE_PATHS = [
    os.path.join(BASE_DIR, "backend", "data", "curriculum_catalog.json"),
    os.path.join(BASE_DIR, "data", "curriculum_catalog.json"),
    os.path.abspath("data/curriculum_catalog.json"),
    os.path.abspath("backend/data/curriculum_catalog.json"),
]


def get_catalog_path() -> Optional[str]:
    for p in CANDIDATE_PATHS:
        if os.path.exists(p):
            return p
    return None


def normalize(text_val: str) -> str:
    """Normalize a string to lowercase alphanumeric characters only."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text_val)).lower()


AMBIGUOUS_NOTES = {
    "biology": "General Biology: Multiple candidates (Intro to Comp Bio, Cell Bio, Microbiology)",
    "biochemistrylaboratory": "Practical laboratory course: Not a direct match for theory Biochemistry",
    "cellandmicrobiologylaboratory": "Practical laboratory course: Multiple candidates (Cell Bio, Microbiology)",
    "electrochemistryandcorrosion": "Specialized course: Substring contains Chemistry but is separate discipline",
    "nanoscalematerialschemistry": "Specialized course: Upper-semester Nanotechnology course",
    "fundamentals of economics": "Naming variant of Fundamental Of Economics (FOE)",
}


def seed_curriculum(db: Session) -> int:
    """Seed the 2,810 curriculum entries and link verified courses idempotently."""
    catalog_path = get_catalog_path()
    if not catalog_path:
        logger.error("Curriculum catalog JSON not found in any candidate path: %s", CANDIDATE_PATHS)
        return 0

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    logger.info("Loaded %d curriculum catalog entries from %s", len(catalog), catalog_path)

    # Check existing count
    existing_count = db.query(func.count(CurriculumMapping.id)).scalar() or 0

    # Load existing courses
    db_courses = db.query(Course).all()
    course_map = {}
    for c in db_courses:
        course_map[normalize(c.name)] = c.id
        if c.code:
            course_map[normalize(c.code)] = c.id

    if existing_count < len(catalog):
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
            elif norm_name in AMBIGUOUS_NOTES:
                status = "AMBIGUOUS"
                notes = AMBIGUOUS_NOTES[norm_name]
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
            logger.info("Successfully seeded %d new curriculum mappings.", len(new_records))

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
    final_count = db.query(func.count(CurriculumMapping.id)).scalar() or 0
    return final_count


def ensure_curriculum_seeded(db: Session) -> int:
    """Check if curriculum_mappings is empty; if so, trigger automatic seeding."""
    count = db.query(func.count(CurriculumMapping.id)).scalar() or 0
    if count == 0:
        logger.warning("curriculum_mappings is empty (0 rows). Running auto-seed...")
        return seed_curriculum(db)
    return count
