import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.core import Document, Exam, Question, Course, Unit, Topic, Section
from sqlalchemy.orm import joinedload
from collections import defaultdict, Counter

db = SessionLocal()

# Let's inspect all 475 exams in the database
exams = db.query(Exam).options(
    joinedload(Exam.course),
    joinedload(Exam.document),
    joinedload(Exam.sections).joinedload(Section.questions).joinedload(Question.topics).joinedload(Topic.unit)
).all()

print(f"Total Exam records loaded: {len(exams)}")

exam_categories = defaultdict(list)
exam_types_found = Counter()

for exam in exams:
    course_name = exam.course.name if exam.course else "Unknown Course"
    course_code = exam.course.code if exam.course else "Unknown Code"
    doc_title = exam.document.title if exam.document else (f"Exam_{exam.id}")
    raw_exam_type = (exam.assessment_type or exam.document.exam_type or "").strip()
    
    # Also check if term, doc_title or sections have exam info
    doc_source = exam.document.source if exam.document else ""
    
    # Gather all questions and units in this exam
    units_in_exam = Counter()
    total_marks = 0
    q_count = 0
    for sec in exam.sections:
        for q in sec.questions:
            q_count += 1
            if q.marks:
                total_marks += q.marks
            for t in q.topics:
                u_name = t.unit.name if t.unit else "Unknown Unit"
                units_in_exam[u_name] += (q.marks or 1)
                
    exam_categories[raw_exam_type].append({
        'exam_id': exam.id,
        'course_code': course_code,
        'course_name': course_name,
        'doc_title': doc_title,
        'doc_source': doc_source,
        'year': exam.year or (exam.document.year if exam.document else None),
        'term': exam.term,
        'raw_exam_type': raw_exam_type,
        'q_count': q_count,
        'total_marks': total_marks,
        'units': dict(units_in_exam)
    })
    exam_types_found[raw_exam_type] += 1

print("\n--- Raw Exam Types Breakdown in Database ---")
for etype, count in exam_types_found.most_common():
    print(f"  '{etype}': {count} exams")

# Look closely at UNKNOWN, UNSPECIFIED, None, or ambiguous ones
print("\n--- Examining UNKNOWN / UNSPECIFIED / Empty Types ---")
for item in exam_categories[''] + exam_categories.get('UNKNOWN', []) + exam_categories.get('UNSPECIFIED', []):
    print(f"ID: {item['exam_id']} | Course: {item['course_code']} | Title: {item['doc_title'][:40]} | Year: {item['year']} | Qs: {item['q_count']} | Marks: {item['total_marks']}")

db.close()
