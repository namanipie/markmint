"""
Comprehensive End-to-End Audit Script for MarkMint Canonical Academic Data Layer.
Tests:
1. Exact reconciliation counts (TOTAL, MATCHED, AMBIGUOUS, UNMATCHED).
2. Corpus invariants (courses=12, exams=8, questions=223, families=548).
3. API endpoints (branches, semesters, subjects, stats).
4. Subject traces: Calculus, Chemistry, Programming, Physics, Biology, +5 from different branches, +5 unmatched, +3 ambiguous.
5. End-to-end MintAI flow for Calculus, Chemistry, Physics, Biology.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import sqlite3
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

print("=" * 70)
print("1. RECONCILIATION COUNTS AUDIT")
print("=" * 70)
conn = sqlite3.connect("production_corpus.db")
cur = conn.cursor()

cur.execute("SELECT count(*) FROM curriculum_mappings")
total = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM curriculum_mappings WHERE status = 'MATCHED'")
matched = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM curriculum_mappings WHERE status = 'AMBIGUOUS'")
ambiguous = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM curriculum_mappings WHERE status = 'UNMATCHED'")
unmatched = cur.fetchone()[0]

print(f"TOTAL:     {total} (expected 2810)")
print(f"MATCHED:   {matched} (expected 250)")
print(f"AMBIGUOUS: {ambiguous} (expected 40)")
print(f"UNMATCHED: {unmatched} (expected 2520)")
assert total == 2810, f"Total mismatch: {total}"
assert matched == 250, f"Matched mismatch: {matched}"
assert ambiguous == 40, f"Ambiguous mismatch: {ambiguous}"
assert unmatched == 2520, f"Unmatched mismatch: {unmatched}"
print(">> Reconciliation counts check: PASSED (Exact Match)\n")

print("=" * 70)
print("2. CORPUS INVARIANTS AUDIT")
print("=" * 70)
cur.execute("SELECT count(*) FROM courses")
courses_cnt = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM exams")
exams_cnt = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM questions")
questions_cnt = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM question_families")
families_cnt = cur.fetchone()[0]

print(f"courses:           {courses_cnt} (expected 12)")
print(f"exams:             {exams_cnt} (expected 8)")
print(f"questions:         {questions_cnt} (expected 223)")
print(f"question_families: {families_cnt} (expected 548)")
assert courses_cnt == 12
assert exams_cnt == 8
assert questions_cnt == 223
assert families_cnt == 548
print(">> Corpus invariants check: PASSED (All conserved)\n")
conn.close()

print("=" * 70)
print("3. API FLOWS AUDIT")
print("=" * 70)
# Flow 1: GET /api/curriculum/branches
resp = client.get("/api/curriculum/branches")
assert resp.status_code == 200
branches = resp.json()
print(f"GET /api/curriculum/branches: status={resp.status_code}, total={len(branches)}, first_3={branches[:3]}")

# Flow 2: GET /api/curriculum/branches/{branch}/semesters
sample_branch = "Computer Science and Engineering"
resp_sem = client.get(f"/api/curriculum/branches/{sample_branch}/semesters")
assert resp_sem.status_code == 200
semesters = resp_sem.json()
print(f"GET /api/curriculum/branches/{sample_branch}/semesters: status={resp_sem.status_code}, semesters={semesters}")

# Flow 3: GET /api/curriculum/branches/{branch}/semesters/{semester}
resp_sub = client.get(f"/api/curriculum/branches/{sample_branch}/semesters/1")
assert resp_sub.status_code == 200
subjects_sem1 = resp_sub.json()
print(f"GET /api/curriculum/branches/{sample_branch}/semesters/1: status={resp_sub.status_code}, subject_count={len(subjects_sem1)}")

# Flow 4: GET /api/curriculum/stats
resp_stats = client.get("/api/curriculum/stats")
assert resp_stats.status_code == 200
stats = resp_stats.json()
print(f"GET /api/curriculum/stats: {stats}\n")

print("=" * 70)
print("4. REPRESENTATIVE CURRICULUM ENTRIES AUDIT")
print("=" * 70)

# Define list of subjects to audit
targets = [
    ("Calculus", "Aerospace Engineering", 1, "aeros-1-1"),
    ("Chemistry", "Aerospace Engineering", 2, "aeros-2-2"),
    ("Programming", "Aerospace Engineering", 2, "aeros-2-5"),
    ("Physics", "Aerospace Engineering", 1, "aeros-1-2"),
    ("Biology", "Aerospace Engineering", 2, "aeros-2-3"),
    # 5 subjects from different branches
    ("Automobile Component Design", "Automobile Engineering", 6, "autom-6-1"),
    ("Digital Signal Processing", "Biomedical Engineering", 5, "biome-5-1"),
    ("Genetic Engineering", "Biotechnology Computational Biology", 5, "biote-5-0"),
    ("Structural Analysis", "Civil Engineering", 4, "civil-4-1"),
    ("Database Management Systems", "Computer Science and Engineering", 3, "compu-3-2"),
    # 5 UNMATCHED subjects
    ("Engineering Graphics and Design", "Aerospace Engineering", 1, "aeros-1-3"),
    ("Electrical and Electronics Engineering", "Aerospace Engineering", 1, "aeros-1-4"),
    ("Applied Engineering Mechanics", "Aerospace Engineering", 2, "aeros-2-4"),
    ("Aircraft Structures - I", "Aerospace Engineering", 3, "aeros-3-2"),
    ("Propulsion - I", "Aerospace Engineering", 4, "aeros-4-1"),
    # 3 AMBIGUOUS subjects
    ("Biology", "Automobile Engineering", 2, "autom-2-4"),
    ("Biochemistry Laboratory", "Biotechnology Computational Biology", 3, "biote-3-2"),
    ("Cell and Microbiology Laboratory", "Biotechnology Computational Biology", 3, "biote-3-4"),
]

for name, branch, sem, curr_id in targets:
    r = client.get(f"/api/curriculum/branches/{branch}/semesters/{sem}")
    if r.status_code != 200:
        print(f"[FAIL] {branch} sem {sem} returned {r.status_code}")
        continue
    items = r.json()
    item = next((x for x in items if x["curriculum_id"] == curr_id), None)
    if not item:
        # try find by name
        item = next((x for x in items if name.lower() in x["subject_name"].lower()), None)
    
    if item:
        print(f"[{item['status']:<9}] {item['curriculum_id']} -> {item['subject_name'][:35]:<35} | course_id: {str(item['course_id']):<4} | canonical: {str(item['canonical_code']):<10} | has_exams: {str(item['has_exams']):<5} | exams: {item['exam_count']} | Qs: {item['question_count']}")
    else:
        print(f"[NOT FOUND] {name} in {branch} sem {sem}")

print("\n" + "=" * 70)
print("5. MINTAI END-TO-END FLOW AUDIT")
print("=" * 70)

# Trace Calculus
print("\n--- A. CALCULUS TRACE ---")
# 1. Subject in Aero Sem 1
aero_sem1 = client.get("/api/curriculum/branches/Aerospace%20Engineering/semesters/1").json()
calc_subj = next(s for s in aero_sem1 if s["curriculum_id"] == "aeros-1-1")
print(f"1. Curriculum Subject:     {calc_subj['curriculum_id']} -> '{calc_subj['subject_name']}'")
print(f"2. Verified Mapping:       status={calc_subj['status']}, course_id={calc_subj['course_id']}")
print(f"3. Canonical Metadata:     code={calc_subj['canonical_code']}")
assert calc_subj['course_id'] == 1
assert calc_subj['canonical_code'] == "21MAB101T"

# 2. ExamDNA for Course 1
dna_calc = client.get(f"/api/analysis/dna?course_id={calc_subj['course_id']}")
print(f"4. ExamDNA status:         {dna_calc.status_code}")
assert dna_calc.status_code == 200
dna_data = dna_calc.json()
print(f"   ExamDNA papers:         {dna_data['sample_size']['papers']}")
print(f"   ExamDNA questions:      {dna_data['sample_size']['questions']}")
print(f"   ExamDNA exam_types:     {dna_data['sample_size']['exam_types']}")

# 3. Prediction for Course 1
pred_calc = client.get(f"/api/predictions/{calc_subj['course_id']}")
print(f"5. Prediction status:      {pred_calc.status_code}")
assert pred_calc.status_code == 200
pred_data = pred_calc.json()
print(f"   Prediction subject:     {pred_data.get('subject')}")
print(f"   Prediction count:       {len(pred_data.get('predictions', []))}")
print(f"   Top prediction:         {pred_data.get('predictions', [{}])[0].get('name')}")

# Trace Chemistry
print("\n--- B. CHEMISTRY TRACE ---")
# 1. Subject in Aero Sem 2
aero_sem2 = client.get("/api/curriculum/branches/Aerospace%20Engineering/semesters/2").json()
chem_subj = next(s for s in aero_sem2 if s["curriculum_id"] == "aeros-2-2")
print(f"1. Curriculum Subject:     {chem_subj['curriculum_id']} -> '{chem_subj['subject_name']}'")
print(f"2. Verified Mapping:       status={chem_subj['status']}, course_id={chem_subj['course_id']}")
print(f"3. Canonical Metadata:     code={chem_subj['canonical_code']}")
assert chem_subj['course_id'] == 2
assert chem_subj['canonical_code'] == "21CYB101J"

# 2. ExamDNA for Course 2
dna_chem = client.get(f"/api/analysis/dna?course_id={chem_subj['course_id']}")
print(f"4. ExamDNA status:         {dna_chem.status_code}")
assert dna_chem.status_code == 200
dna_chem_data = dna_chem.json()
print(f"   ExamDNA papers:         {dna_chem_data['sample_size']['papers']}")
print(f"   ExamDNA questions:      {dna_chem_data['sample_size']['questions']}")
print(f"   ExamDNA exam_types:     {dna_chem_data['sample_size']['exam_types']}")

# 3. Prediction for Course 2
pred_chem = client.get(f"/api/predictions/{chem_subj['course_id']}")
print(f"5. Prediction status:      {pred_chem.status_code}")
assert pred_chem.status_code == 200
pred_chem_data = pred_chem.json()
print(f"   Prediction subject:     {pred_chem_data.get('subject')}")
print(f"   Prediction count:       {len(pred_chem_data.get('predictions', []))}")
print(f"   Top prediction:         {pred_chem_data.get('predictions', [{}])[0].get('name')}")

# Trace Physics (UNMATCHED)
print("\n--- C. PHYSICS TRACE (UNMATCHED) ---")
phys_subj = next(s for s in aero_sem1 if s["curriculum_id"] == "aeros-1-2")
print(f"1. Curriculum Subject:     {phys_subj['curriculum_id']} -> '{phys_subj['subject_name']}'")
print(f"2. Mapping status:         {phys_subj['status']}, course_id={phys_subj['course_id']}")
assert phys_subj['status'] == "UNMATCHED"
assert phys_subj['course_id'] is None
# Ensure querying predictions or DNA does NOT resolve to Physical Chemistry
res_pred_phys = client.get(f"/api/predictions/{phys_subj['subject_name']}")
print(f"3. Prediction query status: {res_pred_phys.status_code} (Clean 404, not falsely mapped to Physical Chemistry)")
assert res_pred_phys.status_code == 404

# Trace Biology (AMBIGUOUS)
print("\n--- D. BIOLOGY TRACE (AMBIGUOUS) ---")
bio_subj = next(s for s in aero_sem2 if s["curriculum_id"] == "aeros-2-3")
print(f"1. Curriculum Subject:     {bio_subj['curriculum_id']} -> '{bio_subj['subject_name']}'")
print(f"2. Mapping status:         {bio_subj['status']}, course_id={bio_subj['course_id']}, notes={bio_subj['notes']}")
assert bio_subj['status'] == "AMBIGUOUS"
assert bio_subj['course_id'] is None
res_pred_bio = client.get(f"/api/predictions/{bio_subj['subject_name']}")
print(f"3. Prediction query status: {res_pred_bio.status_code} (Clean 404, not falsely mapped to Cell Bio or Comp Bio)")
assert res_pred_bio.status_code == 404

print("\n>> All End-to-End Audits PASSED!")
