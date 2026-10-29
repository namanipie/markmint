import sys
import os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Topic, Course, Unit, Syllabus

client = TestClient(app)
db = SessionLocal()

courses_to_test = ["SEM1-CALC", "SEM1-CHEM", "SEM1-SPCM", "SEM1-EEE", "SEM1-PROG"]

endpoints = [
    "overview",
    "topics",
    "families",
    "questions/repeated",
    "evolution",
    "marks",
    "assessment-comparison"
]

print("=== RUNNING ANALYTICS ENDPOINTS AUDIT ===")

for ccode in courses_to_test:
    print(f"\n==================== COURSE: {ccode} ====================")
    for ep in endpoints:
        url = f"/api/analytics/{ccode}/{ep}"
        try:
            resp = client.get(url)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                if isinstance(data, list):
                    summary = f"list of {len(data)} items"
                elif isinstance(data, dict):
                    keys = list(data.keys())[:6]
                    summary = f"dict keys={keys}"
                else:
                    summary = str(type(data))
                print(f"  GET {url:45s} -> HTTP {status} | {summary}")
            else:
                print(f"  GET {url:45s} -> HTTP {status} | Error: {resp.text[:100]}")
        except Exception as e:
            print(f"  GET {url:45s} -> EXCEPTION: {e}")

    # Also test topic intelligence if course has topics
    c = db.query(Course).filter(Course.code == ccode).first()
    if c:
        t = db.query(Topic).join(Unit, Topic.unit_id == Unit.id).join(Syllabus, Unit.syllabus_id == Syllabus.id).filter(Syllabus.course_id == c.id).first()
        if t:
            url = f"/api/analytics/{ccode}/topics/{t.id}/intelligence"
            resp = client.get(url)
            status = resp.status_code
            print(f"  GET {url:45s} -> HTTP {status} (Topic {t.id}: {t.name})")

db.close()
