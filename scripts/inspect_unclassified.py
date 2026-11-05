import json

with open('data/paper_unit_audit_results.json') as f:
    data = json.load(f)

unclassified = [e for e in data['exams'] if e['category'] == 'UNCLASSIFIED']
print(f"Total unclassified: {len(unclassified)}")

for e in unclassified:
    print(f"ID: {e['exam_id']} | Course: {e['course_code']} ({e['course_name']})")
    print(f"  Title: {e['doc_title']}")
    print(f"  Source: {e['doc_source']}")
    print(f"  Raw AssType: {e['raw_assessment_type']}")
    print(f"  Year: {e['year']} | Term: {e['term']} | Qs: {e['total_questions']} | Marks: {e['total_marks']}")
    print(f"  Units: {e['units_present']}")
    print("-" * 60)
