import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.core import Document, Exam, Question, Course, Unit, Topic, Section, question_topic
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
from sqlalchemy.orm import joinedload
from collections import defaultdict, Counter

db = SessionLocal()

print("--- EXAM & DOCUMENT SUMMARY FROM DATABASE ---")
exams = db.query(Exam).options(joinedload(Exam.course), joinedload(Exam.document)).all()
print(f"Total Exam records in DB: {len(exams)}")

exam_types = Counter()
course_exam_counts = defaultdict(lambda: Counter())

for ex in exams:
    c_code = ex.course.code if ex.course else "Unknown"
    doc_title = ex.document.title if ex.document else "No Doc"
    exam_type = ex.assessment_type or "UNSPECIFIED"
    doc_exam_type = ex.document.exam_type if ex.document else "None"
    exam_types[exam_type] += 1
    course_exam_counts[c_code][exam_type] += 1

print("\nExam Assessment Types in DB:")
for k, v in exam_types.most_common():
    print(f"  {k}: {v}")

print(f"\nTotal Courses with Exams: {len(course_exam_counts)}")
for c_code, counts in sorted(course_exam_counts.items())[:10]:
    print(f"  {c_code}: {dict(counts)}")

db.close()
