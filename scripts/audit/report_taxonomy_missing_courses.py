"""
Phase 11: Taxonomy-Missing Courses Boundary Report.
Inspects and records courses that require authoritative syllabus onboarding
and stops them at the taxonomy boundary without inventing taxonomy.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus
from backend.services.taxonomy_registry import get_taxonomy_registry


def generate_boundary_report():
    db = SessionLocal()
    reg = get_taxonomy_registry()

    missing_courses = ["SEM1-FORE", "21PYB101J", "21PYB103J"]
    print("=" * 80)
    print("PHASE 11: TAXONOMY-MISSING COURSES BOUNDARY REPORT")
    print("=" * 80)

    report_data = []

    for code in missing_courses:
        c = db.query(Course).filter((Course.canonical_code == code) | (Course.code == code)).first()
        if not c:
            continue
        syl = db.query(Syllabus).filter(Syllabus.course_id == c.id).first()
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).all() if syl else []
        topics = db.query(Topic).join(Unit).filter(Unit.syllabus_id == syl.id).all() if syl else []
        has_reg = reg.has_course(c.id)

        qs = db.query(Question).join(Section).join(Exam).filter(Exam.course_id == c.id).all()
        unmapped = [q for q in qs if len(q.topics) == 0]

        reg_status = "REGISTERED" if has_reg else "UNREGISTERED (Missing Declarative JSON)"
        syl_source = f"Syllabus Version: {syl.version}" if syl else "No syllabus record in database"

        rec = {
            "course": f"{c.name} ({c.canonical_code or c.code}) [ID {c.id}]",
            "syllabus_source": syl_source,
            "unit_count": len(units),
            "unit_names": [u.name for u in units],
            "topic_count": len(topics),
            "taxonomy_registry_status": reg_status,
            "authentic_question_count": len(qs),
            "unmapped_question_count": len(unmapped),
        }
        report_data.append(rec)

        print(f"Course: {rec['course']}")
        print(f"  Syllabus Source:          {rec['syllabus_source']}")
        print(f"  Unit Count:               {rec['unit_count']} (Names: {rec['unit_names']})")
        print(f"  Topic Count:              {rec['topic_count']}")
        print(f"  Taxonomy Registry Status: {rec['taxonomy_registry_status']}")
        print(f"  Authentic Question Count: {rec['authentic_question_count']}")
        print(f"  Unmapped Question Count:  {rec['unmapped_question_count']}")
        print("  Boundary Status:          HALTED AT TAXONOMY BOUNDARY (No auto-mapping or fake taxonomy)")
        print()

    db.close()
    return report_data


if __name__ == "__main__":
    generate_boundary_report()
