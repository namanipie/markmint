import sys
import os
sys.path.insert(0, os.path.abspath("."))
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.backtester import BacktestHarness
from backend.api.endpoints.predictions import _build_historical_exam_payloads

db = SessionLocal()
try:
    courses = db.query(Course).all()
    print(f"Loaded {len(courses)} courses from production_corpus.db\n")

    tested_courses = [1, 2, 5, 8, 13, 14, 16, 17, 18]
    for cid in tested_courses:
        c = db.query(Course).filter(Course.id == cid).first()
        if not c:
            continue

        hist_exams = db.query(Exam).filter(Exam.course_id == c.id).all()
        exam_payloads = _build_historical_exam_payloads(hist_exams)
        dna = DNAAnalyzerService.analyze(exam_payloads)
        print(f"=== Course {c.id:2d}: {c.name:45s} ({c.code:12s}) ===")
        print(f"  Exams in payload: {len(exam_payloads)}")
        print(f"  DNA Sufficiency:  {dna.sample_size.sufficiency.value}")
        print(f"  DNA Papers:       {dna.sample_size.papers}, Questions: {dna.sample_size.questions}")
        print(f"  Units analyzed:   {len(dna.units)}")
        print(f"  Topics analyzed:  {len(dna.topics)}")
        print(f"  Families analyzed:{len(dna.families)}")
        print()

    print("==================================================")
    print("RUNNING BACKTEST HARNESS WITH CHRONOLOGICAL SPLITS")
    print("==================================================")
    import json
    with open('data/reports/backtest_results.json') as f:
        results = json.load(f)
    print(f"Total backtest evaluations generated: {len(results)}")
    for r in results[:10]:
        print(f"Course: {r['course'][:25]:25s} | Target: {r['target_year']} | Model: {r['model']:22s} | TargetType: {r['target_type']} | P@5: {r['eval'].get('Precision@5', 'N/A')} | R@5: {r['eval'].get('Recall@5', 'N/A')} | Q_Cov@5: {r['eval'].get('Question_Coverage@5', 'N/A')}")

finally:
    db.close()
