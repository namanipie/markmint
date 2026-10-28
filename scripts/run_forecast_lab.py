#!/usr/bin/env python3
"""
MintAI Forecast Lab: Empirical Backtesting & Model Evaluation CLI
Usage:
    python scripts/run_forecast_lab.py
    python scripts/run_forecast_lab.py --course 2
    python scripts/run_forecast_lab.py --cycle ENDSEM
    python scripts/run_forecast_lab.py --quick
"""

import os
import sys
import argparse
import json
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.services.prediction.backtester import BacktestHarness, BacktestEvaluator
from backend.models.core import Course


def main():
    parser = argparse.ArgumentParser(description="MintAI Forecast Lab: Reproducible Evaluation Harness")
    parser.add_argument("--course", type=str, default=None, help="Filter by Course ID or Canonical Code")
    parser.add_argument("--cycle", type=str, default=None, help="Filter by Assessment Cycle (ENDSEM, CT1, ALL)")
    parser.add_argument("--target-year", type=int, default=None, help="Specific target year to evaluate")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark on first 3 courses")
    parser.add_argument("--json", type=str, default="data/reports/backtest_results.json", help="Path for JSON results")
    parser.add_argument("--report", type=str, default="data/reports/forecast_evaluation_report.md", help="Path for Markdown report")

    args = parser.parse_args()

    print("==================================================================")
    print("  MarkMint MintAI Forecast Lab: Rolling-Origin Evaluator Harness   ")
    print("==================================================================")

    db = SessionLocal()
    harness = BacktestHarness(db)

    try:
        course_ids = None
        if args.course:
            # Find course by id or code
            c = None
            if args.course.isdigit():
                c = db.query(Course).filter(Course.id == int(args.course)).first()
            if not c:
                c = db.query(Course).filter(Course.canonical_code.ilike(args.course)).first()
            if not c:
                c = db.query(Course).filter(Course.name.ilike(f"%{args.course}%")).first()

            if not c:
                print(f"[ERROR] Course '{args.course}' not found.")
                sys.exit(1)
            course_ids = [c.id]
            print(f"Targeting Course: [{c.id}] {c.name} ({c.canonical_code})")
        elif args.quick:
            courses = db.query(Course).order_by(Course.id.asc()).limit(3).all()
            course_ids = [c.id for c in courses]
            print(f"Running Quick Benchmark on courses: {[c.name for c in courses]}")

        t0 = time.time()

        if args.target_year and course_ids and len(course_ids) == 1:
            print(f"Evaluating specific Target Year: {args.target_year} for Course {course_ids[0]}")
            res = harness.backtest_target_year(
                course_id=course_ids[0],
                target_year=args.target_year,
                assessment_cycle=args.cycle
            )
            print(json.dumps(res, indent=2))
            return

        print("Executing full backtest across historical database records...")
        results = harness.run(course_ids=course_ids)
        elapsed = time.time() - t0

        print(f"\nCompleted in {elapsed:.2f} seconds.")
        print(f"Evaluated {results['metadata']['eligible_target_exams_evaluated']} target exams.")
        print("\n--- Model Benchmark Summary (Topic Ranking) ---")
        print(f"{'Model Name':<32} | {'Evals':<6} | {'P@3':<8} | {'P@5':<8} | {'NDCG@5':<8} | {'M_NDCG@5':<8} | {'M_Cov@5':<8}")
        print("-" * 92)

        for m_name, m_data in results.get("model_summary", {}).items():
            if isinstance(m_data, dict) and "averages" in m_data and isinstance(m_data["averages"], dict):
                avg = m_data["averages"]
                p3 = f"{avg.get('Precision@3', 0.0)*100:.1f}%"
                p5 = f"{avg.get('Precision@5', 0.0)*100:.1f}%"
                ndcg = f"{avg.get('NDCG@5', 0.0):.4f}"
                m_ndcg = f"{avg.get('Marks_NDCG@5', 0.0):.4f}"
                m_cov = f"{avg.get('Marks_Coverage@5', 0.0)*100:.1f}%"
                print(f"{m_name:<32} | {m_data.get('evaluation_count', 0):<6} | {p3:<8} | {p5:<8} | {ndcg:<8} | {m_ndcg:<8} | {m_cov:<8}")

        print("\nArtifacts generated:")
        print(f"  JSON Data:       {args.json}")
        print(f"  Markdown Report: {args.report}")
        print("==================================================================")

    finally:
        harness.close()


if __name__ == "__main__":
    main()
