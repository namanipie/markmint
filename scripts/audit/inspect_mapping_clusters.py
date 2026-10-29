"""
Inspects the largest unresolved clusters of authentic exam questions.
Shows course, assessment, year range, question count, sample questions,
existing syllabus taxonomy, and failure causes.
"""

import os
import sys
from typing import Dict, List, Any
from collections import defaultdict
from sqlalchemy.orm import selectinload

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus
from backend.services.observed_assessment_coverage import identify_exam_assessment
from scripts.audit.unmapped_exam_questions import determine_unmapped_reason


def inspect_clusters(course_codes: List[str] = None):
    db = SessionLocal()

    target_codes = course_codes or [
        "21MAB101T", "21MAB102T", "21LEH101T", "21EEB101J",
        "21PYB102J", "21CSC102J", "21CSS101J", "21ECC101J",
        "21PYB101J", "SEM1-FORE"
    ]

    print("=" * 90)
    print("HIGHEST-VALUE AUTHENTIC EXAM MAPPING GAP CLUSTERS")
    print("=" * 90)

    for code in target_codes:
        course = db.query(Course).filter((Course.canonical_code == code) | (Course.code == code)).first()
        if not course:
            continue

        # Get syllabus and topics
        syl = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all() if syl else []
        taxonomy_summary = []
        for u in units:
            topics = db.query(Topic).filter(Topic.unit_id == u.id).all()
            taxonomy_summary.append(f"Unit {u.number} ({u.name}): {[t.name for t in topics]}")

        # Get all unmapped authentic exam questions
        exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.document),
                selectinload(Exam.sections).selectinload(Section.questions).selectinload(Question.topics)
            )
            .filter(Exam.course_id == course.id)
            .all()
        )

        # Group by assessment and year
        clusters = defaultdict(list)
        for ex in exams:
            ident = identify_exam_assessment(ex, course.id)
            for sec in ex.sections:
                for q in sec.questions:
                    if len(q.topics) == 0:
                        reason = determine_unmapped_reason(q, ex)
                        if "PENDING_CLASSIFICATION" in reason or "TAXONOMY_EXPANSION_PENDING" in reason:
                            clusters[(ident.normalized_code, ex.year or "Unknown")].append((ex, q, reason))

        total_unmapped_cluster_qs = sum(len(qs) for qs in clusters.values())
        print(f"\n[{course.canonical_code or course.code}] {course.name}")
        print(f"  Syllabus Taxonomy Units ({len(units)} units):")
        for ts in taxonomy_summary[:3]:
            print(f"    - {ts[:110]}...")
        if len(taxonomy_summary) > 3:
            print(f"    - ... and {len(taxonomy_summary) - 3} more units")
        print(f"  Total Authentic Unmapped Questions in Clusters: {total_unmapped_cluster_qs}")

        # Show top clusters
        sorted_clusters = sorted(clusters.items(), key=lambda x: -len(x[1]))
        for (asmt, yr), qlist in sorted_clusters[:4]:
            print(f"\n  Cluster: Assessment={asmt} | Year={yr} | Count={len(qlist)} questions")
            # Show 3 sample questions
            for ex, q, reason in qlist[:3]:
                txt = (q.original_text or q.normalized_text or "")[:120].replace("\n", " ")
                print(f"    * Q#{q.question_number} (ID {q.id}, Exam {ex.id}): {txt!r}")

    db.close()


if __name__ == "__main__":
    inspect_clusters()
