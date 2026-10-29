"""
Verification script for Render production API across Courses 1-13.
Queries live:
- /api/intelligence/{cid}
- /api/study/plan/{course_or_code}
- /api/practice/{code}
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, Any

BASE_URL = "https://markmint.onrender.com"

COURSES = [
    (1, "Calculus And Linear Algebra", "21MAB101T"),
    (2, "Chemistry", "21CYB101J"),
    (3, "Philosophy Of Engineering", "21GNH101J"),
    (4, "Introduction To Computational Biology", "21BTB102T"),
    (5, "Programming For Problem Solving", "21CSS101J"),
    (6, "Fundamental Of Economics (FOE)", "18MSS101T"),
    (7, "Biomedical Sensors", "21BMB101T"),
    (8, "Foreign Languages", "SEM1-FORE"),
    (9, "Cell Biology", "21BTC102J"),
    (10, "Microbiology", "21BTC201T"),
    (11, "Physical And Analytical Chemistry", "21CHC101J"),
    (12, "Biochemistry", "21BTC101T"),
    (13, "Semiconductor Physics and Computational Methods", "21PYB102J"),
]


def fetch_json(endpoint: str) -> Tuple[int, Dict[str, Any]]:
    url = BASE_URL + endpoint
    req = urllib.request.Request(url, headers={"User-Agent": "MarkMint-Verifier/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    print("=" * 110)
    print(f"LIVE PRODUCTION AUDIT ACROSS ALL 13 FIRST-YEAR COURSES ({BASE_URL})")
    print("=" * 110)
    print(f"{'CID':<3} | {'Course':<32} | {'Code':<10} | {'Status':<22} | {'Pred Mode':<10} | {'Topics':<6} | {'TopPred':<8} | {'FamPred':<8} | {'PlanMode':<9} | {'Practice':<8}")
    print("-" * 135)

    results = []

    for cid, name, code in COURSES:
        # 1. Intelligence
        st_i, data_i = fetch_json(f"/api/intelligence/{cid}")
        avail_status = data_i.get("data_availability_status", f"ERR_{st_i}")
        pred_mode = data_i.get("prediction_mode", "N/A")
        top_cnt = data_i.get("taxonomy_topic_count", 0)
        t_preds = data_i.get("topic_predictions_count", 0)
        f_preds = data_i.get("family_predictions_count", 0)

        # 2. Study plan
        encoded_name = urllib.parse.quote(name)
        st_s, data_s = fetch_json(f"/api/study/plan/{encoded_name}")
        plan_mode = data_s.get("plan_mode", "error") if st_s == 200 else f"HTTP_{st_s}"

        # 3. Practice
        st_p, data_p = fetch_json(f"/api/practice/{code}")
        q_count = len(data_p.get("questions", [])) if st_p == 200 else 0
        practice_str = f"{q_count} Qs" if st_p == 200 else f"HTTP_{st_p}"

        print(f"{cid:<3} | {name[:32]:<32} | {code:<10} | {avail_status:<22} | {pred_mode:<10} | {top_cnt:<6} | {t_preds:<8} | {f_preds:<8} | {plan_mode:<9} | {practice_str:<8}")

        results.append({
            "cid": cid,
            "name": name,
            "code": code,
            "avail_status": avail_status,
            "pred_mode": pred_mode,
            "top_cnt": top_cnt,
            "t_preds": t_preds,
            "f_preds": f_preds,
            "plan_mode": plan_mode,
            "practice": practice_str,
        })

    print("=" * 135)


if __name__ == "__main__":
    from typing import Tuple
    main()
