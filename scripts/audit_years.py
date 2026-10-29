import sqlite3
from collections import Counter

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

cur.execute('''
    SELECT e.id, e.year, e.assessment_type, e.course_id, c.name, d.title, d.original_url
    FROM exams e
    JOIN courses c ON e.course_id = c.id
    JOIN documents d ON e.document_id = d.id
''')
exams = cur.fetchall()

print(f"Total exams in DB: {len(exams)}")

year_counts = Counter(e[1] for e in exams)
print("\nExam Year Distribution:")
for yr, cnt in sorted(year_counts.items(), key=lambda x: (x[0] is not None, x[0])):
    print(f"  Year {str(yr):<6}: {cnt} exams")

known_year_exams = [e for e in exams if e[1] is not None]
unknown_year_exams = [e for e in exams if e[1] is None]

print(f"\nKnown-year exams:   {len(known_year_exams)}")
print(f"Unknown-year exams: {len(unknown_year_exams)}")

# Check for suspicious years (e.g. < 2010 or > 2026)
suspicious_years = [e for e in known_year_exams if e[1] < 2010 or e[1] > 2026]
print(f"Suspicious years (<2010 or >2026): {len(suspicious_years)}")
for s in suspicious_years:
    print("  Suspicious:", s)

# Verify evidence backing for sample known-year exams
print("\nSample Known-Year Evidence (matching title vs extracted year):")
matches = 0
for e in known_year_exams[:20]:
    eid, yr, atype, cid, cname, title, url = e
    has_yr_in_title = str(yr) in title
    if has_yr_in_title:
        matches += 1
    print(f"  Exam {eid:3d} | Year: {yr} | Title: {title[:60]:60s} | In Title: {has_yr_in_title}")

# Check question count by exam year
cur.execute('''
    SELECT e.year, COUNT(q.id)
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    GROUP BY e.year
''')
q_by_year = cur.fetchall()
print("\nQuestions by Exam Year:")
for yr, qcnt in sorted(q_by_year, key=lambda x: (x[0] is not None, x[0])):
    print(f"  Year {str(yr):<6}: {qcnt} questions")

con.close()
