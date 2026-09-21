"""
Generates the canonical frontend curriculum catalog (src/data/canonical_curriculum.json)
directly from the database and canonical curriculum catalog.
Ensures zero-latency instant Academic Scope in the Next.js frontend without requiring Render.
"""

import os
import sys
import json
from sqlalchemy import func

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import CurriculumMapping, Course, CourseTrack, Exam, Section, Question

OUTPUT_PATH = os.path.join(BASE_DIR, "src", "data", "canonical_curriculum.json")


def generate_catalog():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    db = SessionLocal()

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
        for t in db.query(CourseTrack).all():
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
            .order_by(CurriculumMapping.branch_name, CurriculumMapping.semester, CurriculumMapping.curriculum_id)
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

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"Successfully generated canonical frontend catalog at: {OUTPUT_PATH}")
        print(f"Total branches: {len(branches)}, total mappings: {len(mappings)}")

    finally:
        db.close()


if __name__ == "__main__":
    generate_catalog()
