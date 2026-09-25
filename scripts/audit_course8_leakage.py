import sqlite3
from collections import defaultdict

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

print("=== PRE-REMEDIATION AUDIT ===")

# Exam 62 details
cur.execute("SELECT id, course_id, track_id, year, term, document_id FROM exams WHERE id = 62")
e62 = cur.fetchone()
print(f"Exam 62: id={e62[0]}, course_id={e62[1]}, track_id={e62[2]}, year={e62[3]}, term={e62[4]}, document_id={e62[5]}")

cur.execute("SELECT title, source, original_url FROM documents WHERE id = ?", (e62[5],))
d244 = cur.fetchone()
print(f"Doc 244: title={d244[0]}, source={d244[1]}, url={d244[2]}")

cur.execute("SELECT COUNT(*) FROM questions q JOIN sections s ON q.section_id = s.id WHERE s.exam_id = 62")
q62_cnt = cur.fetchone()[0]
print(f"Exam 62 question count: {q62_cnt}")

# Exam 49 details
cur.execute("SELECT id, course_id, track_id, year, term, document_id FROM exams WHERE id = 49")
e49 = cur.fetchone()
print(f"Exam 49: id={e49[0]}, course_id={e49[1]}, track_id={e49[2]}, year={e49[3]}, term={e49[4]}, document_id={e49[5]}")

cur.execute("SELECT title, source, original_url FROM documents WHERE id = ?", (e49[5],))
d226 = cur.fetchone()
print(f"Doc 226: title={d226[0]}, source={d226[1]}, url={d226[2]}")

cur.execute("SELECT COUNT(*) FROM questions q JOIN sections s ON q.section_id = s.id WHERE s.exam_id = 49")
q49_cnt = cur.fetchone()[0]
print(f"Exam 49 question count: {q49_cnt}")

# Compare questions between 49 and 62
cur.execute("""
    SELECT q49.question_number, q49.id, q49.original_text, q62.id, q62.original_text
    FROM questions q49
    JOIN sections s49 ON q49.section_id = s49.id AND s49.exam_id = 49
    LEFT JOIN questions q62 ON q62.section_id IN (SELECT id FROM sections WHERE exam_id = 62)
         AND q49.question_number = q62.question_number
    ORDER BY CAST(q49.question_number AS INTEGER)
""")
paired = cur.fetchall()
print(f"Total paired question numbers between 49 and 62: {len(paired)}")

# The 20 cross-track families
cur.execute("""
    SELECT m.family_id, COUNT(DISTINCT e.track_id) as t_cnt, GROUP_CONCAT(DISTINCT e.track_id) as tracks
    FROM question_family_memberships m
    JOIN questions q ON m.question_id = q.id
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    WHERE e.course_id = 8
    GROUP BY m.family_id
    HAVING t_cnt > 1
    ORDER BY m.family_id
""")
cross_track_fams = [r[0] for r in cur.fetchall()]
print(f"Total cross-track families: {len(cross_track_fams)}")
print("Cross-track family IDs:", cross_track_fams)

print("\n--- Details of the 20 Cross-Track Families ---")
for fid in cross_track_fams:
    cur.execute("""
        SELECT q.id, s.exam_id, e.track_id, m.match_type, m.similarity_score, m.decision_method, q.original_text
        FROM question_family_memberships m
        JOIN questions q ON m.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE m.family_id = ?
        ORDER BY s.exam_id
    """, (fid,))
    members = cur.fetchall()
    q_49 = [m for m in members if m[1] == 49]
    q_62 = [m for m in members if m[1] == 62]
    q49_id = q_49[0][0] if q_49 else None
    q62_id = q_62[0][0] if q_62 else None
    score = q_62[0][4] if q_62 else None
    method = q_62[0][5] if q_62 else None
    print(f"Family #{fid}: Q#49={q49_id} (German track 1), Q#62={q62_id} (Korean track 5), score={score}, method={method}")

# The 16 singleton families spawned from remaining Exam 62 questions
cur.execute("""
    SELECT q.id, q.question_number, q.family_id, qf.canonical_name
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN question_families qf ON q.family_id = qf.id
    WHERE s.exam_id = 62 AND q.family_id NOT IN ({})
    ORDER BY q.id
""".format(','.join(map(str, cross_track_fams))))
singleton_fams = cur.fetchall()
print(f"\nTotal singleton families from Exam 62: {len(singleton_fams)}")
for qid, qnum, fid, text in singleton_fams:
    clean_text = text[:50].encode('ascii', 'backslashreplace').decode('ascii')
    print(f"Singleton Family #{fid}: Q#{qid} (qnum={qnum}) -> \"{clean_text}...\"")

con.close()
