import sqlite3
import re
from collections import defaultdict, Counter

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

# Query all questions with exam, section, and document details
cur.execute('''
    SELECT 
        q.id, q.section_id, q.question_number, q.original_text, q.marks, 
        q.is_alternative, q.family_id, q.question_type, q.extraction_method,
        s.id as s_id, s.name as s_name, s.exam_id,
        e.id as e_id, e.course_id, e.year, e.assessment_type, e.document_id,
        d.title as doc_title, d.source
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    JOIN documents d ON e.document_id = d.id
''')
questions = cur.fetchall()
print(f"Total questions loaded: {len(questions)}")

# Categorize issues
empty_truncated = []
impossible_marks = []
missing_numbering = []
header_instruction_leak = []
broken_math = []
duplicate_within_exam = defaultdict(list)
exam_q_map = defaultdict(list)

instruction_patterns = [
    r'^(answer all questions|choose either|all questions carry equal marks|time:\s*\d|max\.?\s*marks:\s*\d|roll no|reg no|instructions?:)',
    r'^(part\s*-[a-z]\s*carry|maximum\s*marks|duration\s*:)'
]

for q in questions:
    qid, sid, qnum, qtext, marks, is_alt, fam_id, qtype, ext_method, _, sname, eid, _, cid, year, atype, doc_id, doc_title, doc_source = q
    
    # 1. Check empty or truncated text
    if not qtext or len(qtext.strip()) < 3:
        empty_truncated.append((qid, eid, ext_method, qtext))
        
    # 2. Check impossible marks
    if marks is not None and (marks < 0 or marks > 100):
        impossible_marks.append((qid, eid, ext_method, marks))
        
    # 3. Missing question numbers
    if not qnum or qnum.strip() == "":
        missing_numbering.append((qid, eid, ext_method, (qtext or '')[:40]))
        
    # 4. Header / Instruction leak
    if qtext:
        text_lower = qtext.strip().lower()
        for pat in instruction_patterns:
            if re.search(pat, text_lower):
                header_instruction_leak.append((qid, eid, ext_method, qtext[:60]))
                break
                
    # 5. Broken math notation (e.g. unclosed $ or \frac{ without closing brace)
    if qtext:
        dollar_count = qtext.count('$')
        open_b = qtext.count('{')
        close_b = qtext.count('}')
        if (dollar_count % 2 != 0 and dollar_count > 0) or abs(open_b - close_b) > 2:
            broken_math.append((qid, eid, ext_method, dollar_count, open_b, close_b, qtext[:60]))

    # 6. Duplicated questions within one exam
    norm_text = re.sub(r'\s+', ' ', (qtext or '').lower().strip())
    exam_q_map[eid].append((qid, qnum, norm_text, ext_method))

for eid, q_list in exam_q_map.items():
    seen = {}
    for qid, qnum, ntext, ext_method in q_list:
        if len(ntext) > 15: # only check substantial questions
            if ntext in seen:
                duplicate_within_exam[eid].append((seen[ntext], (qid, qnum, ntext[:50])))
            else:
                seen[ntext] = (qid, qnum, ntext[:50])

print("\n--- ISSUE SUMMARY ---")
print(f"Empty or truncated questions:          {len(empty_truncated)}")
print(f"Impossible mark values (<0 or >100):    {len(impossible_marks)}")
print(f"Missing question numbers:              {len(missing_numbering)}")
print(f"Headers/instructions leaked as Q:     {len(header_instruction_leak)}")
print(f"Broken math notation:                  {len(broken_math)}")
dup_exam_count = len(duplicate_within_exam)
total_dup_pairs = sum(len(v) for v in duplicate_within_exam.values())
print(f"Exams with duplicate questions:        {dup_exam_count} ({total_dup_pairs} duplicate pairs)")

if empty_truncated:
    print("\nSample empty/truncated:", empty_truncated[:3])
if impossible_marks:
    print("\nSample impossible marks:", impossible_marks[:3])
if missing_numbering:
    print("\nSample missing numbers:", missing_numbering[:3])
if header_instruction_leak:
    print("\nSample header/instructions leaked:", header_instruction_leak[:3])
if broken_math:
    print("\nSample broken math:", broken_math[:3])
if duplicate_within_exam:
    sample_eid = list(duplicate_within_exam.keys())[0]
    print(f"\nSample duplicate within exam {sample_eid}:", duplicate_within_exam[sample_eid][:2])

# Check marks distribution
marks_dist = Counter([q[4] for q in questions])
print("\nTop 10 question mark values:")
for m, cnt in marks_dist.most_common(10):
    print(f"  {m} marks: {cnt} questions")

# Check questions per exam stats
q_per_exam = [len(ql) for ql in exam_q_map.values()]
print(f"\nQuestions per Exam stats (Total {len(q_per_exam)} exams):")
print(f"  Min: {min(q_per_exam)}, Max: {max(q_per_exam)}, Avg: {sum(q_per_exam)/len(q_per_exam):.1f}")

# Check questions by section name
sname_counter = Counter([q[10] for q in questions])
print("\nTop Section Names:")
for sn, cnt in sname_counter.most_common(8):
    print(f"  {sn}: {cnt}")

con.close()
