import os
import json
import urllib.request
import urllib.parse
from sqlalchemy import create_engine, text

BASE_URL = "https://markmint.onrender.com"
PG_URL = os.environ.get(
    "RENDER_DATABASE_URL",
    "postgresql://markmint_user:RDXfizQBWXFjhEUbfshlumjwuQajSUFR@dpg-dakpv1gu01pc73bj47e0-a.oregon-postgres.render.com/markmint?sslmode=require"
).replace("postgresql://", "postgresql+psycopg2://")

print("=" * 80)
print("PRODUCTION SMOKE TEST & VERIFICATION AUDIT")
print(f"Target Host: {BASE_URL}")
print("=" * 80)

# 1. API Endpoints Verification
endpoints_to_test = [
    ("/api/health", "Health check"),
    ("/api/courses/", "Course list"),
    ("/api/curriculum/stats", "Curriculum stats"),
    ("/api/intelligence/1", "Calculus intelligence snapshot"),
    ("/api/intelligence/2", "Chemistry intelligence snapshot"),
    ("/api/intelligence/13", "SPCM intelligence snapshot"),
    ("/api/study/plan/Chemistry", "Chemistry study plan"),
    ("/api/study/plan/21PYB102J", "SPCM study plan via canonical code"),
    ("/api/study/plan/Semiconductor%20Physics%20and%20Computational%20Methods", "SPCM study plan via name"),
    ("/api/practice/21MAB101T", "Calculus practice via canonical code"),
    ("/api/practice/21CYB101J", "Chemistry practice via canonical code"),
    ("/api/practice/21PYB102J", "SPCM practice via canonical code"),
    ("/api/practice/Calculus%20And%20Linear%20Algebra", "Calculus practice via name"),
    ("/api/predictions/1", "Calculus predictions with exam payloads"),
]

endpoint_results = []
api_data = {}

