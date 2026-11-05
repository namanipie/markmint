import sys, os, re
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import engine
from sqlalchemy import text
from collections import defaultdict, Counter
import json

print("--- EXECUTING COMPREHENSIVE PAPER & UNIT AUDIT ---")

with engine.connect() as conn:
    # 1. Fetch all exams with course and document info
    exams_query = text("""
        SELECT 
            e.id AS exam_id,
            e.assessment_type,
            e.year AS exam_year,
            e.term AS exam_term,
            c.id AS course_id,
            c.code AS course_code,
            c.name AS course_name,
            d.id AS doc_id,
            d.title AS doc_title,
            d.source AS doc_source,
            d.exam_type AS doc_exam_type,
            d.year AS doc_year,
            d.resource_type AS doc_resource_type
        FROM exams e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN documents d ON e.document_id = d.id
        ORDER BY c.code, e.id
    """)
    exams = conn.execute(exams_query).fetchall()

    # 2. Fetch unit distribution for every exam
    unit_query = text("""
        SELECT 
            e.id AS exam_id,
            u.number AS unit_number,
            u.name AS unit_name,
            COUNT(DISTINCT q.id) AS question_count,
            COALESCE(SUM(q.marks), 0) AS total_marks
        FROM exams e
        JOIN sections s ON s.exam_id = e.id
        JOIN questions q ON q.section_id = s.id
        JOIN question_topic qt ON qt.question_id = q.id
        JOIN topics t ON t.id = qt.topic_id
        JOIN units u ON u.id = t.unit_id
        GROUP BY e.id, u.number, u.name
        ORDER BY e.id, u.number
    """)
    unit_rows = conn.execute(unit_query).fetchall()

    # 3. Fetch questions total per exam
    q_totals_query = text("""
        SELECT 
            e.id AS exam_id,
            COUNT(q.id) AS total_questions,
            COALESCE(SUM(q.marks), 0) AS total_marks
        FROM exams e
        JOIN sections s ON s.exam_id = e.id
        JOIN questions q ON q.section_id = s.id
        GROUP BY e.id
    """)
    exam_q_totals = {r[0]: {'q_count': r[1], 'total_marks': r[2]} for r in conn.execute(q_totals_query).fetchall()}

    # 4. Fetch sample questions from each exam to inspect headers/prompts
    sample_q_query = text("""
        SELECT 
            s.exam_id,
            q.question_number,
            q.original_text,
            q.marks
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        WHERE q.question_number IN ('1', '21', 'Q1', 'Part A') OR q.marks >= 10
        ORDER BY s.exam_id, q.id
    """)
    sample_q_rows = conn.execute(sample_q_query).fetchall()

print(f"Loaded {len(exams)} exams, {len(unit_rows)} unit-exam entries, {len(exam_q_totals)} question totals.")

# Map unit rows by exam_id
exam_units_map = defaultdict(dict)
for r in unit_rows:
    exam_id, u_num, u_name, q_cnt, u_marks = r
    exam_units_map[exam_id][u_num] = {
        'unit_name': u_name,
        'question_count': q_cnt,
        'marks': float(u_marks)
    }

