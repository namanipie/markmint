"""
Detailed inspection and classification tool for Phase 6.4.
Allows deep inspection of Category A questions by course.
"""
import os
import sys
import json
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def load_data():
    path = os.path.join(BASE_DIR, "data", "s3_s4", "phase6_3_audit_report.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def print_course_questions(cid):
    data = load_data()
    qs = [q for q in data["unmapped_questions"] if q["course_id"] == cid and q["diagnostic_category"] == "A"]
    print(f"=== Course {cid}: {qs[0]['course_name'] if qs else ''} ({len(qs)} Category A questions) ===")
    for idx, q in enumerate(qs, 1):
        print(f"[{idx}/{len(qs)}] Q{q['question_id']} (Fam {q.get('family_id')})")
        print(f"Text:\n{q['original_text']}")
        print("-" * 60)

if __name__ == "__main__":
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    print_course_questions(cid)