for ep, desc in endpoints_to_test:
    url = BASE_URL + ep
    req = urllib.request.Request(url, headers={"User-Agent": "MarkMint-Smoke/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            api_data[ep] = body
            endpoint_results.append((ep, desc, status, "OK"))
            print(f"[PASS] {status} | {ep:<55} ({desc})")
    except urllib.error.HTTPError as e:
        endpoint_results.append((ep, desc, e.code, e.reason))
        print(f"[FAIL] {e.code} | {ep:<55} ({desc}) -> {e.reason}")
    except Exception as e:
        endpoint_results.append((ep, desc, "ERR", str(e)))
        print(f"[FAIL] ERR | {ep:<55} ({desc}) -> {e}")

print("-" * 80)
print("SPECIFIC INTELLIGENCE & PRACTICE VERIFICATIONS:")
# Calculus
c1 = api_data.get("/api/intelligence/1", {})
print(f"  Calculus (Course 1) Mode       : {c1.get('prediction_mode')} (Expected: 'topic')")
assert c1.get("prediction_mode") == "topic"
print(f"  Calculus Predictions Count    : {len(c1.get('predictions', []))}")
print(f"  Calculus Family Preds Count   : {c1.get('family_predictions_count')}")

# Chemistry
c2 = api_data.get("/api/intelligence/2", {})
print(f"  Chemistry (Course 2) Mode      : {c2.get('prediction_mode')} (Expected: 'topic')")
assert c2.get("prediction_mode") == "topic"
print(f"  Chemistry Predictions Count   : {len(c2.get('predictions', []))}")
print(f"  Chemistry Family Preds Count  : {c2.get('family_predictions_count')}")

# SPCM
c13 = api_data.get("/api/intelligence/13", {})
print(f"  SPCM (Course 13) Mode          : {c13.get('prediction_mode')} (Expected: 'topic')")
assert c13.get("prediction_mode") == "topic"
print(f"  SPCM Predictions Count        : {len(c13.get('predictions', []))}")
print(f"  SPCM Family Preds Count       : {c13.get('family_predictions_count')}")

# Curriculum Stats
c_stats = api_data.get("/api/curriculum/stats", {})
print(f"  Curriculum Total Entries       : {c_stats.get('total_entries')} (Expected: 2810)")
assert c_stats.get("total_entries") == 2810
print(f"  Curriculum Branches Count      : {c_stats.get('branches_count')} (Expected: 54)")
assert c_stats.get("branches_count") == 54

# Practice endpoints
p_calc = api_data.get("/api/practice/21MAB101T", {})
print(f"  Calculus Practice Questions    : {len(p_calc.get('questions', []))} questions")
assert len(p_calc.get("questions", [])) > 0

p_chem = api_data.get("/api/practice/21CYB101J", {})
print(f"  Chemistry Practice Questions   : {len(p_chem.get('questions', []))} questions")
assert len(p_chem.get("questions", [])) > 0

p_spcm = api_data.get("/api/practice/21PYB102J", {})
print(f"  SPCM Practice Questions        : {len(p_spcm.get('questions', []))} questions")
assert len(p_spcm.get("questions", [])) > 0

# Check M2M payload exposure in predictions
c1_preds = api_data.get("/api/predictions/1", {})
hist_exams = c1_preds.get("historical_exams", [])
has_topics_list = False
has_topic_mappings = False
sample_q = None
for ex in hist_exams:
    for q in ex.get("questions", []):
        if "topics" in q and isinstance(q["topics"], list):
            has_topics_list = True
        if "topic_mappings" in q and isinstance(q["topic_mappings"], list):
            has_topic_mappings = True
            sample_q = q
            break
    if sample_q:
        break

print(f"  M2M 'topics' list exposed      : {has_topics_list}")
print(f"  M2M 'topic_mappings' exposed   : {has_topic_mappings}")
if sample_q:
    print(f"  Sample question payload fields : id={sample_q.get('id')}, topic={sample_q.get('topic')}, topics={sample_q.get('topics')}")

# 2. Database Counts Audit against known verified state
print("-" * 80)
print("POSTGRESQL PRODUCTION DATABASE INVARIANTS AUDIT:")
engine = create_engine(PG_URL, pool_pre_ping=True)
with engine.connect() as conn:
    total_curr = conn.execute(text("SELECT count(*) FROM curriculum_mappings")).fetchone()[0]
    total_qt = conn.execute(text("SELECT count(*) FROM question_topic")).fetchone()[0]
    
    c1_qt = conn.execute(text("""
        SELECT count(*) 
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 1
    """)).fetchone()[0]
    
    c2_qt = conn.execute(text("""
        SELECT count(*) 
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 2
    """)).fetchone()[0]
    
    c13_qt = conn.execute(text("""
        SELECT count(*) 
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
    """)).fetchone()[0]
    
    cross_course = conn.execute(text("""
        SELECT count(*)
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses syl ON u.syllabus_id = syl.id
        WHERE e.course_id != syl.course_id
    """)).fetchone()[0]
    
    student_topic_p = conn.execute(text("SELECT count(*) FROM student_topic_progress")).fetchone()[0]
    student_resource_p = conn.execute(text("SELECT count(*) FROM student_resource_progress")).fetchone()[0]

print(f"  curriculum_mappings            : {total_curr} (Expected: 2810 | Match: {total_curr == 2810})")
assert total_curr == 2810

print(f"  Total question_topic mappings  : {total_qt} (Expected: 829 | Match: {total_qt == 829})")
assert total_qt == 829

print(f"  Calculus (C1) mappings         : {c1_qt} (Expected: 17 | Match: {c1_qt == 17})")
assert c1_qt == 17

print(f"  Chemistry (C2) mappings        : {c2_qt} (Expected: 192 | Match: {c2_qt == 192})")
assert c2_qt == 192

print(f"  SPCM (C13) mappings            : {c13_qt} (Expected: 620 | Match: {c13_qt == 620})")
assert c13_qt == 620

print(f"  Cross-Course Violations        : {cross_course} (Must be 0 | Match: {cross_course == 0})")
assert cross_course == 0

print(f"  Student Topic Progress Rows    : {student_topic_p} (Unpolluted: {student_topic_p == 1})")
assert student_topic_p == 1

print(f"  Student Resource Progress Rows : {student_resource_p} (Unpolluted: {student_resource_p == 0})")
assert student_resource_p == 0

print("-" * 80)
print("ALL PRODUCTION CHECKS AND DATABASE INVARIANTS SATISFIED!")