# Function to determine authoritative classification based on text written on paper / document
def determine_exam_category(exam_row):
    assessment_type = (exam_row.assessment_type or "").strip().upper()
    doc_title = (exam_row.doc_title or "").strip()
    doc_source = (exam_row.doc_source or "").strip()
    doc_exam_type = (exam_row.doc_exam_type or "").strip().upper()
    term = (exam_row.exam_term or "").strip().upper()

    combined_text = f"{assessment_type} | {doc_title} | {doc_source} | {doc_exam_type}".upper()

    # Check for Cycle Test 1 / CT1 / CLA 1 / Formative Assessment 1
    if any(k in combined_text for k in ['CT1', 'CT-1', 'CYCLE TEST 1', 'CYCLE TEST - 1', 'CYCLE TEST - I', 'CYCLE TEST I', 'CLA-1', 'CLA1', 'FT1', 'FT-1', 'FT-I', 'INTERNAL ASSESSMENT - I', 'INTERNAL ASSESSMENT - 1', 'FJ-1']):
        if 'CT1-2' in combined_text or 'CT 1,2' in combined_text:
            return 'CT_COMPILATION', 'CT 1 & 2 Combined / Compilation'
        return 'CT1', 'Cycle Test 1 (CT1 / CLA-1)'

    # Check for Cycle Test 2 / CT2 / CLA 2 / Formative Assessment 2
    if any(k in combined_text for k in ['CT2', 'CT-2', 'CYCLE TEST 2', 'CYCLE TEST - 2', 'CYCLE TEST - II', 'CYCLE TEST II', 'CLA-2', 'CLA2', 'CLAT-2', 'CLA-T2', 'FT2', 'FT-2', 'FT-II', 'FT 2']):
        return 'CT2', 'Cycle Test 2 (CT2 / CLA-2)'

    # Check for Cycle Test 3 / Formative Assessment 3 or 4
    if any(k in combined_text for k in ['CT3', 'CT-3', 'CYCLE TEST 3', 'CYCLE TEST - 3', 'CYCLE TEST - III', 'FT IV', 'FT-IV', 'INTERNAL ASSESSMENT - III', 'CLA-3']):
        return 'CT3_OR_FORMATIVE', 'Cycle Test 3 / Formative Assessment (CT3 / FT-IV)'

    # Check for Model Exam
    if any(k in combined_text for k in ['MODEL', 'PRE-SEMESTER', 'MOCK']):
        return 'MODEL_EXAM', 'Model Examination'

    # Check for End Semester
    if any(k in combined_text for k in ['END_SEM', 'ENDSEM', 'END SEMESTER', 'SEMESTER EXAMINATION', 'DEGREE EXAMINATION', 'UNIVERSITY EXAMINATION']) or 'PYQ' in combined_text:
        return 'END_SEMESTER', 'End Semester Examination (Summative)'

    return 'UNCLASSIFIED', f'Unclassified ({combined_text[:30]})'

classified_exams = []
cat_counts = Counter()

for e in exams:
    cat_code, cat_label = determine_exam_category(e)
    cat_counts[cat_code] += 1
    q_info = exam_q_totals.get(e.exam_id, {'q_count': 0, 'total_marks': 0.0})
    units_present = sorted(list(exam_units_map[e.exam_id].keys()))
    
    classified_exams.append({
        'exam_id': e.exam_id,
        'course_code': e.course_code,
        'course_name': e.course_name,
        'year': e.exam_year or e.doc_year,
        'term': e.exam_term,
        'raw_assessment_type': e.assessment_type,
        'doc_title': e.doc_title,
        'doc_source': e.doc_source,
        'category': cat_code,
        'category_label': cat_label,
        'total_questions': q_info['q_count'],
        'total_marks': float(q_info['total_marks']),
        'units_present': units_present,
        'units_breakdown': exam_units_map[e.exam_id]
    })

print("\n--- Categorization of All 475 Exams in Database ---")
for cat, count in cat_counts.most_common():
    print(f"  {cat:20}: {count} papers")

# Now let's analyze unit presence by exam category!
print("\n--- Unit Distribution by Exam Category ---")
cat_unit_dist = defaultdict(lambda: Counter())
cat_course_units = defaultdict(lambda: defaultdict(set))

for item in classified_exams:
    cat = item['category']
    course = item['course_code']
    units = item['units_present']
    for u in units:
        cat_unit_dist[cat][u] += 1
        cat_course_units[cat][course].add(u)

for cat in ['CT1', 'CT2', 'CT3_OR_FORMATIVE', 'MODEL_EXAM', 'END_SEMESTER']:
    total_papers = cat_counts[cat]
    print(f"\n=======================================================")
    print(f"Category: {cat} (Total Papers: {total_papers})")
    print("=======================================================")
    dist = cat_unit_dist[cat]
    for u_num in range(1, 6):
        cnt = dist.get(u_num, 0)
        pct = (cnt / total_papers * 100) if total_papers else 0
        print(f"  Unit {u_num}: present in {cnt}/{total_papers} papers ({pct:.1f}%)")

# Let's save the classified results to a JSON file for deep analysis
with open('data/paper_unit_audit_results.json', 'w') as f:
    json.dump({
        'summary': dict(cat_counts),
        'exams': classified_exams
    }, f, indent=2)

print("\nWrote full audit to data/paper_unit_audit_results.json")
