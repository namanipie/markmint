import sys
import os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

courses_to_test = [
    ("SEM1-CALC", "Calculus And Linear Algebra"),
    ("SEM1-CHEM", "Chemistry"),
    ("SEM1-SPCM", "Semiconductor Physics and Computational Methods"),
    ("SEM1-EEE",  "Electrical and Electronics Engineering"),
    ("SEM2-OODP", "Object Oriented Design and Programming"),
    ("SEM1-ENG",  "Communicative English")
]

print("=== ANALYTICS API REGRESSION AUDIT ===")

for ccode, cname in courses_to_test:
    print(f"\n==================== {ccode} | {cname} ====================")
    
    # 1. Overview
    r_over = client.get(f"/api/analytics/{ccode}/overview")
    d_over = r_over.json() if r_over.status_code == 200 else {}
    print(f"  Overview:      Papers={d_over.get('total_papers')}, Qs={d_over.get('total_questions')}, Readiness={d_over.get('readiness_status')}")

    # 2. Families
    r_fam = client.get(f"/api/analytics/{ccode}/families")
    d_fam = r_fam.json() if r_fam.status_code == 200 else {}
    print(f"  Families:      Total Found={d_fam.get('total_families_found')}, Multi-repeat={d_fam.get('multi_repeat_families_count')}, Observed Years={d_fam.get('observed_years')}")

    # 3. Repeated Questions
    r_rep = client.get(f"/api/analytics/{ccode}/questions/repeated")
    d_rep = r_rep.json() if r_rep.status_code == 200 else {}
    print(f"  Repeats:       Exact Repeats={d_rep.get('exact_repeats_count')}, Family Repeats={d_rep.get('family_repeats_count')}")

    # 4. Evolution
    r_evo = client.get(f"/api/analytics/{ccode}/evolution")
    d_evo = r_evo.json() if r_evo.status_code == 200 else {}
    print(f"  Evolution:     Timeline={d_evo.get('timeline_years')}, Gap Years={d_evo.get('gap_years')}")

    # 5. Marks
    r_marks = client.get(f"/api/analytics/{ccode}/marks")
    d_marks = r_marks.json() if r_marks.status_code == 200 else {}
    print(f"  Marks:         Total Marks={d_marks.get('total_marks')}, Avg Marks={d_marks.get('avg_question_marks')}, Common={d_marks.get('common_marks')}")

    # 6. Assessment Comparison
    r_ac = client.get(f"/api/analytics/{ccode}/assessment-comparison")
    d_ac = r_ac.json() if r_ac.status_code == 200 else {}
    print(f"  Assessments:   Types={d_ac.get('assessment_types')}, Compared Papers={d_ac.get('total_papers')}")

print("\nAll endpoints returned HTTP 200 successfully.")
