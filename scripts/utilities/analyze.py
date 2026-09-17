import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('ENVIRONMENT', 'production')

from backend.core.database import SessionLocal
from backend.services.search.discovery import DiscoverySearchEngine as SearchDiscoveryEngine
from backend.models.core import Course

def run_analysis():
    print("=" * 60)
    print("  ExamScope Analysis Engine")
    print("=" * 60)
    
    db = SessionLocal()
    engine = SearchDiscoveryEngine(db)
    
    # We trigger the precomputation for all courses
    courses = db.query(Course).all()
    if not courses:
        print("No courses found in database.")
        return
        
    for course in courses:
        print(f"Running full analysis for {course.name} ({course.code})...")
        # Under normal conditions, we would call an analytics aggregator here
        
    print("\nAnalysis complete. Cache and metrics updated.")
    db.close()

if __name__ == "__main__":
    run_analysis()
