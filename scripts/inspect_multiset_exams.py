import sqlite3
import re
from collections import defaultdict

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

cur.execute('''
    SELECT q.id, s.exam_id, s.name as section_name, q.question_number, q.original_text, d.title
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    JOIN documents d ON e.document_id = d.id
    ORDER BY s.exam_id, q.id
''')
all_q = cur.fetchall()

exam_qs = defaultdict(list)
for qid, eid, sname, qnum, qtext, dtitle in all_q:
    norm = re.sub(r'\s+', ' ', (qtext or '').strip().lower())
    if len(norm) > 15:
        exam_qs[eid].append((qid, sname, qnum, norm, qtext, dtitle))

multi_set_exams = {}
for eid, qlist in exam_qs.items():
    seen = {}
    dups = []
    for qid, sname, qnum, norm, qtext, dtitle in qlist:
        if norm in seen:
            dups.append((seen[norm], (qid, sname, qnum, qtext, dtitle)))
        else:
            seen[norm] = (qid, sname, qnum, qtext, dtitle)
    if dups:
        multi_set_exams[eid] = dups

print(f"Total exams with duplicate normalized text questions: {len(multi_set_exams)}")

for eid, dup_list in multi_set_exams.items():
    print(f"\n==================== EXAM {eid} ({dup_list[0][0][4]}) ====================")
    print(f"Total duplicate pairs: {len(dup_list)}")
    for first_q, second_q in dup_list[:3]:
        print(f"  First:  QID {first_q[0]} | Section: {first_q[1]} | QNum: {first_q[2]}")
        print(f"          {first_q[3][:80]}")
        print(f"  Second: QID {second_q[0]} | Section: {second_q[1]} | QNum: {second_q[2]}")
        print(f"          {second_q[3][:80]}")

con.close()
