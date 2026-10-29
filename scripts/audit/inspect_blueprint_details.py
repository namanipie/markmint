import sqlite3
import json

def inspect_details():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    print("=== COURSE ASSESSMENT PLANS TABLE ===")
    c.execute("SELECT COUNT(*) FROM course_assessment_plans")
    print(f"Total rows in course_assessment_plans: {c.fetchone()[0]}")
    c.execute("SELECT * FROM course_assessment_plans LIMIT 5")
    for r in c.fetchall():
        print("  Plan:", r)

    print("\n=== ASSESSMENT COMPONENTS TABLE ===")
    c.execute("SELECT COUNT(*) FROM assessment_components")
    print(f"Total rows in assessment_components: {c.fetchone()[0]}")
    c.execute("SELECT * FROM assessment_components LIMIT 5")
    for r in c.fetchall():
        print("  Component:", r)

    print("\n=== SECTION INSTRUCTIONS SAMPLE ===")
    c.execute("""
        SELECT s.name, s.instructions, COUNT(*)
        FROM sections s
        WHERE s.instructions IS NOT NULL AND TRIM(s.instructions) != ''
        GROUP BY s.name, s.instructions
        ORDER BY COUNT(*) DESC LIMIT 10
    """)
    for name, inst, cnt in c.fetchall():
        print(f"  [{cnt}x] Sec '{name}': {repr(inst)}")

    print("\n=== QUESTION STRUCTURED_CONTENT INSPECTION ===")
    c.execute("""
        SELECT q.id, q.question_number, q.marks, q.is_alternative, q.structured_content
        FROM questions q
        WHERE q.structured_content IS NOT NULL AND TRIM(q.structured_content) != '' AND q.structured_content != 'null'
        LIMIT 10
    """)
    for qid, qnum, m, is_alt, sc in c.fetchall():
        print(f"  Q {qid} (num={qnum}, m={m}, alt={is_alt}): {sc[:120]}")

    print("\n=== HOW IS_ALTERNATIVE IS DISTRIBUTED ACROSS SECTIONS ===")
    c.execute("""
        SELECT s.name, COUNT(q.id) as total_q, SUM(CASE WHEN q.is_alternative = 1 THEN 1 ELSE 0 END) as alt_q
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        GROUP BY s.name
        ORDER BY total_q DESC LIMIT 15
    """)
    for sname, tot_q, alt_q in c.fetchall():
        print(f"  Sec '{sname}': {tot_q} total Qs, {alt_q} alternative Qs ({alt_q/tot_q*100:.1f}%)")

    print("\n=== TYPICAL ENDSEM EXAM STRUCTURE (e.g. Exam 13, 22, 24 in Course 1) ===")
    for eid in [13, 22, 24]:
        print(f"\n--- Exam {eid} ---")
        c.execute("SELECT e.year, e.term, e.assessment_type FROM exams e WHERE e.id = ?", (eid,))
        print("Exam header:", c.fetchone())
        c.execute("""
            SELECT s.id, s.name, s.instructions, COUNT(q.id) as q_cnt,
                   GROUP_CONCAT(DISTINCT CAST(q.marks AS TEXT)) as marks_list,
                   SUM(CASE WHEN q.is_alternative = 1 THEN 1 ELSE 0 END) as alt_cnt,
                   MIN(CAST(q.question_number AS INTEGER)) as min_num,
                   MAX(CAST(q.question_number AS INTEGER)) as max_num
            FROM sections s
            LEFT JOIN questions q ON s.id = q.section_id
            WHERE s.exam_id = ?
            GROUP BY s.id
            ORDER BY s.id
        """, (eid,))
        for sec in c.fetchall():
            print(f"  Section {sec[0]} ('{sec[1]}'): {sec[3]} Qs | Marks: {sec[4]} | Alts: {sec[5]} | Range: {sec[6]}-{sec[7]} | Inst: {repr(sec[2])}")

    conn.close()

if __name__ == '__main__':
    inspect_details()
