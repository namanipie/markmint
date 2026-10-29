import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.prediction.backtester import BacktestHarness

def main():
    harness = BacktestHarness()
    try:
        report = harness.run()
        meta = report.get("metadata", {})
        print("=== BASELINE BACKTEST SUMMARY ===")
        print(f"Total target exams evaluated: {meta.get('eligible_target_exams_evaluated')}")
        for model_name, data in report.get("model_summary", {}).items():
            avg = data.get("averages", {})
            if avg:
                p5 = avg.get("Precision@5", 0) * 100
                r5 = avg.get("Recall@5", 0) * 100
                m5 = avg.get("Marks Coverage@5", 0) * 100
                print(f"{model_name:<30}: P@5={p5:.1f}%, R@5={r5:.1f}%, Marks@5={m5:.1f}%")
    finally:
        harness.close()

if __name__ == "__main__":
    main()
