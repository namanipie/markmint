"""
Database State Audit Script for MarkMint.
Reports:
- courses
- curriculum mappings
- exams
- questions
- topics
- concepts
- question families
- study evidence
- documents
- sections
- question-topic mappings
- exams by course
- questions by course
- questions by year
- questions by assessment type
- mapped/unmapped questions
- unresolved questions
- readiness status per course
"""

import os
import sys
from sqlalchemy import func, distinct

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import (
    Course, CurriculumMapping, Exam, Section, Question, Topic, Concept,
    QuestionFamily, QuestionFamilyMembership, StudyEvidence, Document, question_topic
)

def audit():
    db = SessionLocal()
    try:
        courses_count = db.query(func.count(Course.id)).scalar() or 0
        curr_count = db.query(func.count(CurriculumMapping.id)).scalar() or 0
        exams_count = db.query(func.count(Exam.id)).scalar() or 0
        sections_count = db.query(func.count(Section.id)).scalar() or 0
        questions_count = db.query(func.count(Question.id)).scalar() or 0
        topics_count = db.query(func.count(Topic.id)).scalar() or 0
        concepts_count = db.query(func.count(Concept.id)).scalar() or 0
        families_count = db.query(func.count(QuestionFamily.id)).scalar() or 0
        memberships_count = db.query(func.count(QuestionFamilyMembership.id)).scalar() or 0
        evidences_count = db.query(func.count(StudyEvidence.id)).scalar() or 0
        docs_count = db.query(func.count(Document.id)).scalar() or 0
        qt_count = db.query(func.count()).select_from(question_topic).scalar() or 0

        print("=" * 70)
        print("                 DATABASE STATE AUDIT")
        print("=" * 70)
        print(f"Courses:                 {courses_count}")
        print(f"Curriculum Mappings:     {curr_count}")
        print(f"Exams:                   {exams_count}")
        print(f"Sections:                {sections_count}")
        print(f"Questions:               {questions_count}")
        print(f"Topics:                  {topics_count}")
        print(f"Concepts:                {concepts_count}")
        print(f"Question Families:       {families_count}")
        print(f"Family Memberships:      {memberships_count}")
        print(f"Study Evidence:          {evidences_count}")
        print(f"Documents:               {docs_count}")
        print(f"Question-Topic Mappings: {qt_count}")

        print("\n" + "-" * 70)
        print("1. EXAMS & QUESTIONS BY COURSE")
        print("-" * 70)
        courses = db.query(Course).order_by(Course.id.asc()).all()
        for c in courses:
            c_exams = db.query(Exam).filter(Exam.course_id == c.id).all()
            q_count = (
                db.query(func.count(Question.id))
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .filter(Exam.course_id == c.id)
                .scalar() or 0
            )
            years = sorted(list({e.year for e in c_exams if e.year is not None}))
            readiness = "READY" if len(c_exams) > 0 and q_count > 0 else "CATALOG_ONLY"
            print(f"ID={c.id:<2} | {c.name:<38} | Code: {c.code:<12} | Exams: {len(c_exams)} | Qs: {q_count:<3} | Years: {years} | Status: {readiness}")

        print("\n" + "-" * 70)
        print("2. QUESTIONS BY YEAR")
        print("-" * 70)
        by_year = (
            db.query(Exam.year, func.count(Question.id))
            .join(Section, Section.exam_id == Exam.id)
            .join(Question, Question.section_id == Section.id)
            .group_by(Exam.year)
            .order_by(Exam.year.asc().nullslast())
            .all()
        )
        for y, count in by_year:
            print(f"Year {str(y):<6}: {count} questions")

        print("\n" + "-" * 70)
        print("3. QUESTIONS BY ASSESSMENT TYPE")
        print("-" * 70)
        by_atype = (
            db.query(Exam.assessment_type, func.count(Question.id))
            .join(Section, Section.exam_id == Exam.id)
            .join(Question, Question.section_id == Section.id)
            .group_by(Exam.assessment_type)
            .order_by(Exam.assessment_type.asc().nullslast())
            .all()
        )
        for atype, count in by_atype:
            print(f"Assessment Type '{str(atype):<12}': {count} questions")

        print("\n" + "-" * 70)
        print("4. MAPPING & UNRESOLVED QUESTIONS")
        print("-" * 70)
        mapped_qs = (
            db.query(func.count(distinct(Question.id)))
            .join(Question.topics)
            .scalar() or 0
        )
        unmapped_qs = questions_count - mapped_qs
        unresolved_qs = (
            db.query(func.count(Question.id))
            .filter((Question.needs_review == True) | (Question.classification_confidence < 0.5))
            .scalar() or 0
        )
        print(f"Mapped to >= 1 Topic:    {mapped_qs}")
        print(f"Unmapped Questions:      {unmapped_qs}")
        print(f"Unresolved Questions:    {unresolved_qs}")

    finally:
        db.close()

if __name__ == "__main__":
    audit()
