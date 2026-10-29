"""
Deep Fix for Questions, Question Families, and Math Formatting

1. Removes all lingering question numbers:
   - Leading prefixes (e.g., '1.', 'Q1.', '21(a)', '(a)', 'a.')
   - Subquestions after '--- OR ---' (e.g., '--- OR ---\n    21. Find...')
   - Strips OCR echo placeholders (e.g., '36. 36.')
2. Cleans all question families in `question_families` table (canonical_name).
3. Fixes math symbols:
   - Balances unclosed \\left and \\right delimiters
   - Fixes unclosed dollar signs
   - Wraps raw LaTeX expressions in $...$
4. Cleans sample questions in src/lib/topics-catalog.json.

Usage:
    python scripts/db/deep_fix_questions_and_math.py --dry-run
    python scripts/db/deep_fix_questions_and_math.py --apply
"""

import sys
import os
import re
import json
import time
import argparse
from typing import Optional, List, Tuple
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv("backend/.env")

from backend.core.database import SessionLocal
from backend.models.core import Question, QuestionFamily
from backend.services.extraction.cleaner import strip_question_prefix


# Keywords for LaTeX math detection
LATEX_OPS = (
    r'int|iint|iiint|oint|sum|prod|lim|infty|partial|nabla|frac|sqrt|'
    r'sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|ln|log|exp|det|vec|'
    r'alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|'
    r'Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|'
    r'times|cdot|pm|mp|approx|neq|le|ge|leq|geq|equiv|sim|propto|'
    r'in|notin|subset|supset|subseteq|supseteq|cap|cup|oplus|otimes|'
    r'angle|perp|circ|deg|hat|bar|dot|ddot|tilde|mathbf|mathbb|mathcal|mathrm'
)

# Single line math chunk containing LaTeX command
RAW_MATH_SEGMENT = re.compile(
    r'(?:[+\-]?[ \t]*)?'
    r'\\(?:' + LATEX_OPS + r')'
    r'(?:'
    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    r'|\[[^\[\]\n]*\]'
    r'|\^[a-zA-Z0-9+\-_]|\^\{[^{}]*\}'
    r'|_[a-zA-Z0-9+\-_]|_\{[^{}]*\}'
    r'|\\left[\(\[\{\.]|\\right[\)\]\}\.]'
    r'|[ \t]*[\+\-\*\/\=\<\>][ \t]*'
    r'|[ \t]*\\(?:' + LATEX_OPS + r')'
    r'|[ \t]+[a-zA-Z](?![a-zA-Z])'
    r'|[ \t]+[0-9]+[a-zA-Z]?(?![a-zA-Z])'
    r'|[a-zA-Z0-9\(\)\,\^]+'
    r')*',
    re.IGNORECASE
)


def balance_left_right(text: str) -> str:
    """Balances any unmatched \\left and \\right in math expressions."""
    if not text:
        return text

    lefts = len(re.findall(r'\\left[\(\[\{\.]', text))
    rights = len(re.findall(r'\\right[\)\]\}\.]', text))
    if lefts > rights:
        text = re.sub(r'\\left\(', '(', text)
        text = re.sub(r'\\left\[', '[', text)
        text = re.sub(r'\\left\\\{', '{', text)
    elif rights > lefts:
        text = re.sub(r'\\right\)', ')', text)
        text = re.sub(r'\\right\]', ']', text)
        text = re.sub(r'\\right\\\}', '}', text)
        text = re.sub(r'\\right\.', '', text)
        text = re.sub(r'\\right', '', text)
    return text


def fix_unclosed_dollars(text: str) -> str:
    """Fixes dangling unclosed $ delimiters."""
    if not text or "$" not in text:
        return text

    # Trailing dangling $\ or $
    text = re.sub(r'\s*\$\\?\s*$', '', text)

    # Count unescaped dollars
    c = text.count("$") - text.count(r"\$")
    if c % 2 != 0:
        # If single dangling dollar at end of an option like "(D) p$"
        text = re.sub(r'(\([A-D]\)\s*[^$]+)\$$', r'\1', text)
        if (text.count("$") - text.count(r"\$")) % 2 != 0:
            text = text + "$"
    return text


