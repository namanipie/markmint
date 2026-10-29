import re
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.core.database import SessionLocal
from backend.models.core import Question, QuestionFamily
from backend.services.extraction.cleaner import strip_question_prefix

db = SessionLocal()
print("=" * 60)
print("  VERIFICATION AUDIT OF NEON POSTGRESQL & TOPICS CATALOG")
print("=" * 60)

# 1. Questions Audit
qs = db.query(Question.id, Question.original_text).filter(Question.original_text.isnot(None)).all()
print(f"Total questions audited: {len(qs)}")

lingering_or_nums = 0
unmatched_lefts = 0
unclosed_dollars = 0
raw_unwrapped_latex = 0

for q in qs:
    txt = q.original_text or ""

    # Check after --- OR ---
    if "--- OR ---" in txt:
        parts = txt.split("--- OR ---")
        for p in parts[1:]:
            c_p = strip_question_prefix(p.strip())
            if c_p != p.strip():
                lingering_or_nums += 1
                break

    # Check left/right balance
    lefts = len(re.findall(r'\\left[\(\[\{\.]', txt))
    rights = len(re.findall(r'\\right[\)\]\}\.]', txt))
    if lefts != rights:
        unmatched_lefts += 1

    # Check dollars
    c = txt.count("$") - txt.count(r"\$")
    if c % 2 != 0:
        unclosed_dollars += 1

print(f"Lingering question numbers after '--- OR ---': {lingering_or_nums}")
print(f"Mismatched \\left / \\right delimiters in DB: {unmatched_lefts}")
print(f"Unclosed dollar signs in DB: {unclosed_dollars}")

# 2. Question Families Audit
fams = db.query(QuestionFamily.id, QuestionFamily.canonical_name).all()
print(f"\nTotal question families audited: {len(fams)}")

fam_leading_nums = 0
for fid, c_name in fams:
    s = c_name or ""
    # Check if starts with Q1, 11., (a), etc.
    if re.match(r'^\s*(?:Q\b|Q\.?\s*\d|\d+[\.\)\:\-]|[a-zA-Z]\))', s, re.I):
        fam_leading_nums += 1

print(f"Question families with lingering numbers: {fam_leading_nums}")

# 3. Topics Catalog Audit
catalog_path = "src/lib/topics-catalog.json"
catalog_prefixes = 0
if os.path.exists(catalog_path):
    with open(catalog_path, "r", encoding="utf-8") as f:
        topics = json.load(f)
    for t in topics:
        for sq in t.get("sampleQuestions", []):
            txt = sq.get("text", "")
            if re.match(r'^\s*(?:Q\b|Q\.?\s*\d|\d+[\.\)\:\-]|[a-zA-Z]\))', txt, re.I):
                catalog_prefixes += 1

print(f"\nSample questions with lingering prefixes in topics-catalog.json: {catalog_prefixes}")

print("=" * 60)
db.close()
