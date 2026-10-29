import sqlite3
from collections import Counter, defaultdict

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

# 1. Total questions
cur.execute("SELECT COUNT(*) FROM questions")
total_questions = cur.fetchone()[0]

# 2. Questions with membership
cur.execute("SELECT COUNT(DISTINCT question_id) FROM question_family_memberships")
q_with_membership = cur.fetchone()[0]

# 3. Questions with zero membership
q_without_membership = total_questions - q_with_membership

# 4. Total families
cur.execute("SELECT COUNT(*) FROM question_families")
total_families = cur.fetchone()[0]

# 5. Total family membership rows
cur.execute("SELECT COUNT(*) FROM question_family_memberships")
total_membership_rows = cur.fetchone()[0]

# 6. Families containing >1 question
cur.execute('''
    SELECT family_id, COUNT(question_id) as q_cnt 
    FROM question_family_memberships 
    GROUP BY family_id 
    HAVING q_cnt > 1
''')
multi_q_families = cur.fetchall()

# 7. Exact duplicate families
cur.execute('''
    SELECT family_id, COUNT(question_id) as q_cnt
    FROM question_family_memberships
    WHERE match_type = 'exact'
    GROUP BY family_id
    HAVING q_cnt > 1
''')
exact_dup_families = cur.fetchall()

# 8. Family size distribution
cur.execute('''
    SELECT q_cnt, COUNT(*) FROM (
        SELECT family_id, COUNT(question_id) as q_cnt 
        FROM question_family_memberships 
        GROUP BY family_id
    ) GROUP BY q_cnt ORDER BY q_cnt
''')
family_size_dist = cur.fetchall()

# 9. Questions grouped into families by course
cur.execute('''
    SELECT c.id, c.code, c.name, 
           COUNT(q.id) as total_course_q,
           COUNT(DISTINCT m.question_id) as q_with_fam
    FROM courses c
    LEFT JOIN exams e ON e.course_id = c.id
    LEFT JOIN sections s ON s.exam_id = e.id
    LEFT JOIN questions q ON q.section_id = s.id
    LEFT JOIN question_family_memberships m ON m.question_id = q.id
    GROUP BY c.id
    ORDER BY c.id
''')
by_course = cur.fetchall()

# 10. Questions from newly ingested exams (id > 13) that have no family membership
cur.execute('''
    SELECT COUNT(q.id)
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    LEFT JOIN question_family_memberships m ON m.question_id = q.id
    WHERE e.id > 13 AND m.id IS NULL
''')
new_q_without_fam = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(q.id)
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    WHERE e.id > 13
''')
total_new_q = cur.fetchone()[0]

print("=== QUESTION FAMILY COVERAGE AUDIT ===")
print(f"Total Questions:                     {total_questions}")
print(f"Questions WITH Family Membership:    {q_with_membership} ({q_with_membership*100/total_questions:.1f}%)")
print(f"Questions WITHOUT Family Membership: {q_without_membership} ({q_without_membership*100/total_questions:.1f}%)")
print(f"Total Families:                      {total_families}")
print(f"Total Membership Rows:               {total_membership_rows}")
print(f"Families with >1 Question:           {len(multi_q_families)}")
print(f"Exact Duplicate Families (>1 Q):     {len(exact_dup_families)}")
print("\nFamily Size Distribution (members -> count of families):")
for sz, cnt in family_size_dist:
    print(f"  {sz} questions: {cnt} families")

print("\nBy Course Breakdown:")
for cid, ccode, cname, tot_q, q_fam in by_course:
    print(f"  Course {cid:2d} | {ccode:12s} | {cname[:30]:30s} | Total Q: {tot_q:4d} | With Fam: {q_fam:4d} ({q_fam*100/tot_q if tot_q else 0:.1f}%)")

print(f"\nNewly Ingested Questions (Exam ID > 13): {total_new_q}")
print(f"New Questions Without Family Membership:  {new_q_without_fam} ({new_q_without_fam*100/total_new_q if total_new_q else 0:.1f}%)")

con.close()
