import os, re, json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from collections import defaultdict

load_dotenv()
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
conn.autocommit = False
cur = conn.cursor(cursor_factory=RealDictCursor)

def extract_mcq_data(text):
    if not text:
        return False, text, [], None
        
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
            opts.append({'key': k, 'text': opt_text})
        return True, stem, opts, keys_seen
        
    return False, text, [], []

print("Auditing DB questions...")
cur.execute("""
    SELECT q.id, q.section_id, s.exam_id, s.name as section_name, q.question_type, q.original_text, q.marks,
           q.question_number, e.course_id
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
""")
all_questions = cur.fetchall()
print(f"Total questions in DB: {len(all_questions)}")

leaked_mcqs = []
for q in all_questions:
    if q["question_type"] != "MCQ":
        is_m, stem, opts, _ = extract_mcq_data(q["original_text"])
        if is_m and (q["marks"] is None or q["marks"] <= 4):
            leaked_mcqs.append(q)

print(f"Found {len(leaked_mcqs)} leaked MCQs currently marked as non-MCQ.")

if leaked_mcqs:
    # Get all existing MCQ sections per exam
    cur.execute("""
        SELECT id, exam_id, name FROM sections WHERE name ILIKE '%multiple choice%' OR name ILIKE '%mcq%'
    """)
    mcq_sections_by_exam = {row["exam_id"]: row["id"] for row in cur.fetchall()}
    
    # Sync sections sequence
    cur.execute("SELECT setval('sections_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sections));")
    
    # For each exam with leaked MCQs, ensure an MCQ section exists
    exams_needing_mcq_section = set(q["exam_id"] for q in leaked_mcqs if q["exam_id"] not in mcq_sections_by_exam)
    print(f"Exams needing a new MCQ section: {len(exams_needing_mcq_section)}")
    
    for e_id in exams_needing_mcq_section:
        cur.execute("""
            INSERT INTO sections (exam_id, name)
            VALUES (%s, 'PART - A (Multiple Choice Questions)')
            RETURNING id
        """, (e_id,))
        new_sec_id = cur.fetchone()["id"]
        mcq_sections_by_exam[e_id] = new_sec_id
        
    print(f"Batch updating {len(leaked_mcqs)} leaked MCQs to dedicated MCQ sections...")
    update_tuples = [(mcq_sections_by_exam[q["exam_id"]], q["id"]) for q in leaked_mcqs]
    
    # Execute batch update using temporary table or UPDATE FROM
    execute_values(cur, """
        UPDATE questions AS q
        SET question_type = 'MCQ',
            section_id = v.target_sec
        FROM (VALUES %s) AS v(target_sec, q_id)
        WHERE q.id = v.q_id
    """, update_tuples)
    
    conn.commit()
    print("Batch update committed successfully.")

# Check topic mapping coverage for all MCQs
print("Verifying topic mappings for all MCQs in DB...")
cur.execute("""
    SELECT q.id, q.original_text, e.course_id
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    LEFT JOIN question_topic qt ON q.id = qt.question_id
    WHERE q.question_type = 'MCQ' AND qt.topic_id IS NULL
""")
unmapped_mcqs = cur.fetchall()
print(f"Unmapped MCQs in DB: {len(unmapped_mcqs)}")

if unmapped_mcqs:
    # Fetch syllabus topics for all courses
    cur.execute("""
        SELECT t.id, s.course_id, t.name 
        FROM topics t 
        JOIN units u ON t.unit_id = u.id 
        JOIN syllabuses s ON u.syllabus_id = s.id
        ORDER BY s.course_id, t.id
    """)
    topics_by_course = defaultdict(list)
    for t in cur.fetchall():
        topics_by_course[t["course_id"]].append(t)
        
    mappings_to_insert = []
    for q in unmapped_mcqs:
        c_id = q["course_id"]
        c_topics = topics_by_course.get(c_id, [])
        if not c_topics:
            continue
        q_text = (q["original_text"] or "").lower()
        best_t = None
        best_score = -1
        for t in c_topics:
            t_words = [w for w in re.findall(r'\b[a-z]{4,}\b', t["name"].lower())]
            score = sum(1 for w in t_words if w in q_text)
            if score > best_score:
                best_score = score
                best_t = t
        if not best_t or best_score == 0:
            best_t = c_topics[0]
            
        mappings_to_insert.append((q["id"], best_t["id"]))
        
    if mappings_to_insert:
        execute_values(cur, """
            INSERT INTO question_topic (question_id, topic_id)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, mappings_to_insert)
        conn.commit()
        print(f"Inserted {len(mappings_to_insert)} topic mappings for unmapped MCQs.")

# Final DB audit
cur.execute("""
    SELECT s.id, s.exam_id, s.name, 
           COUNT(CASE WHEN q.question_type = 'MCQ' THEN 1 END) as mcq_count,
           COUNT(CASE WHEN q.question_type != 'MCQ' THEN 1 END) as non_mcq_count
    FROM sections s
    JOIN questions q ON q.section_id = s.id
    GROUP BY s.id, s.exam_id, s.name
    HAVING COUNT(CASE WHEN q.question_type = 'MCQ' THEN 1 END) > 0 
       AND COUNT(CASE WHEN q.question_type != 'MCQ' THEN 1 END) > 0
""")
mixed = cur.fetchall()
print(f"Final mixed sections in DB: {len(mixed)}")

cur.execute("""
    SELECT COUNT(*) as total_mcqs,
           COUNT(qt.topic_id) as mapped_mcqs
    FROM questions q
    LEFT JOIN question_topic qt ON q.id = qt.question_id
    WHERE q.question_type = 'MCQ'
""")
cov = cur.fetchone()
print(f"Final MCQ count in DB: {cov['total_mcqs']}, Mapped to topics: {cov['mapped_mcqs']} ({cov['mapped_mcqs']/cov['total_mcqs']*100:.1f}%)")

conn.close()
print("DB MCQ purification complete.")
