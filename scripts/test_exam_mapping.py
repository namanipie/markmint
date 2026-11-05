import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.core import Document, Exam, Question, Course, Unit, Topic, Section, question_topic
from sqlalchemy.orm import joinedload
from collections import defaultdict, Counter

db = SessionLocal()

# Check question to unit mapping in DB
print("Checking Question -> Topic -> Unit mappings...")
sample_exam = db.query(Exam).first()
if sample_exam:
    print(f"Sample Exam ID: {sample_exam.id}, Year: {sample_exam.year}, Term: {sample_exam.term}, Assessment: {sample_exam.assessment_type}")
    if sample_exam.course:
        print(f"  Course: {sample_exam.course.code} - {sample_exam.course.name}")
    if sample_exam.document:
        print(f"  Document: {sample_exam.document.title} (type: {sample_exam.document.exam_type})")
    
    questions = db.query(Question).join(Section).filter(Section.exam_id == sample_exam.id).all()
    print(f"  Questions count: {len(questions)}")
    for q in questions[:3]:
        topics = [t.name for t in q.topics]
        units = [t.unit.name if t.unit else "No Unit" for t in q.topics]
        print(f"    Q{q.question_number} ({q.marks}m): {q.original_text[:60]}... | Topics: {topics} | Units: {units}")

db.close()
