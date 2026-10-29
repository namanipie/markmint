import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

with open('src/lib/course-resources.json', 'r', encoding='utf-8') as f:
    resources = json.load(f)

with open('data/extracted_cycle_test_questions.json', 'r', encoding='utf-8') as f:
    extracted_qs = json.load(f)

extracted_counts = {}
for q in extracted_qs:
    s = (q.get('subject') or '').strip().lower()
    extracted_counts[s] = extracted_counts.get(s, 0) + 1

resource_ct_counts = {}
for slug, c in resources.items():
    cname = c.get('courseName', '').strip().lower()
    ct_papers = [p for p in c.get('pyqs', []) if p.get('examType') in ['CT1', 'CT2']]
    resource_ct_counts[cname] = len(ct_papers)

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('''
    SELECT c.id, c.name,
           COUNT(CASE WHEN e.assessment_type = 'CT1' THEN q.id END) as ct1_count,
           COUNT(CASE WHEN e.assessment_type = 'CT2' THEN q.id END) as ct2_count
    FROM courses c
    LEFT JOIN exams e ON e.course_id = c.id AND e.assessment_type IN ('CT1', 'CT2')
    LEFT JOIN sections s ON s.exam_id = e.id
    LEFT JOIN questions q ON q.section_id = s.id
    GROUP BY c.id, c.name
    ORDER BY c.id;
''')
db_counts = cur.fetchall()
conn.close()

print(f"{'ID':<3} | {'Course Name':<48} | {'CT Papers':<10} | {'Extracted Qs':<13} | {'DB CT1':<7} | {'DB CT2':<7}")
print("-" * 100)
missing_courses = []
for cid, name, ct1, ct2 in db_counts:
    n_low = name.strip().lower()
    json_p = resource_ct_counts.get(n_low, 0)
    ext_q = extracted_counts.get(n_low, 0)
    print(f"{cid:<3} | {name:<48} | {json_p:<10} | {ext_q:<13} | {ct1:<7} | {ct2:<7}")
    if json_p == 0 or ext_q == 0 or (ct1 == 0 and ct2 == 0):
        missing_courses.append({
            'id': cid,
            'name': name,
            'papers': json_p,
            'extracted': ext_q,
            'db_ct1': ct1,
            'db_ct2': ct2
        })

print(f"\nTotal courses needing CT attention: {len(missing_courses)} of 43")
with open("data/missing_ct_courses.json", "w", encoding="utf-8") as f:
    json.dump(missing_courses, f, indent=2)
