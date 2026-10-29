import re

with open('backend/api/endpoints/practice.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add json and re imports if needed
if 'import json' not in code:
    code = 'import json\nimport re\nfrom pathlib import Path\n' + code

ct_endpoint_code = '''

CT_QUESTIONS_PATH = Path("data/extracted_cycle_test_questions.json")
_ct_questions_cache = None

def _load_ct_questions():
    global _ct_questions_cache
    if _ct_questions_cache is None and CT_QUESTIONS_PATH.exists():
        try:
            with open(CT_QUESTIONS_PATH, "r", encoding="utf-8") as f:
                _ct_questions_cache = json.load(f)
        except Exception:
            _ct_questions_cache = []
    return _ct_questions_cache or []


@router.get("/practice/cycle-tests/{subject}")
def get_cycle_test_questions(
    subject: str,
    cycle: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Retrieve authentic past Cycle Test questions extracted directly from SRMIST CT papers.
    Supports filtering by subject name/slug and assessment cycle (CT1, CT2, CT3, ALL).
    """
    all_qs = _load_ct_questions()
    s_clean = re.sub(r"[^a-z0-9]+", " ", subject.lower()).strip()

    matched = []
    for q in all_qs:
        q_subj = re.sub(r"[^a-z0-9]+", " ", q.get("subject", "").lower()).strip()
        if s_clean in q_subj or q_subj in s_clean:
            if cycle and cycle.upper() != "ALL":
                c_up = cycle.upper()
                q_cyc = q.get("cycle", "CT").upper()
                if c_up not in q_cyc and q_cyc != "CT":
                    continue
            matched.append(q)

    # Sort so questions with verified answer keys come first
    matched.sort(key=lambda x: (x.get("answer_key") is None, x.get("q_num", 999)))

    return {
        "subject": subject,
        "cycle": cycle or "ALL",
        "total_available": len(matched),
        "questions": matched[:limit]
    }
'''

code += ct_endpoint_code

with open('backend/api/endpoints/practice.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("backend/api/endpoints/practice.py successfully updated with CT endpoint!")
