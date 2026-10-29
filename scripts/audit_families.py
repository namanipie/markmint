import sqlite3

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

# 1. Exact repeat examples
cur.execute('''
    SELECT qf.id, qf.canonical_name, qf.subject, qf.first_seen_year, COUNT(m.id) as mem_count
    FROM question_families qf
    JOIN question_family_memberships m ON m.family_id = qf.id
    WHERE m.match_type = 'exact'
    GROUP BY qf.id
    ORDER BY mem_count DESC
    LIMIT 5
''')
exact_fams = cur.fetchall()
print("=== EXACT REPEAT FAMILY EXAMPLES ===")
for f in exact_fams:
    fid, name, subj, yr, mcnt = f
    print(f"\nFamily {fid} [{subj}] (First seen: {yr}, Members: {mcnt}):")
    print(f"  Canonical: {name[:120]}")
    cur.execute('''
        SELECT q.id, e.year, q.original_text, m.similarity_score
        FROM question_family_memberships m
        JOIN questions q ON m.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE m.family_id = ?
    ''', (fid,))
    for qid, qyr, qtext, score in cur.fetchall():
        print(f"    - QID {qid} (Year: {qyr}, Score: {score}): {qtext[:100]}")

# 2. Conceptual/paraphrase repeat examples
cur.execute('''
    SELECT qf.id, qf.canonical_name, qf.subject, qf.first_seen_year, COUNT(m.id) as mem_count
    FROM question_families qf
    JOIN question_family_memberships m ON m.family_id = qf.id
    WHERE m.match_type = 'conceptual'
    GROUP BY qf.id
    ORDER BY mem_count DESC
    LIMIT 5
''')
concept_fams = cur.fetchall()
print("\n=== CONCEPTUAL/PARAPHRASE REPEAT FAMILY EXAMPLES ===")
for f in concept_fams:
    fid, name, subj, yr, mcnt = f
    print(f"\nFamily {fid} [{subj}] (First seen: {yr}, Members: {mcnt}):")
    print(f"  Canonical: {name[:120]}")
    cur.execute('''
        SELECT q.id, e.year, q.original_text, m.similarity_score
        FROM question_family_memberships m
        JOIN questions q ON m.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE m.family_id = ?
    ''', (fid,))
    for qid, qyr, qtext, score in cur.fetchall():
        print(f"    - QID {qid} (Year: {qyr}, Score: {score}): {qtext[:100]}")

# 3. Subject isolation check (verify that no family has questions from multiple subjects)
cur.execute('''
    SELECT m.family_id, COUNT(DISTINCT c.id) as course_count, GROUP_CONCAT(DISTINCT c.name) as courses
    FROM question_family_memberships m
    JOIN questions q ON m.question_id = q.id
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    JOIN courses c ON e.course_id = c.id
    GROUP BY m.family_id
    HAVING course_count > 1
''')
cross_subj = cur.fetchall()
print(f"\nCross-subject family leaks (must be 0): {len(cross_subj)}")
for cs in cross_subj:
    print("  Leak:", cs)

# 4. Unknown-year questions first_seen_year check
cur.execute('''
    SELECT qf.id, qf.canonical_name, qf.first_seen_year
    FROM question_families qf
    WHERE qf.first_seen_year IS NULL
''')
null_year_fams = cur.fetchall()
print(f"\nFamilies with first_seen_year = None (properly unanchored): {len(null_year_fams)}")

con.close()
