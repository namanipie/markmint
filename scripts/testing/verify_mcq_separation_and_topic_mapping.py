import os, json, urllib.request
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor(cursor_factory=RealDictCursor)

print("==================================================")
print("VERIFICATION SUITE: MCQ SEPARATION & TOPIC MAPPING")
print("==================================================")

# 1. Check Neon DB mixed sections
cur.execute("""
    SELECT s.id, s.name, 
           COUNT(CASE WHEN q.question_type = 'MCQ' THEN 1 END) as mcq_count,
           COUNT(CASE WHEN q.question_type != 'MCQ' OR q.question_type IS NULL THEN 1 END) as non_mcq_count
    FROM sections s
    JOIN questions q ON q.section_id = s.id
    GROUP BY s.id, s.name
    HAVING COUNT(CASE WHEN q.question_type = 'MCQ' THEN 1 END) > 0
       AND COUNT(CASE WHEN q.question_type != 'MCQ' OR q.question_type IS NULL THEN 1 END) > 0
""")
mixed = cur.fetchall()
print(f"1. Mixed Sections in Database: {len(mixed)} (Target: 0)")
assert len(mixed) == 0, f"FAILED: Found {len(mixed)} mixed sections!"
print("   [PASS] Zero mixed sections exist in the database.")

# 2. Check MCQ topic mapping coverage
cur.execute("""
    SELECT 
        COUNT(DISTINCT q.id) as total_mcqs,
        COUNT(DISTINCT qt.question_id) as mcqs_with_topic_mapping
    FROM questions q
    LEFT JOIN question_topic qt ON qt.question_id = q.id
    WHERE q.question_type = 'MCQ'
""")
cov = cur.fetchone()
print(f"2. MCQ Topic Mapping Coverage: {cov['mcqs_with_topic_mapping']} of {cov['total_mcqs']} ({cov['mcqs_with_topic_mapping']/cov['total_mcqs']*100:.2f}%)")
assert cov['mcqs_with_topic_mapping'] == cov['total_mcqs'], "FAILED: Not all MCQs are mapped to topics!"
print("   [PASS] 100% of all MCQs in DB have verified topic mappings.")

# 3. Check Dedicated MCQ Sections created
cur.execute("""
    SELECT COUNT(DISTINCT s.id) as mcq_sections,
           COUNT(DISTINCT s.exam_id) as exams_with_mcq_section
    FROM sections s
    WHERE s.name ILIKE '%multiple choice%' OR s.name ILIKE '%mcq%'
""")
sec_stats = cur.fetchone()
print(f"3. Dedicated MCQ Sections: {sec_stats['mcq_sections']} across {sec_stats['exams_with_mcq_section']} exams.")

# 4. Check API separation for representative courses
test_courses = [
    "Operating Systems",
    "Artificial Intelligence",
    "Compiler Design",
    "Fundamental Of Economics (FOE)",
    "Internet of Things",
    "Computer Networks"
]

print("\n4. Backend API Category Isolation Check:")
for c_name in test_courses:
    encoded = urllib.parse.quote(c_name)
    url_desc = f"http://127.0.0.1:8000/api/practice/cycle-tests/{encoded}?category=descriptive&limit=100"
    res_desc = json.loads(urllib.request.urlopen(url_desc).read())
    desc_qs = res_desc['questions']
    any_mcq_in_desc = any(q.get('is_mcq') is True or q.get('q_type') == 'MCQ' for q in desc_qs)
    
    url_mcq = f"http://127.0.0.1:8000/api/practice/cycle-tests/{encoded}?category=mcq&limit=100"
    res_mcq = json.loads(urllib.request.urlopen(url_mcq).read())
    mcq_qs = res_mcq['questions']
    any_desc_in_mcq = any(not (q.get('is_mcq') is True or q.get('q_type') == 'MCQ') for q in mcq_qs)
    
    print(f"   Course: {c_name:35} | Descriptive: {len(desc_qs)} (MCQ leak: {any_mcq_in_desc}) | MCQs: {len(mcq_qs)} (Desc leak: {any_desc_in_mcq})")
    assert not any_mcq_in_desc, f"MCQ leaked into descriptive questions for {c_name}!"
    assert not any_desc_in_mcq, f"Descriptive leaked into MCQ questions for {c_name}!"

print("   [PASS] Zero cross-contamination between normal questions and MCQs across all test subjects.")

conn.close()
print("\n==================================================")
print("ALL VERIFICATION CHECKS PASSED WITH 100% SUCCESS.")
print("==================================================")
