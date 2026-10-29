import sys
import os
import time
sys.path.insert(0, os.path.abspath("."))

from backend.core.database import SessionLocal
from backend.models.core import Course, QuestionFamily, QuestionFamilyMembership, Question, Exam, Section
from backend.services.families.manager import QuestionFamilyManager
from backend.services.question_classifier import LocalTransformerProvider

print("Initializing SentenceTransformer embedding provider...")
t0 = time.time()
provider = LocalTransformerProvider()
print(f"Provider initialized in {time.time() - t0:.2f}s")

db = SessionLocal()
manager = QuestionFamilyManager(db, provider)

try:
    # Baseline stats
    init_fams = db.query(QuestionFamily).count()
    init_mems = db.query(QuestionFamilyMembership).count()
    init_unassigned = db.query(Question).filter(Question.family_id == None).count()
    print(f"\nBaseline before rebuild:")
    print(f"  Families:    {init_fams}")
    print(f"  Memberships: {init_mems}")
    print(f"  Unassigned:  {init_unassigned}")

    courses = db.query(Course).order_by(Course.id).all()
    print(f"\nProcessing Question Families across {len(courses)} courses...")

    for c in courses:
        c_start = time.time()
        unassigned_in_c = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == c.id)
            .filter(Question.family_id == None)
            .count()
        )
        if unassigned_in_c == 0:
            print(f"Course {c.id:2d} ({c.code}): 0 unassigned questions, skipping.")
            continue

        print(f"\nProcessing Course {c.id:2d} | {c.code:12s} | {c.name} ({unassigned_in_c} unassigned)...")
        manager.process_course_questions(course_id=c.id, subject_name=c.name)
        
        # Intermediate check
        c_fams = db.query(QuestionFamily).filter(QuestionFamily.subject == c.name).count()
        c_mems = (
            db.query(QuestionFamilyMembership)
            .join(QuestionFamily, QuestionFamilyMembership.family_id == QuestionFamily.id)
            .filter(QuestionFamily.subject == c.name)
            .count()
        )
        print(f"Course {c.id:2d} complete in {time.time() - c_start:.2f}s. Subject families: {c_fams}, memberships: {c_mems}")

    final_fams = db.query(QuestionFamily).count()
    final_mems = db.query(QuestionFamilyMembership).count()
    final_unassigned = db.query(Question).filter(Question.family_id == None).count()

    print("\n==================================================")
    print("QUESTION FAMILY REBUILD SUMMARY")
    print("==================================================")
    print(f"Families:    {init_fams} -> {final_fams} (+{final_fams - init_fams})")
    print(f"Memberships: {init_mems} -> {final_mems} (+{final_mems - init_mems})")
    print(f"Unassigned:  {init_unassigned} -> {final_unassigned} (remaining unassigned: {final_unassigned})")

finally:
    db.close()
