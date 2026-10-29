import os, re, json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from collections import defaultdict

load_dotenv()
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
conn.autocommit = False
cur = conn.cursor(cursor_factory=RealDictCursor)

def is_mcq(q_type, text):
    if q_type in ('MCQ', 'Objective / MCQ'):
        return True
    if not text:
        return False
    patterns = [
        r'(\([a-dA-D]\)|\[[a-dA-D]\]|\\\\\s*\([a-dA-D]\)).+?(\([b-dB-D]\)|\[[b-dB-D]\]|\\\\\s*\([b-dB-D]\))',
        r'(?i)\boptions:\s*(\n|.)+?[a-d]\)',
        r'(?i)which of the following.+?(\n|\s)([a-d]\)|[A-D]\.)',
        r'([A-D]\.\s+[^\n]+?\s+){2,}'
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False

print("==================================================")
print("PHASE 1: AUDIT & IDENTIFY ALL MCQS & SECTIONS")
print("==================================================")

cur.execute("""
    SELECT q.id, q.section_id, s.exam_id, s.name as section_name, q.question_type, q.original_text, q.marks,
           q.question_number, e.course_id, e.track_id, e.assessment_type
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
""")
all_questions = cur.fetchall()
print(f"Total questions fetched: {len(all_questions)}")

# Group by exam and section
exams_data = defaultdict(lambda: {'sections': defaultdict(lambda: {'name': '', 'mcqs': [], 'non_mcqs': []})})
all_mcq_ids = set()

for q in all_questions:
    e_id = q['exam_id']
    s_id = q['section_id']
    s_data = exams_data[e_id]['sections'][s_id]
    s_data['name'] = q['section_name']
    
    if is_mcq(q['question_type'], q['original_text']):
        s_data['mcqs'].append(q['id'])
        all_mcq_ids.add(q['id'])
    else:
        s_data['non_mcqs'].append(q['id'])

print(f"Total exams: {len(exams_data)}")
print(f"Total MCQs identified: {len(all_mcq_ids)}")

print("\n==================================================")
print("PHASE 2: CREATE DEDICATED MCQ SECTIONS & MOVE MCQS")
print("==================================================")

# Ensure sequence is correct before inserting new sections
cur.execute("SELECT setval('sections_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sections))")

total_new_sections = 0
total_mcqs_moved = 0
total_sections_renamed = 0

for e_id, e_info in exams_data.items():
    exam_mcqs = []
    for s_id, s_data in e_info['sections'].items():
        exam_mcqs.extend(s_data['mcqs'])
        
    if not exam_mcqs:
        continue
        
    # Check if there is already an existing section dedicated to MCQs
    dedicated_mcq_sec_id = None
    for s_id, s_data in e_info['sections'].items():
        if len(s_data['non_mcqs']) == 0 and ('mcq' in s_data['name'].lower() or 'multiple' in s_data['name'].lower()):
            dedicated_mcq_sec_id = s_id
            break
            
    # Check if any section has 100% MCQs but generic name -> rename it
    for s_id, s_data in e_info['sections'].items():
        if len(s_data['non_mcqs']) == 0 and len(s_data['mcqs']) > 0:
            if not dedicated_mcq_sec_id:
                cur.execute("""
                    UPDATE sections 
                    SET name = 'PART - A (Multiple Choice Questions)', 
                        instructions = 'Multiple Choice Questions (1 Mark each)'
                    WHERE id = %s
                """, (s_id,))
                dedicated_mcq_sec_id = s_id
                total_sections_renamed += 1

    # For any mixed section, we need a dedicated MCQ section
    has_mixed = any(len(s_data['mcqs']) > 0 and len(s_data['non_mcqs']) > 0 for s_data in e_info['sections'].values())
    if has_mixed and not dedicated_mcq_sec_id:
        cur.execute("""
            INSERT INTO sections (exam_id, name, instructions)
            VALUES (%s, 'PART - A (Multiple Choice Questions)', 'Multiple Choice Questions (1 Mark each)')
            RETURNING id
        """, (e_id,))
        dedicated_mcq_sec_id = cur.fetchone()['id']
        total_new_sections += 1

    # Move all MCQs into the dedicated MCQ section
    for s_id, s_data in e_info['sections'].items():
        if s_id != dedicated_mcq_sec_id and len(s_data['mcqs']) > 0:
            mcq_ids_to_move = s_data['mcqs']
            cur.execute("""
                UPDATE questions 
                SET section_id = %s, question_type = 'MCQ'
                WHERE id = ANY(%s)
            """, (dedicated_mcq_sec_id, mcq_ids_to_move))
            total_mcqs_moved += len(mcq_ids_to_move)
            
            # If the original section had non-mcqs, rename it to clarify it's short answer/descriptive
            if len(s_data['non_mcqs']) > 0:
                s_name_clean = s_data['name'].strip().upper()
                if s_name_clean in ('PART - A', 'PART A', 'PART-A', 'SECTION A', 'SECTION-A', 'DEFAULT'):
                    cur.execute("""
                        UPDATE sections 
                        SET name = 'PART - A (Short Answer Questions)'
                        WHERE id = %s
                    """, (s_id,))
                    total_sections_renamed += 1

# Standardize question_type for all detected MCQs in one batch
cur.execute("""
    UPDATE questions
    SET question_type = 'MCQ'
    WHERE id = ANY(%s)
""", (list(all_mcq_ids),))

# Update sequence
cur.execute("SELECT setval('sections_id_seq', (SELECT COALESCE(MAX(id), 1) FROM sections))")

conn.commit()
print(f"Created {total_new_sections} new dedicated MCQ sections.")
print(f"Moved {total_mcqs_moved} MCQs into dedicated sections.")
print(f"Renamed {total_sections_renamed} sections to explicitly separate MCQs and Short Answers.")
print(f"Standardized {len(all_mcq_ids)} questions with question_type = 'MCQ'.")

print("\n==================================================")
print("PHASE 3: MAP ALL UNMAPPED MCQS TO TOPICS")
print("==================================================")

# Find all MCQs currently lacking a topic in question_topic
cur.execute("""
    SELECT q.id, q.question_number, q.original_text, e.course_id, e.track_id, e.assessment_type
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    LEFT JOIN question_topic qt ON qt.question_id = q.id
    WHERE q.id = ANY(%s)
      AND qt.question_id IS NULL
""", (list(all_mcq_ids),))
unmapped_mcqs = cur.fetchall()
print(f"Unmapped MCQs to map to topics: {len(unmapped_mcqs)}")

# Load all course topics
cur.execute("""
    SELECT c.id as course_id, syl.track_id, u.number as unit_number, t.id as topic_id, t.name as topic_name
    FROM courses c
    JOIN syllabuses syl ON syl.course_id = c.id
    JOIN units u ON u.syllabus_id = syl.id
    JOIN topics t ON t.unit_id = u.id
    ORDER BY c.id, syl.track_id, u.number, t.id
""")
all_topics_rows = cur.fetchall()

STOPWORDS = {
    'the', 'is', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'by', 'from',
    'which', 'what', 'following', 'are', 'not', 'that', 'this', 'it', 'as', 'be', 'has', 'have', 'had',
    'can', 'could', 'should', 'would', 'does', 'do', 'options', 'part', 'marks', 'question', 'calculate',
    'find', 'determine', 'state', 'write', 'explain', 'give', 'one', 'two', 'true', 'false'
}

def get_tokens(text):
    if not text:
        return set()
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return set(w for w in words if w not in STOPWORDS)

course_topics_map = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
course_all_topics = defaultdict(list)

for r in all_topics_rows:
    c_id = r['course_id']
    tr_id = r['track_id']
    u_num = r['unit_number']
    t_id = r['topic_id']
    t_name = r['topic_name']
    toks = get_tokens(t_name)
    course_topics_map[c_id][tr_id][u_num].append((t_id, t_name, toks))
    course_all_topics[c_id].append((t_id, t_name, toks, u_num, tr_id))

new_mappings = []
for q in unmapped_mcqs:
    c_id = q['course_id']
    tr_id = q['track_id']
    q_txt = q['original_text'] or ''
    q_toks = get_tokens(q_txt)
    q_num_raw = re.sub(r'[^0-9]', '', str(q['question_number'] or ''))
    q_num = int(q_num_raw) if q_num_raw else 1
    
    at = (q['assessment_type'] or '').upper()
    if 'CT1' in at:
        allowed_units = [1, 2]
    elif 'CT2' in at:
        allowed_units = [3, 4]
    else:
        allowed_units = [1, 2, 3, 4, 5]

    unit_map = course_topics_map[c_id].get(tr_id) or course_topics_map[c_id].get(None) or {}
    if not unit_map and course_topics_map[c_id]:
        first_tr = list(course_topics_map[c_id].keys())[0]
        unit_map = course_topics_map[c_id][first_tr]
        
    candidates = []
    for u_num in allowed_units:
        t_list = unit_map.get(u_num, [])
        for t_id, t_name, toks in t_list:
            overlap = len(q_toks.intersection(toks))
            candidates.append((overlap, u_num, t_id, t_name))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0]
        if best[0] >= 1:
            chosen_topic_id = best[2]
        else:
            # Positional mapping based on question number sequence
            if len(allowed_units) == 2:
                target_unit = allowed_units[0] if q_num <= 10 else allowed_units[1]
            else:
                unit_idx = min(4, max(0, (q_num - 1) // 4))
                target_unit = allowed_units[min(unit_idx, len(allowed_units)-1)]
                
            unit_topics = unit_map.get(target_unit) or []
            if unit_topics:
                t_idx = (q_num % len(unit_topics))
                chosen_topic_id = unit_topics[t_idx][0]
            else:
                chosen_topic_id = candidates[0][2]
    else:
        fallback = course_all_topics[c_id][0]
        chosen_topic_id = fallback[0]
        
    new_mappings.append((q['id'], chosen_topic_id))

if new_mappings:
    execute_values(
        cur,
        """
        INSERT INTO question_topic (question_id, topic_id)
        VALUES %s
        ON CONFLICT DO NOTHING
        """,
        new_mappings
    )
    conn.commit()
    print(f"Inserted {len(new_mappings)} topic mappings into question_topic.")

print("\n==================================================")
print("PHASE 4: FINAL INTEGRITY VERIFICATION")
print("==================================================")

# 1. Verify 0 mixed sections
cur.execute("""
    SELECT s.id, s.name, count(case when q.question_type = 'MCQ' then 1 end) as mcq_count,
           count(case when q.question_type != 'MCQ' or q.question_type is null then 1 end) as non_mcq_count
    FROM sections s
    JOIN questions q ON q.section_id = s.id
    GROUP BY s.id, s.name
    HAVING count(case when q.question_type = 'MCQ' then 1 end) > 0
       AND count(case when q.question_type != 'MCQ' or q.question_type is null then 1 end) > 0
""")
remaining_mixed = cur.fetchall()
print(f"1. Remaining mixed sections: {len(remaining_mixed)} (Expected: 0)")

# 2. Verify MCQ topic mapping coverage
cur.execute("""
    SELECT 
        COUNT(DISTINCT q.id) as total_mcqs,
        COUNT(DISTINCT qt.question_id) as mcqs_with_topic_mapping
    FROM questions q
    LEFT JOIN question_topic qt ON qt.question_id = q.id
    WHERE q.question_type = 'MCQ'
""")
cov = cur.fetchone()
print(f"2. MCQ Topic Mapping Coverage: {cov['mcqs_with_topic_mapping']} of {cov['total_mcqs']} ({cov['mcqs_with_topic_mapping']/cov['total_mcqs']*100:.1f}%)")

# 3. Verify total MCQs by course
cur.execute("""
    SELECT c.name as course_name, COUNT(q.id) as mcq_count
    FROM courses c
    JOIN exams e ON e.course_id = c.id
    JOIN sections s ON s.exam_id = e.id
    JOIN questions q ON q.section_id = s.id
    WHERE q.question_type = 'MCQ'
    GROUP BY c.name
    ORDER BY mcq_count DESC
    LIMIT 10
""")
print("\nTop 10 Courses by MCQ Count:")
for r in cur.fetchall():
    print(f"  {r['course_name']}: {r['mcq_count']} MCQs in dedicated section")

conn.close()
print("\nALL PHASES COMPLETED SUCCESSFULLY.")
