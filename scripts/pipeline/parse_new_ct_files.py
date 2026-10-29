import fitz
import re
import json
from pathlib import Path

def clean_text(text: str) -> str:
    t = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

def parse_new_pdf(fpath: Path, subject: str, cycle: str):
    doc = fitz.open(fpath)
    full_text = "\n".join(p.get_text() for p in doc if p.get_text().strip())
    
    # Split on question numbers
    q_blocks = re.split(r'\n(?=(?:Q(?:uestion)?\s*\.?\s*\d+|\b\d{1,2}\s*[\.\)\-]))', full_text)
    questions = []
    
    for blk in q_blocks:
        blk = clean_text(blk)
        if len(blk) < 20 or len(blk) > 3000:
            continue

        m = re.match(r'^(?:Q(?:uestion)?\s*\.?\s*)?(\d{1,2})\s*[\.\)\-]\s*(.+)', blk, re.DOTALL)
        if not m:
            continue

        q_num = int(m.group(1))
        body = m.group(2).strip()

        if any(h in body.lower() for h in ['course outcome', 'program specific', 'academic year', 'max. marks', 'duration:', 'college of engineering']):
            continue

        marks = 2
        marks_m = re.search(r'\[?\(?(\d{1,2})\s*(?:Marks?|M)\)?\]?', blk, re.IGNORECASE)
        if marks_m:
            try:
                marks = int(marks_m.group(1))
            except:
                pass
        elif re.search(r'(?i)\b(?:a\)|[A-D]\.|\(a\)|\(A\))\b', body):
            marks = 1

        q_type = "DESCRIPTIVE"
        if re.search(r'(?i)\b(?:a\)|[A-D]\.|\(a\)|\(A\))\b', body):
            q_type = "MCQ"
        elif marks <= 2:
            q_type = "SHORT_ANSWER"
        elif any(k in body.lower() for k in ['algorithm', 'pseudocode', 'code', 'program', 'function', 'class']):
            q_type = "CODING"
        elif any(k in body.lower() for k in ['calculate', 'derive', 'evaluate', 'compute', 'find', 'solve']):
            q_type = "NUMERICAL"

        ans_m = re.search(r'(?i)(?:Ans(?:wer)?|Key|Solution)\s*[:\-]?\s*([^\n]+)', blk)
        answer_key = ans_m.group(1).strip() if ans_m else None

        questions.append({
            'q_num': q_num,
            'question_text': body,
            'marks': marks,
            'q_type': q_type,
            'answer_key': answer_key,
            'subject': subject,
            'cycle': cycle,
            'source_file': fpath.name
        })

    return questions

base_dir = Path("data/downloads/more_cycle_tests")
parsed_more = []

# Mapping from filename keywords to (Subject Name, Cycle)
file_configs = [
    ("Discrete_Mathematics_CT1", "Discrete Mathematics", "CT1"),
    ("Discrete_Mathematics_CT2", "Discrete Mathematics", "CT2"),
    ("Operating_Systems_CT1", "Operating Systems", "CT1"),
    ("Fundamental_Of_Economics", "Fundamental Of Economics (FOE)", "CT1"),
    ("Object_Oriented_Design_and_Programming_CT1", "Object Oriented Design and Programming", "CT1"),
    ("Object_Oriented_Design_and_Programming_CT2", "Object Oriented Design and Programming", "CT2"),
    ("Compiler_Design_CT1", "Compiler Design", "CT1"),
    ("Compiler_Design_CT2", "Compiler Design", "CT2"),
    ("Electromagnetic_Theory__Quantum_Mechanics__Waves_and_Optics_CT2", "Electromagnetic Theory, Quantum Mechanics, Waves and Optics", "CT2"),
    ("Philosophy_Of_Engineering_CT1", "Philosophy Of Engineering", "CT1"),
]

for kw, subj, cyc in file_configs:
    matched = list(base_dir.glob(f"*{kw}*.pdf"))
    if matched:
        f = matched[0]
        qs = parse_new_pdf(f, subj, cyc)
        print(f"[{subj}] {cyc}: Extracted {len(qs)} questions from {f.name}")
        parsed_more.extend(qs)

out_file = Path("data/more_parsed_ct_questions.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(parsed_more, f, indent=2, ensure_ascii=False)

print(f"\nTotal new questions parsed: {len(parsed_more)} saved to {out_file}")
