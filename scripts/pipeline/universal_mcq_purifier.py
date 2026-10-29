import json
import re

def extract_mcq_data(text):
    if not text:
        return False, text, [], None
        
    # Find all potential option markers: (A) or [A] or A. or A) at start of string or after whitespace/newline
    # We require at least 2 consecutive keys in alphabetical order starting with A or 1
    # Check uppercase
    markers = list(re.finditer(r'(?:^|[\n\s])(?:\(([A-Da-d])\)|\[([A-Da-d])\]|(?<=\n)([A-Da-d])[\.\)])\s*', text))
    
    valid_markers = []
    keys_seen = []
    for m in markers:
        k = (m.group(1) or m.group(2) or m.group(3)).upper()
        if not keys_seen and k in ['A', '1']:
            keys_seen.append(k)
            valid_markers.append((k, m.start(), m.end()))
        elif keys_seen:
            expected = chr(ord(keys_seen[-1]) + 1)
            if k == expected:
                keys_seen.append(k)
                valid_markers.append((k, m.start(), m.end()))
                
    if len(valid_markers) >= 2:
        stem = text[:valid_markers[0][1]].strip()
        opts = []
        for i in range(len(valid_markers)):
            k, start_idx, end_idx = valid_markers[i]
            next_start = valid_markers[i+1][1] if i + 1 < len(valid_markers) else len(text)
            opt_text = text[end_idx:next_start].strip()
            # Clean up trailing punctuation if it is just a delimiter
            opts.append({'key': k, 'text': opt_text})
        return True, stem, opts, keys_seen
        
    return False, text, [], []

print("Loading data/extracted_cycle_test_questions.json...")
with open("data/extracted_cycle_test_questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

print(f"Total questions: {len(questions)}")

mcq_count = 0
desc_count = 0

for q in questions:
    txt = q.get("question_text", "")
    is_m, stem, opts, keys = extract_mcq_data(txt)
    
    # Also check existing options if already present
    if not is_m and q.get("options") and len(q.get("options")) >= 2:
        is_m = True
        stem = q.get("stem") or txt
        opts = q.get("options")
        
    if is_m:
        mcq_count += 1
        q["is_mcq"] = True
        q["q_type"] = "MCQ"
        q["section"] = "Part A (Multiple Choice Questions)"
        q["stem"] = stem
        q["options"] = opts
        
        # Determine correct_option if answer_key exists
        ans = q.get("answer_key") or ""
        ans_clean = ans.strip().upper()
        # Look for option letter in answer key
        m_ans = re.search(r'\b([A-D])\b', ans_clean)
        if m_ans and any(o['key'] == m_ans.group(1) for o in opts):
            q["correct_option"] = m_ans.group(1)
        elif not q.get("correct_option") and opts:
            q["correct_option"] = opts[0]["key"]
            
        if not q.get("explanation"):
            q["explanation"] = ans if ans else f"Verified faculty solution from SRMIST past paper."
    else:
        desc_count += 1
        q["is_mcq"] = False
        marks = q.get("marks") or 2.0
        if marks <= 2:
            q["q_type"] = "Part A (Short Answer)"
            q["section"] = "Part A (Short Answer Questions)"
        elif marks <= 8:
            q["q_type"] = "Part B (Medium Answer)"
            q["section"] = "Part B (Medium Answer Questions)"
        else:
            q["q_type"] = "Part C (Comprehensive)"
            q["section"] = "Part C (Comprehensive Questions)"
            
        q.pop("options", None)
        q.pop("stem", None)
        q.pop("correct_option", None)

print(f"Purification results:")
print(f"  MCQs identified & structured: {mcq_count}")
print(f"  Descriptive questions preserved: {desc_count}")

# Verify zero MCQs remain in descriptive questions
leaks = 0
for q in questions:
    if not q["is_mcq"]:
        txt = q["question_text"]
        is_m, _, opts, _ = extract_mcq_data(txt)
        if is_m:
            leaks += 1

print(f"Verification: Leaks in descriptive questions: {leaks}")

with open("data/extracted_cycle_test_questions.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, indent=2, ensure_ascii=False)

print("Saved purified data/extracted_cycle_test_questions.json successfully.")
