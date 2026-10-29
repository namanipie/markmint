import sqlite3

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

cur.execute('''
    SELECT q.id, e.course_id, c.name, e.year, q.question_number, q.marks, q.original_text
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    JOIN courses c ON e.course_id = c.id
    WHERE q.extraction_method = 'vision_gemini' 
      AND (q.original_text LIKE '%$%' OR q.original_text LIKE '%\\%' OR q.original_text LIKE '%^%')
      AND c.id IN (1, 13, 16, 19)
    ORDER BY q.id DESC
    LIMIT 12
''')
math_qs = cur.fetchall()

print(f"Sample Gemini Math/LaTeX Questions ({len(math_qs)} sampled):")
for q in math_qs:
    qid, cid, cname, year, qnum, marks, qtext = q
    print(f"\n[QID: {qid} | Course {cid}: {cname} | Year: {year} | QNum: {qnum} | Marks: {marks}]")
    print(qtext[:250])

con.close()
