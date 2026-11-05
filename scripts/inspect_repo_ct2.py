import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository

db = SessionLocal()
ctx = HistoricalContext(course_id=1, cutoff_year=2026, assessment_cycle='CT2')
repo = HistoricalRepository(db, ctx)
exams = repo.get_historical_exams()
print(f"Historical exams for CT2 (Course 1): {len(exams)}")
for ex in exams:
    print(f"Exam ID: {ex.id} | Year: {ex.year} | AssType: {ex.assessment_type} | Doc: {ex.document.title if ex.document else 'No Doc'}")
    qs = repo.get_historical_questions()
    print(f"Total questions retrieved: {len(qs)}")
    for q in qs[:5]:
        print(f"  Q{q.question_number}: {q.original_text[:60]}... | Topics: {[t.name for t in q.topics]}")
    break
db.close()
