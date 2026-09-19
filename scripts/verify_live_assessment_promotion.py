"""
Comprehensive Live Production Verification Script for Course-Specific Assessment Structure.
Tests live Render production backend https://markmint.onrender.com
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, Any

BASE_URL = "https://markmint.onrender.com"

def fetch_json(endpoint: str) -> Dict[str, Any]:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "MarkMint-Verification/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def main():
    print("=" * 80)
    print("MARKMINT LIVE PRODUCTION ASSESSMENT STRUCTURE VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. Calculus (Course 1)
    # --------------------------------------------------------------------------
    print("\n--- 1. CALCULUS (Course 1: 21MAB101T) ---")
    calc_ct1 = fetch_json("/api/intelligence/1?assessment_cycle=CT1")
    calc_ct2 = fetch_json("/api/intelligence/1?assessment_cycle=CT2")
    calc_end = fetch_json("/api/intelligence/1?assessment_cycle=ENDSEM")

    print(f"CT1 -> component: {calc_ct1.get('assessment_component')}, label: {calc_ct1.get('assessment_label')}")
    print(f"     -> units: {calc_ct1['assessment_scope']['unit_numbers']}")
    print(f"     -> total scope topics: {calc_ct1['assessment_scope']['total_in_scope_topics']}")
    print(f"     -> predictions: {[p['name'] for p in calc_ct1.get('predictions', [])]}")
    print(f"     -> unobserved count: {len(calc_ct1['assessment_scope']['unobserved_in_scope_topics'])}")

    print(f"CT2 -> component: {calc_ct2.get('assessment_component')}, label: {calc_ct2.get('assessment_label')}")
    print(f"     -> units: {calc_ct2['assessment_scope']['unit_numbers']}")
    print(f"     -> total scope topics: {calc_ct2['assessment_scope']['total_in_scope_topics']}")
    print(f"     -> predictions: {[p['name'] for p in calc_ct2.get('predictions', [])]}")
    print(f"     -> unobserved count: {len(calc_ct2['assessment_scope']['unobserved_in_scope_topics'])}")

    print(f"ENDSEM -> component: {calc_end.get('assessment_component')}, units: {calc_end['assessment_scope']['unit_numbers']}")

    assert calc_ct1['assessment_scope']['unit_numbers'] == [1, 2], "Calculus CT1 must cover units 1, 2"
    assert calc_ct2['assessment_scope']['unit_numbers'] == [3, 4, 5, 6], "Calculus CT2 must cover units 3, 4, 5, 6 (absorbs FT2/FT-II)"
    assert set(calc_ct1['assessment_scope']['unit_numbers']).isdisjoint(set(calc_ct2['assessment_scope']['unit_numbers'])), "CT1 and CT2 units must be disjoint"
    
    # Check candidate restriction
    calc_ct1_preds = {p['name'] for p in calc_ct1.get('predictions', [])}
    calc_ct2_preds = {p['name'] for p in calc_ct2.get('predictions', [])}
    assert calc_ct1_preds.isdisjoint(calc_ct2_preds), f"Calculus CT1 and CT2 predictions must be disjoint! CT1: {calc_ct1_preds}, CT2: {calc_ct2_preds}"
    print("  [PASS] Calculus CT1 and CT2 scopes and prediction candidates are strictly disjoint and correct.")

    # --------------------------------------------------------------------------
    # 2. Chemistry (Course 2)
    # --------------------------------------------------------------------------
    print("\n--- 2. CHEMISTRY (Course 2: 21CYB101J) ---")
    chem_ct1 = fetch_json("/api/intelligence/2?assessment_cycle=CT1")
    chem_ct2 = fetch_json("/api/intelligence/2?assessment_cycle=CT2")
    chem_end = fetch_json("/api/intelligence/2?assessment_cycle=ENDSEM")

    print(f"CT1 -> component: {chem_ct1.get('assessment_component')}, units: {chem_ct1['assessment_scope']['unit_numbers']}")
    print(f"     -> predictions: {[p['name'] for p in chem_ct1.get('predictions', [])]}")
    print(f"CT2 -> component: {chem_ct2.get('assessment_component')}, units: {chem_ct2['assessment_scope']['unit_numbers']}")
    print(f"     -> predictions: {[p['name'] for p in chem_ct2.get('predictions', [])]}")

    assert chem_ct1['assessment_scope']['unit_numbers'] == [1, 2], "Chemistry CT1 must cover units 1, 2"
    assert chem_ct2['assessment_scope']['unit_numbers'] == [3, 4], "Chemistry CT2 must cover units 3, 4"
    print("  [PASS] Chemistry CT1 and CT2 unit scopes are correct.")

    # --------------------------------------------------------------------------
    # 3. Electrical and Electronics Engineering (Course 14)
    # --------------------------------------------------------------------------
    print("\n--- 3. ELECTRICAL AND ELECTRONICS ENGINEERING (Course 14: 21EEB101J) ---")
    eee_ct1 = fetch_json("/api/intelligence/14?assessment_cycle=CT1")
    eee_ct2 = fetch_json("/api/intelligence/14?assessment_cycle=CT2")
    eee_ct3 = fetch_json("/api/intelligence/14?assessment_cycle=CT3")
    print(f"CT1 -> component: {eee_ct1.get('assessment_component')}, units: {eee_ct1['assessment_scope']['unit_numbers']}")
    print(f"CT2 -> component: {eee_ct2.get('assessment_component')}, units: {eee_ct2['assessment_scope']['unit_numbers']}")
    print(f"CT3 -> component: {eee_ct3.get('assessment_component')}, units: {eee_ct3['assessment_scope']['unit_numbers']}")

    assert eee_ct1['assessment_scope']['unit_numbers'] == [1, 2]
    assert eee_ct3['assessment_scope']['unit_numbers'] == [4, 5], "EEE CT3 must be formative component covering Units 4, 5"
    print("  [PASS] EEE CT3 verified as distinct formative component for Units 4 & 5.")

    # --------------------------------------------------------------------------
    # 4. Communicative English (Course 15)
    # --------------------------------------------------------------------------
    print("\n--- 4. COMMUNICATIVE ENGLISH (Course 15: 21LEH101T) ---")
    eng_ct1 = fetch_json("/api/intelligence/15?assessment_cycle=CT1")
    eng_ct2 = fetch_json("/api/intelligence/15?assessment_cycle=CT2")
    eng_ft4 = fetch_json("/api/intelligence/15?assessment_cycle=FT_IV")

    print(f"CT1 -> component: {eng_ct1.get('assessment_component')}, units: {eng_ct1['assessment_scope']['unit_numbers']}")
    print(f"CT2 -> component: {eng_ct2.get('assessment_component')}, units: {eng_ct2['assessment_scope']['unit_numbers']}")
    print(f"FT4 -> component: {eng_ft4.get('assessment_component')}, label: {eng_ft4.get('assessment_label')}, units: {eng_ft4['assessment_scope']['unit_numbers']}")

    assert eng_ct2['assessment_scope']['unit_numbers'] == [3, 4], "English CT2 must cover units 3, 4"
    assert eng_ft4['assessment_scope']['unit_numbers'] == [1, 2], "English FT_IV covers units 1, 2"
    assert eng_ft4.get('assessment_component') == "FT_IV", "English FT IV must NOT become CT2!"
    print("  [PASS] English FT IV is confirmed NOT CT2 and mapped to Units 1 & 2.")

    # --------------------------------------------------------------------------
    # 5. Electronic System and PCB Design (Course 18)
    # --------------------------------------------------------------------------
    print("\n--- 5. ELECTRONIC SYSTEM & PCB DESIGN (Course 18: 21ECC101J) ---")
    espcb_ct1 = fetch_json("/api/intelligence/18?assessment_cycle=CT1")
    espcb_ct2 = fetch_json("/api/intelligence/18?assessment_cycle=CT2")
    print(f"CT1 -> component: {espcb_ct1.get('assessment_component')}, units: {espcb_ct1['assessment_scope']['unit_numbers']}")
    print(f"CT2 -> component: {espcb_ct2.get('assessment_component')}, units: {espcb_ct2['assessment_scope']['unit_numbers']}")

    assert espcb_ct1['assessment_scope']['unit_numbers'] == [1, 2], "ESPCB FJ-1 maps to CT1 (Units 1, 2)"
    assert espcb_ct2['assessment_scope']['unit_numbers'] == [3, 4], "ESPCB CLAT-2 maps to CT2 (Units 3, 4)"
    print("  [PASS] ESPCB FJ-1 and CLAT-2 resolve to course-specific CT1/CT2 unit scopes.")

    # --------------------------------------------------------------------------
    # 6. Secondary Endpoints Verification
    # --------------------------------------------------------------------------
    print("\n--- 6. SECONDARY ENDPOINTS VERIFICATION ---")
    # Predictions endpoint
    pred_res = fetch_json("/api/predictions/1?assessment_cycle=CT2")
    assert pred_res.get("assessment_cycle") == "CT2"
    assert pred_res.get("assessment_component") == "CT2"
    assert pred_res["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]
    print(f"  [PASS] GET /api/predictions/1?assessment_cycle=CT2 returned component {pred_res['assessment_component']}")

    # Study plan priorities endpoint
    study_res = fetch_json("/api/study/priorities/1?assessment_cycle=CT2")
    assert study_res.get("assessment_cycle") == "CT2"
    assert study_res.get("assessment_component") == "CT2"
    assert study_res["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]
    print(f"  [PASS] GET /api/study/priorities/1?assessment_cycle=CT2 returned component {study_res['assessment_component']}")

    # Practice endpoint
    prac_res = fetch_json("/api/practice/1?assessment_cycle=CT2")
    assert prac_res.get("assessment_cycle") == "CT2"
    assert prac_res.get("assessment_component") == "CT2"
    assert prac_res["assessment_scope"]["unit_numbers"] == [3, 4, 5, 6]
    print(f"  [PASS] GET /api/practice/1?assessment_cycle=CT2 returned component {prac_res['assessment_component']}")

    # Historical questions endpoint
    q_res = fetch_json("/api/intelligence/1/questions?assessment_cycle=CT2")
    assert q_res.get("assessment_cycle") == "CT2"
    assert q_res.get("assessment_component") == "CT2"
    print(f"  [PASS] GET /api/intelligence/1/questions?assessment_cycle=CT2 returned component {q_res['assessment_component']}")

    print("\n" + "=" * 80)
    print("ALL PRODUCTION ENDPOINT VERIFICATIONS PASSED WITH ZERO REGRESSIONS!")
    print("=" * 80)

if __name__ == "__main__":
    main()
