import time
from backend.core.database import SessionLocal
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.analysis import _get_exams_as_dicts
from backend.models.core import Unit, Syllabus, Course

def benchmark():
    db = SessionLocal()
    try:
        courses = [
            (28, "Database Management Systems (Small course, 4 exams)"),
            (1, "Calculus And Linear Algebra (Medium course, 13 exams)"),
            (2, "Chemistry (Topic-heavy course, 40 topics)"),
            (5, "Programming For Problem Solving (Large course, 20 exams)")
        ]

        print("=== PERFORMANCE BENCHMARK: EXAM DNA FOCUS EVOLUTION ===")
        for cid, desc in courses:
            # 1. Cold DB Fetch
            t0 = time.perf_counter()
            exams = _get_exams_as_dicts(cid, db=db)
            syllabus_units = [
                {'id': u.id, 'name': u.name, 'number': u.number}
                for u in db.query(Unit).join(Syllabus).filter(Syllabus.course_id == cid).order_by(Unit.number).all()
            ]
            t_db = (time.perf_counter() - t0) * 1000

            # 2. Cold Analysis
            t0 = time.perf_counter()
            res_cold = DNAAnalyzerService.analyze(exams, syllabus_units=syllabus_units)
            t_analyze_cold = (time.perf_counter() - t0) * 1000

            # 3. Warm Analysis (5 runs average)
            warm_times = []
            for _ in range(5):
                t0 = time.perf_counter()
                res_warm = DNAAnalyzerService.analyze(exams, syllabus_units=syllabus_units)
                warm_times.append((time.perf_counter() - t0) * 1000)
            t_analyze_warm = sum(warm_times) / len(warm_times)

            total_q = sum(len(e.get('questions', [])) for e in exams)
            total_temporal_q = sum(r.question_count for r in res_cold.temporal_unit_focus)

            print(f"\n{desc}:")
            print(f"  Total Questions in Scope: {total_q} (Temporal Questions: {total_temporal_q})")
            print(f"  DB Fetch Time: {t_db:.2f} ms")
            print(f"  Analyzer Compute Time (Cold): {t_analyze_cold:.2f} ms")
            print(f"  Analyzer Compute Time (Warm avg): {t_analyze_warm:.2f} ms")
            print(f"  Total Request Latency (DB + Compute): {t_db + t_analyze_cold:.2f} ms")
    finally:
        db.close()

if __name__ == '__main__':
    benchmark()