def wrap_raw_latex(text: str) -> str:
    """Wraps standalone raw LaTeX commands (e.g. \\sin(2x+5), \\beta(m,n)) in $...$."""
    if not text or "\\" not in text:
        return text

    # First balance left/right throughout text
    text = balance_left_right(text)

    # Protect existing math blocks
    placeholders = []
    def save_math(m):
        placeholders.append(m.group(0))
        return f"__MM_PH_{len(placeholders)-1}__"

    protected = re.sub(
        r'\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|(?<!\\)\$((?:\\\\|\\\$|[^\$])+?)(?<!\\)\$|\\begin\{[a-zA-Z*]+\}[\s\S]*?\\end\{[a-zA-Z*]+\}',
        save_math,
        text
    )

    def repl(m):
        full = m.group(0)
        leading_space = full[:len(full) - len(full.lstrip())]
        raw = full.strip()

        # Trailing punctuation cleanup
        punct = ""
        while raw and raw[-1] in ('.', ',', '?', ';', ':', ')'):
            if raw[-1] == ')' and raw.count('(') >= raw.count(')'):
                break
            punct = raw[-1] + punct
            raw = raw[:-1].strip()

        if not raw:
            return leading_space + punct

        raw = balance_left_right(raw)
        return f"{leading_space}${raw}${punct}"

    wrapped = RAW_MATH_SEGMENT.sub(repl, protected)

    # Restore placeholders
    for idx, ph in enumerate(placeholders):
        wrapped = wrapped.replace(f"__MM_PH_{idx}__", ph)

    return wrapped


def deep_clean_question_text(text: str, q_num: str = "") -> str:
    """Comprehensive cleaning of question text stem and math formatting."""
    if not text:
        return ""

    # 1. Strip leading question numbers from outer text in a loop
    cleaned = text.strip()
    while True:
        new_s = strip_question_prefix(cleaned, q_num)
        if new_s == cleaned:
            break
        cleaned = new_s

    # 2. Clean after '--- OR ---'
    lines = cleaned.split("\n")
    new_lines = []
    after_or = False
    for line in lines:
        if "--- OR ---" in line:
            after_or = True
            new_lines.append(line)
        elif after_or:
            s_line = line.strip()
            # If line is empty or just redundant header like '21. (OR)' or 'b.'
            if not s_line:
                continue
            if re.match(r'^(?:\d+[\.\:\)]\s*)?(?:\([oO][rR]\)|\([oO][uU]\)|[a-zA-Z][\.\:\)\-]|\d+[\.\:\)])$', s_line):
                # Pure placeholder/header line after OR, omit and keep looking for question text
                continue

            indent = len(line) - len(line.lstrip())
            c_line = s_line
            while True:
                new_cl = strip_question_prefix(c_line)
                if new_cl == c_line:
                    break
                c_line = new_cl
            new_lines.append(" " * indent + c_line)
            after_or = False
        else:
            new_lines.append(line)

    cleaned = "\n".join(new_lines).strip()

    # 3. Clean leading numeric prefix if text is short e.g. "24. (ou)"
    cleaned = re.sub(r'^\s*\d{1,3}[\.\:\)]\s*(?=\([a-zA-Z0-9]+\)|$)', '', cleaned).strip()

    # 4. OCR placeholder cleanup (e.g. "36. 36.")
    if re.match(r'^\d+[\.\:\)]\s*\d+[\.\:\)]?$', cleaned):
        return ""

    # 4. Fix math: balance \left / \right, fix unclosed $, wrap raw LaTeX
    cleaned = balance_left_right(cleaned)
    cleaned = fix_unclosed_dollars(cleaned)
    cleaned = wrap_raw_latex(cleaned)

    # 5. Clean trailing unescaped backslashes e.g. "show that x\"
    cleaned = re.sub(r'\\+$', '', cleaned)

    return cleaned.strip()


