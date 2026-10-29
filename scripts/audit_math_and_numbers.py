"""
Forensic audit of math symbols, LaTeX formatting, question numbering, and OCR corruptions
across all questions and question families.
"""
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv("backend/.env")

from backend.core.database import SessionLocal
from backend.models.core import Question, QuestionFamily

def audit():
    db = SessionLocal()
    questions = db.query(Question.id, Question.question_number, Question.original_text).all()
    print(f"Total questions in database: {len(questions)}")

    # 1. Math audit
    latex_cmd = re.compile(r'\\(int|iint|iiint|sum|prod|lim|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|psi|omega|nabla|partial|infty|times|cdot|approx|le|ge|neq|pm|vec|det|log|ln|sin|cos|tan|cot|sec|csc|cosh|sinh|tanh|frac|sqrt|hat|bar|dot|ddot|mathbf|mathbb|mathcal|text|begin|left|right|to|rightarrow|forall|exists|in|notin|subset|cap|cup|oplus|otimes|circ|deg|angle|perp|sim|cong)(?![a-zA-Z])')
    
    # Check for unclosed $
    unclosed_dollar = []
    # Check for raw LaTeX outside $...$ or \(...\)
    raw_latex = []
    # Check for broken \left( without \right)
    broken_left_right = []
    # Check for double backslash issues like \\\\frac
    excess_slashes = []
    # Check for OCR replacement character 
    ocr_replacement = []
    # Check for still existing question numbering
    has_qnum = []

    prefix_re = re.compile(
        r'^\s*(?:'
        r'Q(?:uestion)?\.?\s*\d+'
        r'|\d{1,3}\s*[\.\:\)]'
        r'|\d{1,3}\s*\([a-zA-Z0-9]+\)'
        r'|\d{1,3}[a-zA-Z][\.\:\)\-]'
        r'|\([a-zA-Z0-9]{1,3}\)'
        r'|[a-zA-Z][\.\)]\s+'
        r')',
        re.IGNORECASE
    )

    # Subquestion prefix inside text: e.g. "--- OR --- \n 21. " or "\n 21. "
    internal_qnum_re = re.compile(
        r'(?:---\s*OR\s*---\s*|\n\s*)(?:Q(?:uestion)?\.?\s*)?(\d{1,3}\s*[\.\:\)]|\d{1,3}[a-zA-Z][\.\:\)\-]|\d{1,3}\s*\([a-zA-Z0-9]+\))\s*',
        re.IGNORECASE
    )

    for q in questions:
        t = q.original_text or ""
        
        # Check dollar balance
        dollar_count = t.count("$") - t.count(r"\$")
        if dollar_count % 2 != 0:
            unclosed_dollar.append((q.id, q.question_number, t))

        # Check raw LaTeX outside math delimiters
        stripped = re.sub(r'\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|(?<!\\)\$((?:\\\\|\\\$|[^\$])+?)(?<!\\)\$', '', t)
        if latex_cmd.search(stripped):
            raw_latex.append((q.id, q.question_number, stripped))

        # Check broken left right
        left_count = len(re.findall(r'\\left[\(\[\{]', t))
        right_count = len(re.findall(r'\\right[\)\]\}]', t))
        if left_count != right_count:
            broken_left_right.append((q.id, q.question_number, left_count, right_count, t))

        # Check excess slashes
        if r"\\\\" in t:
            # Note: \\\\ can be valid in pmatrix row breaks (e.g. \\\\), but in \\\\frac it is broken
            if re.search(r'\\\\\\\\(frac|int|sum|sqrt|alpha|beta|theta|partial|begin)', t):
                excess_slashes.append((q.id, t))

        # Check OCR 
        if "\ufffd" in t or "" in t:
            ocr_replacement.append((q.id, t))

        # Check question numbers at start
        if prefix_re.match(t):
            has_qnum.append((q.id, q.question_number, t[:60]))

        # Check internal question numbers after OR or newline
        if internal_qnum_re.search(t):
            has_qnum.append((q.id, q.question_number, t[:60]))

    print("\n" + "=" * 60)
    print("AUDIT FINDINGS:")
    print("=" * 60)
    print(f"1. Questions with unclosed '$' delimiters: {len(unclosed_dollar)}")
    print(f"2. Questions with raw LaTeX math commands outside delimiters: {len(raw_latex)}")
    print(f"3. Questions with mismatched \\left and \\right: {len(broken_left_right)}")
    print(f"4. Questions with broken quadruple backslashes (\\\\\\\\cmd): {len(excess_slashes)}")
    print(f"5. Questions with OCR replacement characters (): {len(ocr_replacement)}")
    print(f"6. Questions with lingering question numbering (start or internal): {len(has_qnum)}")

    print("\n--- Samples of Raw LaTeX Math outside delimiters ---")
    for qid, qnum, snip in raw_latex[:10]:
        print(f"  ID {qid} | {repr(snip[:70])}")

    print("\n--- Samples of Unclosed '$' ---")
    for qid, qnum, snip in unclosed_dollar[:5]:
        print(f"  ID {qid} | {repr(snip[:80])}")

    print("\n--- Samples of Mismatched \\left and \\right ---")
    for qid, qnum, l, r, snip in broken_left_right[:5]:
        print(f"  ID {qid} (left={l}, right={r}) | {repr(snip[:80])}")

    print("\n--- Samples of OCR characters () ---")
    for qid, snip in ocr_replacement[:5]:
        print(f"  ID {qid} | {repr(snip[:80])}")

    print("\n--- Samples of Lingering Question Numbers ---")
    for qid, qnum, snip in has_qnum[:10]:
        print(f"  ID {qid} | Q#{qnum} | {repr(snip[:70])}")

    db.close()

if __name__ == "__main__":
    audit()
