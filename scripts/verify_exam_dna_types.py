"""
Verification of Exam DNA Question Type Breakdown on Production Courses.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Course

def verify_courses():
    client = TestClient(app)
    db = SessionLocal()
    target_courses = [
        "Calculus And Linear Algebra",
        "Chemistry",
        "Programming For Problem Solving",
        "Database Management Systems"
    ]

    for cname in target_courses:
        course = db.query(Course).filter(Course.name == cname).first()
        if not course:
            print(f"Course {cname} not found!")
            continue

        resp = client.get(f"/api/analysis/dna?course_id={course.id}")
        assert resp.status_code == 200, f"Error {resp.status_code}: {resp.text}"
        data = resp.json()

        print(f"\n{'='*70}")
        print(f"EXAM DNA: {cname} (Course ID: {course.id})")
        print(f"{'='*70}")
        sample = data["sample_size"]
        years = sample.get("time_range_years", [])
        y_range = f"{years[0]} - {years[-1]}" if years else "None"
        print(f"Dataset: {sample['papers']} exams | {sample['questions']} questions | Range: {y_range}")
        print(f"Data Sufficiency: {sample['sufficiency'].upper()}")
        print("\nHistorical Question Type Breakdown:")
        for qt in data["question_types"]:
            q_name = qt["question_type"]
            cnt = qt["count"]
            pct = qt["percentage"] * 100
            mw = qt["marks_weighting"] * 100
            print(f"  {q_name:<32}: count={cnt:>3} ({pct:>5.1f}%) | marks_weight={mw:>5.1f}%")

    db.close()

if __name__ == "__main__":
    verify_courses()
