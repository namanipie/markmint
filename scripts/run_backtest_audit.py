"""
Audit script for MarkMint Phase 11 Rigorous Prediction Backtesting.

Runs BacktestHarness and prints structured summaries:
- Overall metadata and coverage
- Metrics breakdown by model
- Metrics breakdown by assessment cycle
- Metrics breakdown by evidence sufficiency tier (Sufficient vs Limited)
- Sparse data / insufficient evidence analysis
"""

import sys
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.prediction.backtester import BacktestHarness

def run_audit():
    print("=" * 100)
    print("MARKMINT PHASE 11: RIGOROUS PREDICTION BACKTESTING AUDIT")
    print("=" * 100)

    harness = BacktestHarness()
    try:
        report = harness.run()
    finally:
        harness.close()

    meta = report.get("metadata", {})
    model_summary = report.get("model_summary", {})
    cycle_summary = report.get("cycle_summary", {})
    sufficiency_summary = report.get("sufficiency_summary", {})
    sparse_cases = report.get("sparse_cases", [])
    detailed = report.get("detailed_evaluations", [])

    print("\n" + "=" * 100)
    print("1. BACKTEST COVERAGE OVERVIEW")
    print("=" * 100)
    print(f"Total Courses Evaluated:         {meta.get('total_courses_evaluated')}")
    print(f"Eligible Target Exams Evaluated: {meta.get('eligible_target_exams_evaluated')}")
    print(f"Total Model Evaluation Records:  {meta.get('total_evaluation_records')}")
    print(f"Total Sparse / Excluded Cases:   {meta.get('total_sparse_cases')}")
    print(f"Probability Calibration Formula: {meta.get('probability_calibration_formula')}")

    print("\n" + "=" * 100)
    print("2. METRICS BY PREDICTION MODEL (Topic Mode across all evaluated targets)")
    print("=" * 100)
    print(f"{'Model Name':<28} | {'Evals':<5} | {'P@3':<7} | {'P@5':<7} | {'P@10':<7} | {'R@5':<7} | {'Marks@5':<8} | {'Q_Cov@5':<8}")
    print("-" * 100)
    for model_name, data in model_summary.items():
        evals = data.get("evaluation_count", 0)
        avg = data.get("averages")
        if isinstance(avg, dict):
            p3 = f"{avg.get('Precision@3', 0.0)*100:.1f}%"
            p5 = f"{avg.get('Precision@5', 0.0)*100:.1f}%"
            p10 = f"{avg.get('Precision@10', 0.0)*100:.1f}%"
            r5 = f"{avg.get('Recall@5', 0.0)*100:.1f}%"
            m5 = f"{avg.get('Marks_Coverage@5', 0.0)*100:.1f}%"
            q5 = f"{avg.get('Question_Coverage@5', 0.0)*100:.1f}%"
            print(f"{model_name:<28} | {evals:<5} | {p3:<7} | {p5:<7} | {p10:<7} | {r5:<7} | {m5:<8} | {q5:<8}")
        else:
            print(f"{model_name:<28} | {evals:<5} | {str(avg)}")

    print("\n" + "=" * 100)
    print("3. METRICS BY ASSESSMENT CYCLE (ExamScopeCombinedModel)")
    print("=" * 100)
    print(f"{'Cycle':<12} | {'Exams':<5} | {'P@3':<7} | {'P@5':<7} | {'P@10':<7} | {'R@5':<7} | {'Marks@5':<8} | {'Q_Cov@5':<8}")
    print("-" * 100)
    for cycle, data in cycle_summary.items():
        exams = data.get("target_exams", 0)
        avg = data.get("averages", {})
        if isinstance(avg, dict) and avg:
            p3 = f"{avg.get('Precision@3', 0.0)*100:.1f}%"
            p5 = f"{avg.get('Precision@5', 0.0)*100:.1f}%"
            p10 = f"{avg.get('Precision@10', 0.0)*100:.1f}%"
            r5 = f"{avg.get('Recall@5', 0.0)*100:.1f}%"
            m5 = f"{avg.get('Marks_Coverage@5', 0.0)*100:.1f}%"
            q5 = f"{avg.get('Question_Coverage@5', 0.0)*100:.1f}%"
            print(f"{cycle:<12} | {exams:<5} | {p3:<7} | {p5:<7} | {p10:<7} | {r5:<7} | {m5:<8} | {q5:<8}")

    print("\n" + "=" * 100)
    print("4. SAMPLE SIZE SUFFICIENCY BREAKDOWN (ExamScopeCombinedModel)")
    print("=" * 100)
    print(f"{'Sufficiency Tier':<22} | {'Evals':<5} | {'P@3':<7} | {'P@5':<7} | {'P@10':<7} | {'R@5':<7} | {'Marks@5':<8} | {'Q_Cov@5':<8}")
    print("-" * 100)
    for tier, data in sufficiency_summary.items():
        evals = data.get("evaluation_count", 0)
        avg = data.get("averages", {})
        if isinstance(avg, dict) and avg:
            p3 = f"{avg.get('Precision@3', 0.0)*100:.1f}%"
            p5 = f"{avg.get('Precision@5', 0.0)*100:.1f}%"
            p10 = f"{avg.get('Precision@10', 0.0)*100:.1f}%"
            r5 = f"{avg.get('Recall@5', 0.0)*100:.1f}%"
            m5 = f"{avg.get('Marks_Coverage@5', 0.0)*100:.1f}%"
            q5 = f"{avg.get('Question_Coverage@5', 0.0)*100:.1f}%"
            print(f"{tier:<22} | {evals:<5} | {p3:<7} | {p5:<7} | {p10:<7} | {r5:<7} | {m5:<8} | {q5:<8}")

    print("\n" + "=" * 100)
    print("5. SAMPLE SPARSE / EXCLUDED CASES (Guardrail Demonstration)")
    print("=" * 100)
    for case in sparse_cases[:5]:
        code = case.get("canonical_code") or f"Course {case.get('course_id')}"
        reason = case.get("reason")
        y = case.get("target_year", "N/A")
        print(f"  - [{code}] Target Year: {y} | Reason: {reason}")
    print(f"  ... Total sparse/isolated cases: {len(sparse_cases)}")
    print("=" * 100)

if __name__ == "__main__":
    run_audit()
