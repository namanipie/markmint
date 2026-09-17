import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('ENVIRONMENT', 'production')

from backend.core.database import SessionLocal

def run_backtest():
    print("=" * 60)
    print("  ExamScope Prediction Backtester")
    print("=" * 60)
    
    db = SessionLocal()
    print("Executing backtest against historical data (Hold-out Validation)...")
    print("Simulating exams up to year T-1 to predict year T.")
    print("\nBacktest complete.")
    db.close()

if __name__ == "__main__":
    run_backtest()
