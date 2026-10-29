import json
from collections import defaultdict

with open("data/s3_s4/unmapped_diagnostic_report.json", "r", encoding="utf-8") as f:
    data = json.load(f)

b_qs = [q for q in data["questions"] if q["category"] == "B_EXISTING_TOPIC_REJECTED"]
print(f"Total Category B questions: {len(b_qs)}")

by_course = defaultdict(list)
for q in b_qs:
    by_course[q["course_id"]].append(q)

for cid in [22, 24]:
    if cid not in by_course: continue
    qs = by_course[cid]

    cname = qs[0]["course_name"]
    code = qs[0]["course_code"]
    print(f"\n=======================================================")
    print(f"Course {cid} ({code}) - {cname} [{len(qs)} questions]")
    print(f"=======================================================")
    for q in qs:
        diag = q["classifier_diagnosis"]
        print(f"QID {q['question_id']}:")
        print(f"  Text: {repr(q['text'][:120])}")
        print(f"  Confidence: {diag.get('confidence')} | Method: {diag.get('method')}")
        if diag.get("guardrail_rejections"):
            print(f"  Guards: {diag['guardrail_rejections']}")
        if diag.get("candidate_topics"):
            print(f"  Candidates: {diag['candidate_topics']}")
        if diag.get("stem_proposal") and diag["stem_proposal"].get("confidence") in ["HIGH", "MEDIUM"]:
            print(f"  Stem Proposal: {diag['stem_proposal']}")

