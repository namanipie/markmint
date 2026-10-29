"""
Forensic audit script for Phase 6.4: Category A questions breakdown and classification.
Inspects all 222 Category A questions against the official syllabi and taxonomy definitions.
Classifies each into:
- A1: Genuine syllabus concept missing from taxonomy
- A2: Existing taxonomy concept with insufficient representation
- A3: Genuinely out-of-syllabus
- A4: Insufficiently informative (truncated, corrupted, or uninterpretable)
- A5: Duplicate/redundant concept
"""
import os
import sys
import json
from collections import defaultdict, Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, Topic, Unit, Course
from backend.services.taxonomy_registry.registry import get_taxonomy_registry

def inspect_all_category_a():
    with open(os.path.join(BASE_DIR, "data", "s3_s4", "phase6_3_audit_report.json"), encoding="utf-8") as f:
        report = json.load(f)

    cat_a = [q for q in report["unmapped_questions"] if q["diagnostic_category"] == "A"]
    print(f"Total Category A questions: {len(cat_a)}")

    by_course = defaultdict(list)
    for q in cat_a:
        by_course[q["course_id"]].append(q)

    registry = get_taxonomy_registry()

    for cid in sorted(by_course.keys()):
        qs = by_course[cid]
        cname = qs[0]["course_name"]
        print(f"\n{'='*80}")
        print(f"COURSE {cid}: {cname} (Total: {len(qs)} unmapped)")
        print(f"{'='*80}")
        
        c_entry = registry.get_course(cid)
        print(f"Units in current taxonomy:")
        for u in c_entry.units:
            print(f"  Unit {u.number}: {u.name} ({len(u.topics)} topics)")
            for t in u.topics:
                print(f"    Topic {t.id}: {t.name}")

        print(f"\nQuestions to audit ({len(qs)}):")
        for idx, q in enumerate(qs, 1):
            text = q["original_text"].replace("\n", " ").strip()
            print(f"[{idx}/{len(qs)}] Q{q['question_id']} (Fam {q.get('family_id')}): {text[:140]}")

if __name__ == "__main__":
    inspect_all_category_a()
