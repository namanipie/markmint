import json

with open("data/s3_s4/unmapped_diagnostic_report.json", "r", encoding="utf-8") as f:
    data = json.load(f)

d_qs = [q for q in data["questions"] if q["category"] == "D_FAMILY_SIBLING_MAPPED"]
print(f"=== Category D: Sibling Mapped ({len(d_qs)} questions) ===")
for i, q in enumerate(d_qs[:7], 1):
    s_info = [(s['sibling_id'], [t['name'] for t in s['sibling_topics']]) for s in q['family']['mapped_siblings']]
    print(f"{i}. QID {q['question_id']} Course {q['course_id']} ({q['course_code']}) -> Siblings: {s_info}")
    print(f"   Text: {repr(q['text'][:120])}")
    print(f"   Diagnosis: {q['classifier_diagnosis']}")
    print("-" * 50)

b_qs = [q for q in data["questions"] if q["category"] == "B_EXISTING_TOPIC_REJECTED"]
print(f"\n=== Category B: Existing Topic Rejected ({len(b_qs)} questions) ===")

