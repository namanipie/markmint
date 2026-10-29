import fitz
import re
import json
from pathlib import Path

def parse_oodp_bank(fpath):
    doc = fitz.open(fpath)
    full_text = "\n".join(p.get_text() for p in doc)
    blocks = re.split(r'\n(?=\d{1,3}\n)', full_text)
    questions = []
    current_unit = 1
    
    for b in blocks:
        b = b.strip()
        if "UNIT II" in b or "UNIT 2" in b:
            current_unit = 2
        elif "UNIT III" in b or "UNIT 3" in b:
            current_unit = 3
        elif "UNIT IV" in b or "UNIT 4" in b:
            current_unit = 4
        elif "UNIT V" in b or "UNIT 5" in b:
            current_unit = 5

        m = re.match(r'^(\d{1,3})\n(.+)', b, re.DOTALL)
        if not m:
            continue
        q_num = int(m.group(1))
        body = m.group(2).strip()
        body = re.sub(r'\nCO\d.*$', '', body, flags=re.DOTALL).strip()
        
        if len(body) < 15 or "DEPARTMENT OF" in body or "Course Outcomes" in body:
            continue
            
        cycle = "CT1" if current_unit in [1, 2] else "CT2"
        questions.append({
            'q_num': q_num,
            'question_text': body,
            'marks': 1 if re.search(r'\b[A-D]\.', body) else 2,
            'q_type': "MCQ" if re.search(r'\b[A-D]\.', body) else "SHORT_ANSWER",
            'answer_key': None,
            'subject': "Object Oriented Design and Programming",
            'cycle': cycle,
            'unit': current_unit,
            'source_file': "Object_Oriented_Design_and_Programming_CT1_Question_Bank.pdf"
        })
    return questions

def parse_foe_bank(fpath):
    doc = fitz.open(fpath)
    full_text = "\n".join(p.get_text() for p in doc)
    pattern = re.compile(r'((?:(?!Answer:).)+?)(Answer:\s*[^\n]+)', re.DOTALL)
    questions = []
    current_unit = 1
    
    for m in pattern.finditer(full_text):
        q_raw = m.group(1).strip()
        ans = m.group(2).replace('Answer:', '').strip()
        
        if "UNIT II" in q_raw or "UNIT 2" in q_raw:
            current_unit = 2
        elif "UNIT III" in q_raw or "UNIT 3" in q_raw:
            current_unit = 3
        elif "UNIT IV" in q_raw or "UNIT 4" in q_raw:
            current_unit = 4
        elif "UNIT V" in q_raw or "UNIT 5" in q_raw:
            current_unit = 5

        lines = [l.strip() for l in q_raw.split('\n') if l.strip()]
        clean_lines = [l for l in lines if not any(h in l for h in ['SRM INSTITUTE', 'RAMAPURAM', 'B.TECH', '21MGH', 'Fundamentals of Economics', 'Question Bank', 'UNIT I', 'UNIT II', 'UNIT III', 'UNIT IV', 'UNIT V'])]
        body = "\n".join(clean_lines).strip()
        
        if len(body) < 15:
            continue
            
        cycle = "CT1" if current_unit in [1, 2] else "CT2"
        questions.append({
            'q_num': len(questions) + 1,
            'question_text': body,
            'marks': 1,
            'q_type': "MCQ",
            'answer_key': ans,
            'subject': "Fundamental Of Economics (FOE)",
            'cycle': cycle,
            'unit': current_unit,
            'source_file': "Fundamental_Of_Economics__FOE__CT1_Questions_Bank.pdf"
        })
    return questions

