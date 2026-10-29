import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)

import json
from collections import defaultdict

with open("data/s3_s4/unmapped_diagnostic_report.json", "r", encoding="utf-8") as f:
    data = json.load(f)

a_qs = [q for q in data["questions"] if q["category"] == "A_GENUINE_TAXONOMY_GAP"]
print(f"Total Category A questions: {len(a_qs)}")

by_course = defaultdict(list)
for q in a_qs:
    by_course[q["course_id"]].append(q)

for cid in sorted(by_course.keys()):
    qs = by_course[cid]
    cname = qs[0]["course_name"]
    code = qs[0]["course_code"]
    print(f"\n=======================================================")
    print(f"Course {cid} ({code}) - {cname} [{len(qs)} questions in Category A]")
    print(f"=======================================================")
    for q in qs[:8]:
        print(f"  QID {q['question_id']}: {repr(q['text'][:100])}")
