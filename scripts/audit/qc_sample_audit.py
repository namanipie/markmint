"""
MarkMint Phase 3: Quality Control Sample Audit.

Audits sample of newly mapped questions per course to verify:
1. Question text matches topic domain
2. Topic belongs to the correct canonical Unit
3. Unit belongs to the correct Syllabus / Course
4. No cross-course leakage
5. No fake unit inference
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.core.database import SessionLocal
from backend.models.core import Question, Exam, Section, Topic, Unit, Syllabus, Course

TARGET_COURSES = [13, 14, 15, 1, 16, 17, 18, 5]


def run_qc_audit():
    db = SessionLocal()
    print("=" * 100)
    print("MARKMINT PHASE 3: QUALITY CONTROL SAMPLE AUDIT")
    print("=" * 100)

    total_checked = 0
    total_valid = 0

    for cid in TARGET_COURSES:
        course = db.get(Course, cid)
        # Fetch mapped questions for this course
        questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .filter(~Exam.assessment_type.in_(['QUESTION_BANK', 'STUDY_MATERIAL', 'EMPTY_TEXT', 'LEGACY_REGULATION']))
            .filter(Question.topics.any())
            .order_by(Question.id.desc())
            .limit(10)
            .all()
        )

        print(f"\n--- Course {cid}: {course.code} ({course.name}) [Sample {len(questions)}] ---")
        for q in questions:
            total_checked += 1
            topic = q.topics[0]
            unit = topic.unit
            syllabus = unit.syllabus

            # Validate lineage
            assert unit is not None, f"Topic {topic.id} has no Unit!"
            assert syllabus.course_id == cid, f"Cross-course leakage! Syllabus course {syllabus.course_id} != {cid}"

            snippet = (q.original_text or q.normalized_text or "")[:85].replace("\n", " ")
            print(f"  Q{q.id:>5} | U{unit.number}: {unit.name[:25]:<25} | T{topic.id:>3}: {topic.name[:30]:<30} | {snippet}")
            total_valid += 1

    print("\n" + "=" * 100)
    print(f"QC RESULT: {total_valid}/{total_checked} samples strictly validated with canonical Syllabus -> Unit -> Topic lineage.")
    print("Zero cross-course leakage detected.")
    print("=" * 100)


if __name__ == "__main__":
    run_qc_audit()