def main():
    # 1. Load existing extracted questions
    with open("data/extracted_cycle_test_questions.json", "r", encoding="utf-8") as f:
        existing_qs = json.load(f)

    print(f"1. Existing extracted questions: {len(existing_qs)}")

    # 2. Load more_parsed_ct_questions.json
    with open("data/more_parsed_ct_questions.json", "r", encoding="utf-8") as f:
        more_qs = json.load(f)

    print(f"2. Additional parsed questions: {len(more_qs)}")

    # 3. Parse OODP bank
    oodp_path = "data/downloads/more_cycle_tests/Object_Oriented_Design_and_Programming_CT1_Question_Bank.pdf"
    oodp_qs = parse_oodp_bank(oodp_path) if Path(oodp_path).exists() else []
    print(f"3. OODP questions parsed: {len(oodp_qs)}")

    # 4. Parse FOE bank
    foe_path = "data/downloads/more_cycle_tests/Fundamental_Of_Economics__FOE__CT1_Questions_Bank.pdf"
    foe_qs = parse_foe_bank(foe_path) if Path(foe_path).exists() else []
    print(f"4. FOE questions parsed: {len(foe_qs)}")

    COURSE_NORM = {
        'advanced programming practice': 'Advanced Programming Practice',
        'calculus and linear algebra': 'Calculus And Linear Algebra',
        'chemistry': 'Chemistry',
        'communicative english': 'Communicative English',
        'computer organization and architecture': 'Computer Organization and Architecture',
        'computer organization and architecture ': 'Computer Organization and Architecture',
        'data structures and algorithm': 'Data Structures and Algorithms',
        'data structures and algorithms': 'Data Structures and Algorithms',
        'database management systems': 'Database Management Systems',
        'design and analysis of algorithms': 'Design and Analysis of Algorithms',
        'electrical and electronics engineering': 'Electrical and Electronics Engineering',
        'electronic system and pcb design': 'Electronic System and PCB Design',
        'foreign languages': 'Foreign Languages',
        'introduction to computational biology': 'Introduction To Computational Biology',
        'machine learning': 'Machine Learning',
        'numerical methods & analysis': 'Numerical Methods & Analysis',
        'operating systems': 'Operating Systems',
        'programming for problem solving': 'Programming For Problem Solving',
        'semiconductor physics and computational methods': 'Semiconductor Physics and Computational Methods',
        'transforms and boundary value problems': 'Transforms and Boundary Value Problems',
        'compiler design': 'Compiler Design',
        'discrete mathematics': 'Discrete Mathematics',
        'electromagnetic theory, quantum mechanics, waves and optics': 'Electromagnetic Theory, Quantum Mechanics, Waves and Optics',
        'fundamental of economics (foe)': 'Fundamental Of Economics (FOE)',
        'object oriented design and programming': 'Object Oriented Design and Programming',
        'philosophy of engineering': 'Philosophy Of Engineering'
    }

    all_qs = existing_qs + more_qs + oodp_qs + foe_qs
    print(f"\nRaw total questions before deduplication: {len(all_qs)}")

    deduped = []
    seen_signatures = set()

    for q in all_qs:
        raw_sub = (q.get("subject") or "").strip().lower()
        norm_sub = COURSE_NORM.get(raw_sub, q.get("subject", "").strip())
        q["subject"] = norm_sub
        
        cyc = (q.get("cycle") or "CT").upper()
        if cyc == "CT":
            unit = q.get("unit")
            if unit in [1, 2]:
                cyc = "CT1"
            elif unit in [3, 4, 5]:
                cyc = "CT2"
            else:
                cyc = "CT1"
        elif cyc == "MODEL":
            cyc = "CT2"
        q["cycle"] = cyc

        text = q.get("question_text", "").strip()
        if len(text) < 15:
            continue

        sig_key = f"{norm_sub}::" + re.sub(r'[^a-zA-Z0-9]', '', text[:60].lower())
        if sig_key in seen_signatures:
            continue
        seen_signatures.add(sig_key)
        deduped.append(q)

    print(f"Final deduplicated master CT questions: {len(deduped)}")

    from collections import Counter
    counts_by_sub = Counter(q["subject"] for q in deduped)
    print("\nMaster CT Questions Count by Course:")
    for s, cnt in counts_by_sub.most_common():
        c1 = sum(1 for q in deduped if q["subject"] == s and q["cycle"] == "CT1")
        c2 = sum(1 for q in deduped if q["subject"] == s and q["cycle"] == "CT2")
        print(f"  {s:<55} | Total: {cnt:<4} (CT1: {c1:<3}, CT2: {c2:<3})")

    master_path = Path("data/extracted_cycle_test_questions.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"\nSaved consolidated master dataset ({len(deduped)} questions) to {master_path}")

if __name__ == "__main__":
    main()
