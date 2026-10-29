import json, re

def is_true_mcq(q):
    txt = q.get('question_text', '') or ''
    marks = q.get('marks')
    
    if marks is not None and marks >= 5:
        return False
        
    has_options_caps = bool(re.search(r'(\([A-D]\)|\[[A-D]\]|\\\\\s*\([A-D]\)).+?(\([B-D]\)|\[[B-D]\]|\\\\\s*\([B-D]\))', txt))
    has_options_lower = bool(re.search(r'(\([a-d]\)|\[[a-d]\])\s+[^\n]+?(\([b-d]\)|\[[b-d]\])', txt))
    has_options_colon = bool(re.search(r'(?i)\boptions:\s*(\n|.)+?[a-d]\)', txt))
    which_of_following = bool(re.search(r'(?i)which of the following.+?(\n|\s)([a-d]\)|[A-D]\.)', txt))
    lettered_lines = bool(re.search(r'(?:^|\n)\s*[A-D]\.\s+[^\n]+\n\s*[B-D]\.\s+', txt))
    
    if has_options_caps or has_options_colon or which_of_following or lettered_lines:
        return True
        
    if has_options_lower and marks is not None and marks <= 2:
        if not re.search(r'(?i)(answer all|part\s*-\s*[bc]|or\s*\n\s*\d+\s*\(a\))', txt):
            return True
            
    return False

with open('data/extracted_cycle_test_questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

mcq_count = 0
desc_count = 0

for q in questions:
    marks = q.get('marks') or 2
    mcq = is_true_mcq(q)
    q['is_mcq'] = mcq
    
    if mcq:
        mcq_count += 1
        q['q_type'] = 'MCQ'
        q['section'] = 'Part A (Multiple Choice Questions)'
    else:
        desc_count += 1
        if marks <= 2:
            q['q_type'] = 'Part A (Short Answer)'
            q['section'] = 'Part A (Short Answer Questions)'
        elif marks <= 8:
            q['q_type'] = 'Part B (Medium Answer)'
            q['section'] = 'Part B (Medium Answer Questions)'
        else:
            q['q_type'] = 'Part C (Comprehensive)'
            q['section'] = 'Part C (Comprehensive Questions)'

with open('data/extracted_cycle_test_questions.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, indent=2, ensure_ascii=False)

print(f"Updated data/extracted_cycle_test_questions.json:")
print(f"  Total questions: {len(questions)}")
print(f"  MCQs categorized: {mcq_count}")
print(f"  Descriptive questions categorized: {desc_count}")
