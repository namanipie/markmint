"""
Generates the canonical frontend curriculum catalog (src/data/canonical_curriculum.json)
directly from the repository-local canonical curriculum sources.
Ensures zero-latency instant Academic Scope in the Next.js frontend without requiring Render.

Guarantees:
- Deterministic, stable ordering
- Complete 54-branch and 2,810 curriculum mapping coverage
- Zero network or production-database dependencies
- Strict validation: fails hard if any invariant is violated
"""

import os
import sys
import json
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

from backend.models.core import CurriculumMapping, Course, CourseTrack, Exam, Section, Question

OUTPUT_PATH = os.path.join(BASE_DIR, "src", "data", "canonical_curriculum.json")
LOCAL_SQLITE_PATH = os.path.join(BASE_DIR, "production_corpus.db")


def get_session():
    """Obtain a session preferring the local canonical database without network dependencies."""
    if os.path.exists(LOCAL_SQLITE_PATH):
        engine = create_engine(f"sqlite:///{LOCAL_SQLITE_PATH}")
        Session = sessionmaker(bind=engine)
        return Session()
    from backend.core.database import SessionLocal
    return SessionLocal()


def validate_catalog(payload: dict):
    """Strictly validate catalog integrity. Raises AssertionError on any violation."""
    branches = payload.get("branches", [])
    hierarchy = payload.get("hierarchy", {})

    assert len(branches) == 54, f"Expected 54 branches, got {len(branches)}"
    assert len(hierarchy) == 54, f"Expected 54 branches in hierarchy, got {len(hierarchy)}"

    seen_triplets = set()
    total_subjects = 0
    course_8_found = False

    for branch_name, semesters in hierarchy.items():
        assert branch_name in branches, f"Branch '{branch_name}' not in branches list"
        for sem_str, subjects in semesters.items():
            sem_num = int(sem_str)
            seen_sem_curr_ids = set()
            for subj in subjects:
                curr_id = subj.get("curriculum_id")
                assert curr_id, f"Missing curriculum_id in {branch_name} Sem {sem_str}: {subj}"
                
                # Check uniqueness of triplets
                triplet = (branch_name, sem_num, curr_id)
                assert triplet not in seen_triplets, f"Duplicate triplet found: {triplet}"
                seen_triplets.add(triplet)

                # Check uniqueness of curriculum_id within this branch + semester
                assert curr_id not in seen_sem_curr_ids, f"Duplicate curriculum_id in {branch_name} Sem {sem_num}: {curr_id}"
                seen_sem_curr_ids.add(curr_id)

                # Validate required fields
                assert subj.get("subject_name"), f"Missing subject_name in {curr_id}"
                assert isinstance(subj.get("credits"), (int, float)), f"Invalid credits in {curr_id}"
                assert subj.get("status") in ("MATCHED", "UNMATCHED", "AMBIGUOUS"), f"Invalid status in {curr_id}"

                # Validate course mapping if matched
                if subj.get("status") == "MATCHED":
                    assert subj.get("course_id") is not None, f"Matched course missing course_id in {curr_id}"

                # Validate Course 8 Foreign Languages multi-track
                if subj.get("course_id") == 8:
                    course_8_found = True
                    assert subj.get("has_tracks") is True, "Course 8 must have has_tracks=True"
                    tracks = subj.get("tracks", [])
                    assert len(tracks) == 6, f"Course 8 expected 6 language tracks, got {len(tracks)}"
                    track_keys = {t["track_key"] for t in tracks}
                    expected_keys = {"german", "french", "spanish", "japanese", "korean", "chinese"}
                    assert track_keys == expected_keys, f"Invalid track keys for Course 8: {track_keys}"

                total_subjects += 1

    assert total_subjects == 2810, f"Expected exactly 2,810 total curriculum mappings, got {total_subjects}"
    assert course_8_found, "Course 8 (Foreign Languages) was not found in hierarchy"
    print(f"[Validation Passed] 54 branches, {total_subjects} entries, 0 duplicate IDs, Course 8 verified.")


def generate_catalog():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    db = get_session()

    try:
        # Pre-fetch course exam counts and question counts to avoid N+1
        exam_rows = db.query(Exam.course_id, func.count(Exam.id)).group_by(Exam.course_id).all()
        exam_counts = {r[0]: r[1] for r in exam_rows}

        q_rows = (
            db.query(Exam.course_id, func.count(Question.id))
            .join(Section, Section.exam_id == Exam.id)
            .join(Question, Question.section_id == Section.id)
            .group_by(Exam.course_id)
            .all()
        )
        q_counts = {r[0]: r[1] for r in q_rows}

        tracks_by_course = {}
        for t in db.query(CourseTrack).order_by(CourseTrack.id.asc()).all():
            tracks_by_course.setdefault(t.course_id, []).append({
                "id": t.id,
                "course_id": t.course_id,
                "track_key": t.track_key,
                "track_name": t.track_name,
                "track_code": t.track_code,
                "track_type": t.track_type,
            })

        mappings = (
            db.query(CurriculumMapping)
            .order_by(CurriculumMapping.branch_name.asc(), CurriculumMapping.semester.asc(), CurriculumMapping.curriculum_id.asc())
            .all()
        )

        branches = sorted(list(set(m.branch_name for m in mappings)))
        default_branch = "Aerospace Engineering" if "Aerospace Engineering" in branches else (branches[0] if branches else "")

        hierarchy = {b: {} for b in branches}

        for m in mappings:
            sem_str = str(m.semester)
            if sem_str not in hierarchy[m.branch_name]:
                hierarchy[m.branch_name][sem_str] = []

            cid = m.course_id
            c_exams = exam_counts.get(cid, 0) if cid else 0
            c_qs = q_counts.get(cid, 0) if cid else 0
            c_tracks = tracks_by_course.get(cid, []) if cid else []
            canonical_code = m.course.canonical_code if m.course else None

            hierarchy[m.branch_name][sem_str].append({
                "curriculum_id": m.curriculum_id,
                "subject_name": m.subject_name,
                "credits": m.credits or 3,
                "course_id": cid,
                "canonical_code": canonical_code,
                "status": m.status,
                "has_exams": c_exams > 0,
                "exam_count": c_exams,
                "question_count": c_qs,
                "has_tracks": len(c_tracks) > 0,
                "tracks": c_tracks,
                "notes": m.notes,
            })

        payload = {
            "version": "2.0.0",
            "branches": branches,
            "default_branch": default_branch,
            "default_semester": 1,
            "hierarchy": hierarchy,
        }

        # Run strict validation before writing
        validate_catalog(payload)

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"Successfully generated and validated canonical frontend catalog at: {OUTPUT_PATH}")
        print(f"File size: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")

    finally:
        db.close()


if __name__ == "__main__":
    generate_catalog()
