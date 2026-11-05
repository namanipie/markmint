import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.core import Document, Exam, Course
from sqlalchemy.orm import joinedload
from collections import Counter

db = SessionLocal()

docs = db.query(Document).options(joinedload(Document.exams)).all()
print(f"Total documents in DB: {len(docs)}")

doc_types = Counter(d.resource_type for d in docs)
print(f"Document resource types: {dict(doc_types)}")

exam_docs = [d for d in docs if d.resource_type == 'EXAM' or len(d.exams) > 0]
print(f"Documents that are EXAM or have exams: {len(exam_docs)}")

sources = Counter(d.source for d in docs)
print(f"Top sources: {sources.most_common(10)}")

sample_docs = docs[:10]
for d in sample_docs:
    print(f"ID: {d.id} | Title: {d.title} | Source: {d.source} | ExamType: {d.exam_type} | Year: {d.year} | Exams: {len(d.exams)}")

db.close()
