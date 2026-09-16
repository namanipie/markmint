"""
Performance and Load Measurement Script for MarkMint Academic Intelligence.
Measures:
- Request latency (min, avg, max, p95) over repeated requests
- Response payload size
- Database query count per snapshot request
- Calculus (Course 1), Chemistry (Course 2), and Large Synthetic Corpus (50 papers)
"""

import os
import sys
import time
import json
import statistics

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from sqlalchemy import event
from backend.main import app
from backend.core.database import engine
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.prediction.context import PredictionTarget

client = TestClient(app)


class QueryCounter:
    def __init__(self):
        self.count = 0

    def __enter__(self):
        self.count = 0
        event.listen(engine, "before_cursor_execute", self._callback)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(engine, "before_cursor_execute", self._callback)

    def _callback(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1


def benchmark_endpoint(path: str, name: str, method: str = "GET", json_data: dict = None, iterations: int = 25) -> dict:
    latencies = []
    payload_size = 0
    query_count = 0

    def call():
        if method == "POST":
            return client.post(path, json=json_data)
        return client.get(path)

    # Warm-up
    warmup_res = call()
    assert warmup_res.status_code == 200, f"Endpoint {path} failed with {warmup_res.status_code}"

    # Measurement with query counting on first iteration
    with QueryCounter() as qc:
        r = call()
        payload_size = len(r.content)
        query_count = qc.count

    for _ in range(iterations):
        t0 = time.perf_counter()
        res = call()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    avg_lat = statistics.mean(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    p95_lat = sorted(latencies)[int(0.95 * len(latencies))]

    # Grade determination
    if avg_lat < 50 and p95_lat < 100:
        grade = "Production-grade"
    elif avg_lat < 150 and p95_lat < 300:
        grade = "Beta-grade"
    else:
        grade = "Development-grade"

    return {
        "name": name,
        "path": path,
        "iterations": iterations,
        "avg_ms": round(avg_lat, 2),
        "min_ms": round(min_lat, 2),
        "max_ms": round(max_lat, 2),
        "p95_ms": round(p95_lat, 2),
        "payload_bytes": payload_size,
        "payload_kb": round(payload_size / 1024, 2),
        "db_query_count": query_count,
        "grade": grade
    }


def benchmark_synthetic_scale(paper_count: int = 50, iterations: int = 10) -> dict:
    exams = []
    for i in range(1, paper_count + 1):
        questions = [
            {"id": f"q_{i}_{j}", "topic": f"Topic_{j}", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5}
            for j in range(1, 11)
        ]
        exams.append({
            "id": f"exam_{i}",
            "year": 2000 + (i % 6),
            "exam_type": "FINAL",
            "questions": questions
        })

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        dna = DNAAnalyzerService.analyze(exams)
        engine = ExamScopeCombinedModel(dna)
        preds = engine.predict(PredictionTarget.TOPIC)
        _ = [p.to_dict() for p in preds]
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    avg_lat = statistics.mean(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    p95_lat = sorted(latencies)[int(0.95 * len(latencies))]

    grade = "Production-grade" if avg_lat < 80 else ("Beta-grade" if avg_lat < 200 else "Development-grade")

    return {
        "name": f"Synthetic Corpus ({paper_count} papers, {paper_count * 10} Qs)",
        "iterations": iterations,
        "avg_ms": round(avg_lat, 2),
        "min_ms": round(min_lat, 2),
        "max_ms": round(max_lat, 2),
        "p95_ms": round(p95_lat, 2),
        "grade": grade
    }


def main():
    print("=" * 75)
    print("  MarkMint Performance & Load Benchmark")
    print("=" * 75)

    results = []
    results.append(benchmark_endpoint("/api/intelligence/1", "Calculus (4 papers, 26 Qs)"))
    results.append(benchmark_endpoint("/api/intelligence/2", "Chemistry (4 papers, 197 Qs)"))
    results.append(benchmark_endpoint("/api/search/", "Discovery Search ('matrix')", method="POST", json_data={"raw_query": "matrix", "limit": 5}, iterations=20))
    synthetic = benchmark_synthetic_scale(50)

    print(f"\n{'Target':<32} | {'Avg (ms)':<9} | {'p95 (ms)':<9} | {'Payload':<10} | {'DB Queries':<10} | {'Grade'}")
    print("-" * 88)
    for r in results:
        queries = str(r["db_query_count"]) if "db_query_count" in r else "N/A"
        print(f"{r['name']:<32} | {r['avg_ms']:<9} | {r['p95_ms']:<9} | {r['payload_kb']} KB    | {queries:<10} | {r['grade']}")

    print(f"{synthetic['name']:<32} | {synthetic['avg_ms']:<9} | {synthetic['p95_ms']:<9} | N/A        | N/A        | {synthetic['grade']}")
    print("-" * 88)

    # Export report
    os.makedirs(os.path.join(BASE_DIR, "data", "reports"), exist_ok=True)
    report_path = os.path.join(BASE_DIR, "data", "reports", "load_benchmark.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"api_benchmarks": results, "synthetic_benchmark": synthetic}, f, indent=2)
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
