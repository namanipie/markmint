"""
Audit script for SPCM (Course 13) question_topic mappings.
Analyzes coverage, confidence tiers, per-unit and per-topic distribution,
finds zero-mapping or overloaded topics, and samples questions for quality review.
"""
import sqlite3
import os
import sys
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

def run_audit():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Total SPCM questions
    total_q = cur.execute("""
        SELECT count(q.id)
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 13
    """).fetchone()[0]

    # 2. Accepted mappings in DB
    accepted_rows = cur.execute("""
        SELECT 
            qt.question_id,
            qt.topic_id,
            t.name as topic_name,
            u.id as unit_id,
            u.number as unit_number,
            u.name as unit_name,
            COALESCE(q.normalized_text, q.original_text) as text,
            q.marks
        FROM question_topic qt
        JOIN questions q ON qt.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN topics t ON qt.topic_id = t.id
        JOIN units u ON t.unit_id = u.id
        WHERE e.course_id = 13
        ORDER BY u.number, t.id, q.id
    """).fetchall()

    accepted_count = len(accepted_rows)

    # 3. All topics in SPCM
    topics = cur.execute("""
        SELECT t.id, t.name, u.number as unit_number, u.name as unit_name
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        JOIN syllabuses syl ON u.syllabus_id = syl.id
        WHERE syl.course_id = 13
        ORDER BY u.number, t.id
    """).fetchall()

    topic_counts = defaultdict(int)
    topic_questions = defaultdict(list)
    unit_counts = defaultdict(int)

    for r in accepted_rows:
        topic_counts[r["topic_name"]] += 1
        unit_counts[f"Unit {r['unit_number']}: {r['unit_name']}"] += 1
        topic_questions[r["topic_name"]].append(r)

    print("=" * 80)
    print("SPCM MAPPING AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total SPCM Questions : {total_q}")
    print(f"Accepted Mappings    : {accepted_count}")
    print(f"Coverage Percentage  : {accepted_count / total_q * 100:.2f}%\n")

    print("--- UNIT DISTRIBUTION ---")
    for u_name in sorted(unit_counts.keys()):
        cnt = unit_counts[u_name]
        pct = cnt / accepted_count * 100
        print(f"  {u_name}: {cnt} questions ({pct:.1f}%)")

    print("\n--- TOPIC DISTRIBUTION & OUTLIERS ---")
    zero_topics = []
    overloaded_topics = []
    
    for t in topics:
        tname = t["name"]
        cnt = topic_counts[tname]
        if cnt == 0:
            zero_topics.append((t["unit_number"], tname))
        elif cnt > 40:
            overloaded_topics.append((t["unit_number"], tname, cnt))
        print(f"  [Unit {t['unit_number']}] {tname}: {cnt}")

    print("\n--- ZERO-MAPPING TOPICS ---")
    if zero_topics:
        for u_num, zt in zero_topics:
            print(f"  Unit {u_num}: {zt}")
    else:
        print("  None (all topics have at least 1 mapped question)")

    print("\n--- SUSPICIOUSLY OVERLOADED TOPICS (>40 questions) ---")
    if overloaded_topics:
        for u_num, ot, cnt in overloaded_topics:
            print(f"  Unit {u_num}: {ot} -> {cnt} questions ({cnt/accepted_count*100:.1f}%)")
    else:
        print("  None")

    # Sample check for overloaded topics
    print("\n" + "=" * 80)
    print("OVERLOADED TOPIC SAMPLING INSPECTION")
    print("=" * 80)
    for u_num, ot, cnt in overloaded_topics:
        print(f"\nTOPIC: {ot} (Total: {cnt})")
        samples = topic_questions[ot][:8]
        for s in samples:
            qtext = s["text"].strip().replace("\n", " ")
            if len(qtext) > 120:
                qtext = qtext[:117] + "..."
            print(f"  [Q {s['question_id']} | {s['marks']} marks]: {qtext}")

    # Representative sample from each unit
    print("\n" + "=" * 80)
    print("REPRESENTATIVE MAPPINGS FROM EVERY UNIT")
    print("=" * 80)
    for u in sorted(list({t['unit_number'] for t in topics})):
        u_topics = [t for t in topics if t["unit_number"] == u]
        print(f"\n--- UNIT {u} SAMPLES ---")
        sampled = 0
        for ut in u_topics:
            qs = topic_questions[ut["name"]]
            if qs:
                s = qs[0]
                qtext = s["text"].strip().replace("\n", " ")
                if len(qtext) > 100:
                    qtext = qtext[:97] + "..."
                print(f"  Topic: {ut['name']}")
                print(f"    Q {s['question_id']} ({s['marks']} marks): {qtext}")
                sampled += 1
                if sampled >= 3:
                    break

    conn.close()

if __name__ == "__main__":
    run_audit()
