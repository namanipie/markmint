import os
import re
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')

def clean_text(text: str) -> str:
    t = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    t = re.sub(r'[ \t]+', ' ', t)
    return t.strip()

def tokenize(text: str) -> set:
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    # remove short stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'for', 'with', 'on', 'at', 'by', 'from', 'is', 'are', 'was', 'were', 'what', 'which', 'how', 'explain', 'describe', 'define', 'write'}
    return {w for w in words if w not in stopwords and len(w) > 2}

def jaccard_similarity(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def sync_sequences(cur):
    tables = ['documents', 'exams', 'sections', 'questions', 'question_families', 'question_family_memberships']
    for t in tables:
        cur.execute(f"SELECT pg_get_serial_sequence('{t}', 'id');")
        seq = cur.fetchone()[0]
        if seq:
            cur.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {t};")
            next_val = cur.fetchone()[0]
            cur.execute(f"SELECT setval('{seq}', {next_val}, false);")
            print(f"  Synced sequence {seq} to {next_val}", flush=True)

def main():
    print("==================================================")
    print("MarkMint: CT Question Ingestion & Family Clustering")
    print("==================================================")
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # 1. Sync sequences before starting
    print("\n1. Synchronizing PostgreSQL sequences...")
    sync_sequences(cur)

    # 2. Fetch courses from DB
    cur.execute("SELECT id, name, code FROM courses;")
    db_courses = {}
    for cid, name, code in cur.fetchall():
        db_courses[name.lower()] = {
            'id': cid,
            'name': name,
            'code': code,
            'semester': "1"
        }

    COURSE_ALIAS = {
        'advanced programming practice': None,
        'calculus and linear algebra': 'calculus and linear algebra',
        'chemistry': 'chemistry',
        'communicative english': 'communicative english',
        'computer organization and architecture': 'computer organization and architecture',
        'data structures and algorithms': 'data structures and algorithms',
        'database management systems': 'database management systems',
        'design and analysis of algorithms': 'design and analysis of algorithms',
        'electrical and electronics engineering': 'electrical and electronics engineering',
        'electronic system and pcb design': 'electronic system and pcb design',
        'foreign languages': 'foreign languages',
        'introduction to computational biology': 'introduction to computational biology',
        'machine learning': None,
        'numerical methods & analysis': None,
        'operating systems': 'operating systems',
        'programming for problem solving': 'programming for problem solving',
        'semiconductor physics and computational methods': 'semiconductor physics and computational methods',
        'transforms and boundary value problems': 'transforms and boundary value problems',
        'compiler design': 'compiler design',
        'discrete mathematics': 'discrete mathematics',
        'electromagnetic theory, quantum mechanics, waves and optics': 'electromagnetic theory, quantum mechanics, waves and optics',
        'fundamental of economics (foe)': 'fundamental of economics (foe)',
        'object oriented design and programming': 'object oriented design and programming',
        'philosophy of engineering': 'philosophy of engineering'
    }

    # 3. Load syllabus topics per course
    print("\n2. Loading syllabus topics and existing question families...")
    cur.execute("""
        SELECT c.id, u.number, t.id, t.name
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses s ON u.syllabus_id = s.id
        JOIN courses c ON s.course_id = c.id
        ORDER BY c.id, u.number, t.id;
    """)
    course_topics = {}
    for cid, unum, tid, tname in cur.fetchall():
        course_topics.setdefault(cid, []).append({
            'unit': unum,
            'topic_id': tid,
            'topic_name': tname,
            'tokens': tokenize(tname)
        })

    # 4. Load existing question families per course
    cur.execute("SELECT id, subject, canonical_name, repetition_type, first_seen_year, latest_seen_year FROM question_families;")
    existing_families = {}
    for fid, subj, cname, rep, f_yr, l_yr in cur.fetchall():
        s_low = (subj or "").strip().lower()
        existing_families.setdefault(s_low, []).append({
            'id': fid,
            'canonical_name': cname,
            'repetition_type': rep,
            'tokens': tokenize(cname),
            'first_seen_year': f_yr,
            'latest_seen_year': l_yr
        })

    # 5. Load questions JSON
    with open("data/extracted_cycle_test_questions.json", "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    # 6. Check existing questions in DB to ensure idempotency
    cur.execute("SELECT e.course_id, e.assessment_type, q.original_text FROM questions q JOIN sections s ON q.section_id = s.id JOIN exams e ON s.exam_id = e.id;")
    existing_q_sigs = set()
    for cid, a_type, q_txt in cur.fetchall():
        sig = f"{cid}::{a_type}::" + re.sub(r'[^a-zA-Z0-9]', '', (q_txt or '')[:60].lower())
        existing_q_sigs.add(sig)

    print(f"Existing questions in DB signature index: {len(existing_q_sigs)}", flush=True)

    # 7. Ingestion loop
    print("\n3. Processing CT questions for ingestion & clustering...", flush=True)
    exam_cache = {} # (course_id, cycle) -> exam_id
    section_cache = {} # (exam_id, sec_name) -> section_id

    stats = {
        'new_documents': 0,
        'new_exams': 0,
        'new_questions': 0,
        'skipped_existing': 0,
        'mapped_topics': 0,
        'linked_families': 0,
        'new_families': 0
    }

    for item in questions_data:
        raw_sub = (item.get("subject") or "").strip().lower()
        alias = COURSE_ALIAS.get(raw_sub, raw_sub)
        if not alias or alias not in db_courses:
            continue

        c_info = db_courses[alias]
        cid = c_info['id']
        cname = c_info['name']
        cycle = (item.get("cycle") or "CT1").upper()
        if cycle not in ["CT1", "CT2"]:
            cycle = "CT1"

        q_text = clean_text(item.get("question_text", ""))
        if len(q_text) < 15:
            continue

        # Check idempotency
        q_sig = f"{cid}::{cycle}::" + re.sub(r'[^a-zA-Z0-9]', '', q_text[:60].lower())
        if q_sig in existing_q_sigs:
            stats['skipped_existing'] += 1
            continue
        existing_q_sigs.add(q_sig)

        # Ensure Document & Exam
        exam_key = (cid, cycle)
        if exam_key not in exam_cache:
            # Check if exam already exists in DB
            cur.execute("""
                SELECT e.id FROM exams e 
                WHERE e.course_id = %s AND e.assessment_type = %s AND e.year = 2024;
            """, (cid, cycle))
            row = cur.fetchone()
            if row:
                exam_id = row[0]
            else:
                # Create Document
                doc_title = f"{cname} - Authentic {cycle} Papers Archive (2024)"
                doc_hash = f"ct_{cid}_{cycle.lower()}_2024_auth"
                cur.execute("""
                    INSERT INTO documents (source, original_url, title, semester, subject, year, exam_type, resource_type, processing_status, extraction_status, extraction_confidence, document_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, ("markmint_ct_pipeline", "https://markmint.vercel.app", doc_title, str(c_info['semester']), cname, 2024, cycle, "exam_paper", "completed", "completed", 1.0, doc_hash))
                doc_id = cur.fetchone()[0]
                stats['new_documents'] += 1

                # Create Exam
                term = "ODD" if cycle == "CT1" else "EVEN"
                cur.execute("""
                    INSERT INTO exams (course_id, document_id, year, term, assessment_type)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (cid, doc_id, 2024, term, cycle))
                exam_id = cur.fetchone()[0]
                stats['new_exams'] += 1

            exam_cache[exam_key] = exam_id

        exam_id = exam_cache[exam_key]

        # Determine Section
        marks = float(item.get("marks") or 2.0)
        q_type = item.get("q_type") or ("MCQ" if marks <= 1 else "SHORT_ANSWER" if marks <= 2 else "DESCRIPTIVE")
        sec_name = "PART - A" if (marks <= 2 or q_type in ["MCQ", "SHORT_ANSWER"]) else "PART - B"
        
        sec_key = (exam_id, sec_name)
        if sec_key not in section_cache:
            cur.execute("SELECT id FROM sections WHERE exam_id = %s AND name = %s;", (exam_id, sec_name))
            srow = cur.fetchone()
            if srow:
                sec_id = srow[0]
            else:
                cur.execute("INSERT INTO sections (exam_id, name) VALUES (%s, %s) RETURNING id;", (exam_id, sec_name))
                sec_id = cur.fetchone()[0]
            section_cache[sec_key] = sec_id

        sec_id = section_cache[sec_key]

        # Cognitive Level & Difficulty
        cog_level = "REMEMBER" if q_type == "MCQ" else "UNDERSTAND" if marks <= 2 else "APPLY" if q_type in ["CODING", "NUMERICAL"] else "ANALYZE"
        difficulty = 0.3 if q_type == "MCQ" else 0.4 if marks <= 2 else 0.6 if q_type == "DESCRIPTIVE" else 0.75

        # -------------------------------------------------------------
        # Question Family Clustering (Option A)
        # -------------------------------------------------------------
        q_tokens = tokenize(q_text)
        course_fams = existing_families.setdefault(cname.lower(), [])
        best_fam = None
        best_sim = 0.0

        for f in course_fams:
            sim = jaccard_similarity(q_tokens, f['tokens'])
            if sim > best_sim:
                best_sim = sim
                best_fam = f

        family_id = None
        if best_fam and best_sim >= 0.55:
            family_id = best_fam['id']
            # Upgrade repetition type
            new_rep = "exact_repeat" if best_sim >= 0.8 else "family_repeat"
            cur.execute("""
                UPDATE question_families 
                SET repetition_type = %s, latest_seen_year = GREATEST(latest_seen_year, 2024)
                WHERE id = %s;
            """, (new_rep, family_id))
            stats['linked_families'] += 1
        else:
            first_words = " ".join(q_text.split()[:7])
            can_name = f"Family: {first_words}..."
            cur.execute("""
                INSERT INTO question_families (subject, canonical_name, first_seen_year, latest_seen_year, repetition_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (cname, can_name, 2024, 2024, "singleton"))
            family_id = cur.fetchone()[0]
            course_fams.append({
                'id': family_id,
                'canonical_name': can_name,
                'repetition_type': 'singleton',
                'tokens': q_tokens,
                'first_seen_year': 2024,
                'latest_seen_year': 2024
            })
            stats['new_families'] += 1

        # Insert Question
        q_num = str(item.get("q_num") or "1")
        cur.execute("""
            INSERT INTO questions (
                section_id, family_id, question_number, original_text, normalized_text,
                marks, is_alternative, needs_review, extraction_method, extraction_confidence,
                question_type, cognitive_level, difficulty, classification_confidence
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            ) RETURNING id;
        """, (
            sec_id, family_id, q_num, q_text, q_text.lower(),
            marks, False, False, "AUTHENTIC_CT_PIPELINE", 1.0,
            q_type, cog_level, difficulty, 0.95
        ))
        question_id = cur.fetchone()[0]
        stats['new_questions'] += 1

        # Insert QuestionFamilyMembership
        match_type = "EXACT" if best_sim >= 0.8 else "CONCEPTUAL" if best_sim >= 0.55 else "CANONICAL"
        dec_method = "rule_heuristic" if best_sim >= 0.55 else "spawn"
        cur.execute("""
            INSERT INTO question_family_memberships (family_id, question_id, similarity_score, match_type, decision_method, algorithm_version)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (family_id, question_id, max(best_sim, 1.0 if match_type == "CANONICAL" else 0.6), match_type, dec_method, "v2.0"))

        # -------------------------------------------------------------
        # Topic Classification (Portion Invariant)
        # -------------------------------------------------------------
        topics = course_topics.get(cid, [])
        in_scope_units = [1, 2] if cycle == "CT1" else [3, 4]
        in_scope_topics = [t for t in topics if t['unit'] in in_scope_units]
        
        # Match by token overlap
        best_topic = None
        best_topic_sim = 0.0
        for t in in_scope_topics:
            sim = jaccard_similarity(q_tokens, t['tokens'])
            if sim > best_topic_sim:
                best_topic_sim = sim
                best_topic = t

        chosen_topic_id = None
        if best_topic and best_topic_sim > 0.05:
            chosen_topic_id = best_topic['topic_id']
        elif in_scope_topics:
            # Fallback to first topic of first in-scope unit
            chosen_topic_id = in_scope_topics[0]['topic_id']

        if chosen_topic_id:
            cur.execute("""
                INSERT INTO question_topic (question_id, topic_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """, (question_id, chosen_topic_id))
            stats['mapped_topics'] += 1

        if stats['new_questions'] % 50 == 0:
            conn.commit()
            print(f"  [Commit Batch] New questions: {stats['new_questions']}, Families linked: {stats['linked_families']}, New families: {stats['new_families']}, Topics mapped: {stats['mapped_topics']}", flush=True)

    # Re-sync sequences after inserting
    print("\n4. Re-synchronizing sequences post-ingestion...", flush=True)
    sync_sequences(cur)

    # Final commit
    conn.commit()
    print("\n==================================================")
    print("INGESTION & QUESTION FAMILY CLUSTERING COMPLETE!")
    print("==================================================")
    for k, v in stats.items():
        print(f"  {k:<20}: {v}")

    # Verify new counts
    cur.execute("""
        SELECT e.assessment_type, count(q.id)
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.assessment_type IN ('CT1', 'CT2')
        GROUP BY e.assessment_type;
    """)
    print("\nVerified Neon CT Question Counts:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} questions")

    conn.close()

if __name__ == '__main__':
    main()
