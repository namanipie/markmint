"""
Deep inspection tool for the 8 prioritized courses:
1. SPCM (13)
2. EEE (14)
3. Communicative English (15)
4. Calculus (1)
5. ACCA (16)
6. OODP (17)
7. ESPCB (18)
8. PPS (5)

Extracts all authentic unmapped questions, their text snippets, marks, and
compares against canonical syllabus topics to identify clusters and failure causes.
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

TARGET_COURSES = [
    (13, "21PYB102J", "SPCM"),
    (14, "21EEB101J", "EEE"),
    (15, "21LEH101T", "English"),
    (1, "21MAB101T", "Calculus"),
    (16, "21MAB102T", "ACCA"),
    (17, "21CSC102J", "OODP"),
    (18, "21ECC101J", "ESPCB"),
    (5, "21CSS101J", "PPS"),
]


def inspect_all_targets():
    db = SessionLocal()

    for course_id, code, short_name in TARGET_COURSES:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            print(f"[ERROR] Course {course_id} ({code}) not found")
            continue

        syl = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all() if syl else []
        topics = []
        for u in units:
            top_list = db.query(Topic).filter(Topic.unit_id == u.id).order_by(Topic.id).all()
            for t in top_list:
                topics.append((u.number, u.name, t.id, t.name))

        # Fetch authentic unmapped questions
        exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.document),
                selectinload(Exam.sections).selectinload(Section.questions).selectinload(Question.topics)
            )
            .filter(Exam.course_id == course.id)
            .all()
        )

        authentic_unmapped = []
        for ex in exams:
            ident = identify_exam_assessment(ex, course.id)
            for sec in ex.sections:
                for q in sec.questions:
                    if len(q.topics) == 0:
                        reason = determine_unmapped_reason(q, ex)
                        if "PENDING_CLASSIFICATION" in reason:
                            authentic_unmapped.append({
                                "exam_id": ex.id,
                                "exam_year": ex.year,
                                "assessment": ident.normalized_code,
                                "cycle": ident.student_cycle,
                                "q_id": q.id,
                                "q_num": q.question_number,
                                "marks": q.marks,
                                "text": (q.original_text or q.normalized_text or "").strip(),
                            })

        print("=" * 80)
        print(f"[{code}] {course.name} ({short_name})")
        print(f"  Canonical Units: {len(units)} | Canonical Topics: {len(topics)}")
        print(f"  Authentic Unmapped Questions: {len(authentic_unmapped)}")
        print("=" * 80)

        # Show topics
        print("  Syllabus Topics:")
        for u_num, u_name, t_id, t_name in topics:
            print(f"    - Unit {u_num} [{u_name[:25]}]: Topic {t_id:3d} -> {t_name}")

        # Show sample unmapped questions with text
        print(f"\n  Sample Unmapped Authentic Questions (first 10 of {len(authentic_unmapped)}):")
        for item in authentic_unmapped[:10]:
            clean_text = item["text"][:140].replace("\n", " ")
            print(f"    * Q#{item['q_num']} (ID {item['q_id']}, Exam {item['exam_id']}, {item['assessment']} {item['exam_year']}): {clean_text!r}")
        print("\n")

    db.close()


if __name__ == "__main__":
    inspect_all_targets()