def run_deep_fix(apply_changes: bool = False, batch_size: int = 1000):
    db = SessionLocal()
    print("=" * 70, flush=True)
    print("  DEEP FIX: QUESTIONS, QUESTION FAMILIES, AND MATH FORMATTING", flush=True)
    print(f"  Mode: {'APPLY (COMMITTING TO NEON POSTGRES)' if apply_changes else 'DRY RUN (NO DB WRITES)'}", flush=True)
    print("=" * 70, flush=True)

    try:
        t0 = time.time()
        conn = db.connection().connection
        cur = conn.cursor()

        # ==========================================
        # STEP 1: CLEAN ALL QUESTIONS IN DATABASE
        # ==========================================
        print("\n--- STEP 1: Processing Questions Table ---", flush=True)
        q_rows = (
            db.query(Question.id, Question.question_number, Question.original_text)
            .filter(Question.original_text.isnot(None))
            .order_by(Question.id)
            .all()
        )
        print(f"Loaded {len(q_rows)} questions in {time.time() - t0:.2f}s.", flush=True)

        q_updates = []
        q_samples = []

        for q_id, q_num, orig in q_rows:
            orig_str = orig or ""
            cleaned = deep_clean_question_text(orig_str, str(q_num or ""))

            if cleaned != orig_str:
                q_updates.append((q_id, cleaned))
                if len(q_samples) < 12:
                    q_samples.append({
                        "id": q_id,
                        "q_num": q_num,
                        "before": orig_str[:80].replace("\n", " "),
                        "after": cleaned[:80].replace("\n", " ")
                    })

        print(f"Questions needing update: {len(q_updates)} / {len(q_rows)} ({len(q_updates)/len(q_rows)*100:.1f}%)", flush=True)
        print("Sample Question Transformations:")
        for s in q_samples:
            print(f"  [Q ID {s['id']} | Q#{s['q_num']}]")
            print(f"    BEFORE: {repr(s['before'])}")
            print(f"    AFTER:  {repr(s['after'])}")

        if apply_changes and q_updates:
            print(f"\nExecuting question updates in batches of {batch_size}...", flush=True)
            sql_q = """
            UPDATE questions AS q
            SET original_text = v.orig
            FROM (VALUES %s) AS v(id, orig)
            WHERE q.id = v.id;
            """
            for i in range(0, len(q_updates), batch_size):
                batch = q_updates[i : i + batch_size]
                execute_values(cur, sql_q, batch, template="(%s, %s)")
                conn.commit()
                print(f"  Processed {min(i + batch_size, len(q_updates))} / {len(q_updates)} questions...", flush=True)
            print(f"Committed {len(q_updates)} question updates to Neon!", flush=True)

        # ==========================================
        # STEP 2: CLEAN ALL QUESTION FAMILIES
        # ==========================================
        print("\n--- STEP 2: Processing Question Families Table ---", flush=True)
        f_rows = db.query(QuestionFamily.id, QuestionFamily.canonical_name).all()
        print(f"Loaded {len(f_rows)} question families.", flush=True)

        f_updates = []
        f_samples = []

        for f_id, c_name in f_rows:
            orig_c = c_name or ""
            new_c = deep_clean_question_text(orig_c)

            if new_c != orig_c:
                f_updates.append((f_id, new_c))
                if len(f_samples) < 12:
                    f_samples.append({
                        "id": f_id,
                        "before": orig_c[:70].replace("\n", " "),
                        "after": new_c[:70].replace("\n", " ")
                    })

        print(f"Question Families needing update: {len(f_updates)} / {len(f_rows)} ({len(f_updates)/len(f_rows)*100:.1f}%)", flush=True)
        print("Sample Family Transformations:")
        for s in f_samples:
            print(f"  [Family ID {s['id']}]")
            print(f"    BEFORE: {repr(s['before'])}")
            print(f"    AFTER:  {repr(s['after'])}")

        if apply_changes and f_updates:
            print(f"\nExecuting question family updates in batches of {batch_size}...", flush=True)
            sql_f = """
            UPDATE question_families AS f
            SET canonical_name = v.c_name
            FROM (VALUES %s) AS v(id, c_name)
            WHERE f.id = v.id;
            """
            for i in range(0, len(f_updates), batch_size):
                batch = f_updates[i : i + batch_size]
                execute_values(cur, sql_f, batch, template="(%s, %s)")
                conn.commit()
                print(f"  Processed {min(i + batch_size, len(f_updates))} / {len(f_updates)} families...", flush=True)
            print(f"Committed {len(f_updates)} question family updates to Neon!", flush=True)

        cur.close()

        # ==========================================
        # STEP 3: CLEAN src/lib/topics-catalog.json
        # ==========================================
        print("\n--- STEP 3: Processing topics-catalog.json ---", flush=True)
        catalog_path = "src/lib/topics-catalog.json"
        if os.path.exists(catalog_path):
            with open(catalog_path, "r", encoding="utf-8") as f:
                topics = json.load(f)

            catalog_modified = 0
            for t in topics:
                for sq in t.get("sampleQuestions", []):
                    txt = sq.get("text", "")
                    cleaned_sq = deep_clean_question_text(txt)
                    if cleaned_sq != txt:
                        sq["text"] = cleaned_sq
                        catalog_modified += 1

            print(f"Sample questions cleaned in topics-catalog.json: {catalog_modified}")
            if apply_changes and catalog_modified > 0:
                with open(catalog_path, "w", encoding="utf-8") as f:
                    json.dump(topics, f, indent=2)
                print("Successfully saved updated topics-catalog.json!")

        print("\n" + "=" * 70, flush=True)
        print(f"DEEP FIX COMPLETED in {time.time() - t0:.2f}s", flush=True)
        if not apply_changes:
            print("DRY RUN FINISHED. Zero writes made to Neon.", flush=True)
            print("To execute live migration, run with: python scripts/db/deep_fix_questions_and_math.py --apply", flush=True)
        print("=" * 70, flush=True)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Deep fix failed: {e}", flush=True)
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep fix questions, families, and math formatting")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying anything")
    parser.add_argument("--apply", action="store_true", help="Apply updates to database and json")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size")
    args = parser.parse_args()

    run_deep_fix(apply_changes=args.apply, batch_size=args.batch_size)
