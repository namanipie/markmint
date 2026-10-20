"""
Question text cleaning and prefix stripping utilities.
Ensures question numbers (e.g. '1.', 'Q.1:', '21(a)', '(a)') are stripped from question stem
without corrupting mathematical notation, LaTeX symbols, programming code (e.g. a[0]),
or numerical quantities in word problems (e.g. '15 samples of...').
"""
import re

PREFIX_REGEX = re.compile(
    r'^\s*(?:'
    r'Q(?:uestion)?\.?\s*\d{1,3}\s*[\.\:\)\-]\s*(?:\([a-zA-Z0-9]+\)|[a-zA-Z][\.\:\)\-])?\s*'
    r'|\d{1,3}\s*[\.\:\)]\s*(?:\([a-zA-Z0-9]+\)|[a-zA-Z][\.\:\)\-])?\s*'
    r'|\d{1,3}\s*\([a-zA-Z0-9]+\)[\.\:\-]?\s*'
    r'|\d{1,3}[a-zA-Z][\.\:\)\-]\s*'
    r'|\([a-zA-Z0-9]{1,3}\)\s*'
    r'|[a-zA-Z][\.\)]\s+'
    r')',
    re.IGNORECASE
)

def strip_question_prefix(text: str, q_num: str = "") -> str:
    """
    Strips leading question numbers/labels (e.g., '1.', 'Q1.', '21(a)', '(a)') from question text.
    Leaves mathematical formulas, code brackets (e.g. a[0]), word problems ('15 samples...'),
    and actual question stem intact.
    """
    if not text:
        return ""
    cleaned = text.strip()
    m = PREFIX_REGEX.match(cleaned)
    if m:
        remainder = cleaned[m.end():].strip()
        # Safety: avoid stripping if remainder is essentially empty or just punctuation
        if len(remainder) >= 2 and not re.match(r'^[\d\s\.\:\)\-]+$', remainder):
            return remainder
    return cleaned
