import time
import os
import sys
sys.path.insert(0, os.path.abspath("."))
from backend.core.database import SessionLocal
from backend.models.core import Course
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.study_intelligence import StudyIntelligenceService
from backend.api.endpoints.predictions import _build_historical_exam_payloads

db = SessionLocal()
course = db.query(Course).filter(Course.id == 2).first() # Chemistry

print(f"Profiling internal components for Chemistry (Course 2)...")

# 1. HistoricalContext & HistoricalRepository
t0 = time.perf_counter()
context = HistoricalContext(course_id=2, cutoff_year=2025)
repo = HistoricalRepository(db, context)
hist_exams = repo.get_historical_exams()
t1 = time.perf_counter()
print(f"1. Repository get_historical_exams: {(t1-t0)*1000:.1f}ms ({len(hist_exams)} exams)")

# 2. Build exam payloads
t0 = time.perf_counter()
hist_dicts = _build_historical_exam_payloads(hist_exams)
t1 = time.perf_counter()
print(f"2. _build_historical_exam_payloads: {(t1-t0)*1000:.1f}ms")

# 3. DNA Analyzer
t0 = time.perf_counter()
analyzer = DNAAnalyzerService()
dna = analyzer.analyze(hist_dicts)
t1 = time.perf_counter()
print(f"3. DNAAnalyzerService.analyze: {(t1-t0)*1000:.1f}ms")

# 4. Prediction Model
t0 = time.perf_counter()
model = ExamScopeCombinedModel(dna)
preds = model.predict(top_n=10)
t1 = time.perf_counter()
print(f"4. ExamScopeCombinedModel.predict: {(t1-t0)*1000:.1f}ms ({len(preds)} predictions)")

# 5. StudyIntelligenceService
t0 = time.perf_counter()
study_service = StudyIntelligenceService(db)
priorities = study_service.get_study_priorities(course_id=2, student_id="anonymous", target_year=None)
t1 = time.perf_counter()
print(f"5. StudyIntelligenceService.get_study_priorities: {(t1-t0)*1000:.1f}ms ({len(priorities)} priorities)")

db.close()
