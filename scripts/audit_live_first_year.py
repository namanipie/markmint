import urllib.request
import json
import sys

BASE_URL = "https://markmint.onrender.com"

courses = [
    (1, "Calculus And Linear Algebra", "21MAB101T"),
    (2, "Chemistry", "21CYB101J"),
    (3, "Philosophy Of Engineering", "21GNH101J"),
    (4, "Introduction To Computational Biology", "21BTB102T"),
    (5, "Programming For Problem Solving", "21CSS101J"),
    (6, "Fundamental Of Economics (FOE)", "18MSS101T"),
    (7, "Biomedical Sensors", "21BMB101T"),
    (8, "Foreign Languages", None),
    (9, "Cell Biology", "21BTC102J"),
    (10, "Microbiology", "21BTC201T"),
    (11, "Physical And Analytical Chemistry", "21CHC101J"),
    (12, "Biochemistry", "21BTC101T"),
]

print("=" * 100)
print(f"MARKMINT COURSES 1-12 LIVE VERIFICATION AUDIT ON RENDER ({BASE_URL})")
print("=" * 100)

results = []

for cid, name, ccode in courses:
    print(f"\n[{cid:02d}] {name} (Canonical: {ccode})")
    print("-" * 80)
    
    # 1. Intelligence
    intel_url = f"{BASE_URL}/api/intelligence/{cid}"
    intel_data = None
    intel_status = None
    try:
        req = urllib.request.Request(intel_url, headers={"User-Agent": "MarkMint-Verification/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            intel_status = r.status
            intel_data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        intel_status = e.code
    except Exception as e:
        intel_status = str(e)
        
    pred_mode = intel_data.get("prediction_mode") if intel_data else None
    preds_cnt = len(intel_data.get("predictions", [])) if intel_data else 0
    fam_preds_cnt = intel_data.get("family_predictions_count") if intel_data else None
    priorities_cnt = len(intel_data.get("study_priorities", [])) if intel_data else 0
    
    print(f"  Intelligence: Status {intel_status} | Mode: {pred_mode} | Predictions: {preds_cnt} | Family Preds: {fam_preds_cnt} | Study Priorities: {priorities_cnt}")
    
    # 2. Study Plan
    study_target = ccode if ccode else name
    study_url = f"{BASE_URL}/api/study/plan/{urllib.parse.quote(study_target)}"
    study_status = None
    study_priorities_cnt = 0
    try:
        req = urllib.request.Request(study_url, headers={"User-Agent": "MarkMint-Verification/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            study_status = r.status
            s_data = json.loads(r.read().decode("utf-8"))
            study_priorities_cnt = len(s_data.get("priorities", []))
    except urllib.error.HTTPError as e:
        study_status = e.code
    except Exception as e:
        study_status = str(e)
        
    print(f"  Study Plan  : Status {study_status} | Target: {study_target} | Priorities: {study_priorities_cnt}")

    # 3. Practice
    practice_url = f"{BASE_URL}/api/practice/{urllib.parse.quote(study_target)}"
    practice_status = None
    practice_q_cnt = 0
    try:
        req = urllib.request.Request(practice_url, headers={"User-Agent": "MarkMint-Verification/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            practice_status = r.status
            p_data = json.loads(r.read().decode("utf-8"))
            practice_q_cnt = len(p_data.get("questions", [])) if isinstance(p_data, dict) else len(p_data)
    except urllib.error.HTTPError as e:
        practice_status = e.code
    except Exception as e:
        practice_status = str(e)

    print(f"  Practice    : Status {practice_status} | Questions Available: {practice_q_cnt}")

    results.append({
        "cid": cid,
        "name": name,
        "ccode": ccode,
        "intel_status": intel_status,
        "pred_mode": pred_mode,
        "preds_cnt": preds_cnt,
        "study_status": study_status,
        "study_priorities": study_priorities_cnt,
        "practice_status": practice_status,
        "practice_questions": practice_q_cnt,
    })

print("\n" + "=" * 100)
print("AUDIT SUMMARY TABLE:")
print(f"{'ID':<3} | {'Course Name':<35} | {'Intel':<5} | {'Mode':<8} | {'Preds':<5} | {'Study':<5} | {'Practice':<8}")
print("-" * 100)
for r in results:
    print(f"{r['cid']:<3} | {r['name'][:35]:<35} | {str(r['intel_status']):<5} | {str(r['pred_mode']):<8} | {r['preds_cnt']:<5} | {str(r['study_status']):<5} | {str(r['practice_status']):<8}")
print("=" * 100)
