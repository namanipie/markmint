"""
Audit and diagnostic tool for Phase 6.2 Category C questions.
Extracts detailed forensics on all 125 Category C second-year questions:
- Candidate topics and collision reasons
- QuestionFamily sibling mappings
- Stem and options analysis
- Course priority clustering
"""
import os
import sys
import json
from collections import defaultdict
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, Topic, QuestionFamily, question_topic

def audit_category_c():
    report_path = os.path.join(BASE_DIR, "data", "s3_s4", "unmapped_diagnostic_report.json")
    if not os.path.exists(report_path):
        print("unmapped_diagnostic_report.json not found!")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cat_c_questions = [q for q in data.get("questions", []) if q.get("category") == "C_AMBIGUOUS_MULTI_TOPIC"]
    print(f"Loaded {len(cat_c_questions)} Category C questions from diagnostic report.")

    db = SessionLocal()
    detailed_records = []

    try:
        # Collect family information
        family_ids = [q["family"]["family_id"] for q in cat_c_questions if q.get("family") and q["family"].get("family_id")]
        
        # Query sibling mappings
        sibling_rows = (
            db.query(Question.id, Question.family_id, Question.original_text, Topic.id, Topic.name)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .filter(Question.family_id.in_(family_ids))
            .all()
        )
        
        family_sibling_map = defaultdict(list)
        for q_id, fam_id, q_text, top_id, top_name in sibling_rows:
            family_sibling_map[fam_id].append({
                "question_id": q_id,
                "topic_id": top_id,
                "topic_name": top_name,
                "text_snippet": q_text[:80]
            })

        for q in cat_c_questions:
            qid = q["question_id"]
            fam_id = q.get("family", {}).get("family_id")
            siblings = family_sibling_map.get(fam_id, [])
            
            # Remove self from siblings if present
            sibling_mapped = [s for s in siblings if s["question_id"] != qid]

            diag = q.get("classifier_diagnosis", {})
            cand_topics = diag.get("candidate_topics", [])
            evidence = diag.get("evidence", [])
            guardrails = diag.get("guardrail_rejections", [])

            rec = {
                "question_id": qid,
                "course_id": q["course_id"],
                "course_name": q["course_name"],
                "course_code": q["course_code"],
                "semester": q["semester"],
                "exam_id": q["exam_id"],
                "assessment_type": q["assessment_type"],
                "year": q["year"],
                "family_id": fam_id,
                "family_name": q.get("family", {}).get("canonical_name"),
                "family_size": q.get("family", {}).get("family_size", 1),
                "mapped_siblings": sibling_mapped,
                "text": q["text"],
                "stem": q.get("stem"),
                "options": q.get("options", []),
                "candidate_topics": cand_topics,
                "evidence": evidence,
                "guardrail_rejections": guardrails
            }
            detailed_records.append(rec)

        # Output to file
        out_path = os.path.join(BASE_DIR, "data", "s3_s4", "category_c_detailed_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(detailed_records, f, indent=2)

        print(f"Exported detailed Category C forensics to: {out_path}")

        # Group by course and print quick summaries
        by_course = defaultdict(list)
        for r in detailed_records:
            by_course[r["course_id"]].append(r)

        COURSE_ORDER = [28, 27, 25, 26, 22, 24, 29]
        for cid in COURSE_ORDER:
            c_recs = by_course.get(cid, [])
            if not c_recs:
                continue
            cname = c_recs[0]["course_name"]
            ccode = c_recs[0]["course_code"]
            print(f"\n=======================================================")
            print(f"Course {cid} ({ccode}) — {cname}: {len(c_recs)} Category C questions")
            print(f"=======================================================")
            for r in c_recs:
                cands = [c.get("topic_name") for c in r.get("candidate_topics", [])]
                sib_topics = list({s["topic_name"] for s in r.get("mapped_siblings", [])})
                print(f"  Q{r['question_id']} (Fam {r['family_id']}): {r['text'][:70]}...")
                print(f"     Candidates: {cands}")
                print(f"     Sibling topics: {sib_topics}")
                if r.get("guardrail_rejections"):
                    print(f"     Guardrails: {r['guardrail_rejections'][:2]}")

    finally:
        db.close()

if __name__ == "__main__":
    audit_category_c()
