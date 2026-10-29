import sqlite3
import json
from collections import defaultdict, Counter

def audit_sections_and_questions():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    print("=== SECTIONS TABLE AUDIT ===")
    c.execute("SELECT COUNT(*) FROM sections")
    total_sections = c.fetchone()[0]
    print(f"Total Sections: {total_sections}")

    c.execute("SELECT name, COUNT(*) FROM sections GROUP BY name ORDER BY COUNT(*) DESC")
    sec_names = c.fetchall()
    print(f"Distinct Section Names ({len(sec_names)}):")
    for name, cnt in sec_names[:25]:
        print(f"  {repr(name)}: {cnt}")

    c.execute("SELECT COUNT(*) FROM sections WHERE instructions IS NOT NULL AND TRIM(instructions) != ''")
    inst_count = c.fetchone()[0]
    print(f"\nSections with non-empty instructions: {inst_count} / {total_sections} ({inst_count/total_sections*100:.1f}%)")

    c.execute("SELECT instructions, COUNT(*) FROM sections WHERE instructions IS NOT NULL AND TRIM(instructions) != '' GROUP BY instructions ORDER BY COUNT(*) DESC LIMIT 15")
    for inst, cnt in c.fetchall():
        print(f"  [{cnt}x] {repr(inst[:100])}")

    print("\n=== EXAM SECTION COUNTS ===")
    c.execute("""
        SELECT section_count, COUNT(*) FROM (
            SELECT exam_id, COUNT(*) as section_count FROM sections GROUP BY exam_id
        ) GROUP BY section_count ORDER BY section_count
    """)
    for sc, cnt in c.fetchall():
        print(f"  Exams with {sc} sections: {cnt}")

    print("\n=== QUESTION MARKS & ALTERNATIVE/CHOICE FLAGS ===")
    c.execute("SELECT COUNT(*) FROM questions WHERE marks IS NOT NULL")
    q_with_marks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE marks IS NULL")
    q_null_marks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE is_alternative = 1")
    q_alt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE structured_content IS NOT NULL AND TRIM(structured_content) != '' AND structured_content != '{}'")
    q_struct = c.fetchone()[0]

    print(f"Questions with marks: {q_with_marks} / 9013")
    print(f"Questions with NULL marks: {q_null_marks} / 9013")
    print(f"Questions with is_alternative=1: {q_alt} / 9013")
    print(f"Questions with non-empty structured_content: {q_struct} / 9013")

    # Sample structured_content
    c.execute("SELECT structured_content FROM questions WHERE structured_content IS NOT NULL AND TRIM(structured_content) != '' AND structured_content != '{}' LIMIT 5")
    sample_struct = c.fetchall()
    print("\nSample structured_content:")
    for s in sample_struct:
        print(f"  {s[0][:150]}")

    print("\n=== QUESTION NUMBERING FORMATS ===")
    c.execute("SELECT question_number, COUNT(*) FROM questions GROUP BY question_number ORDER BY COUNT(*) DESC LIMIT 20")
    for qn, cnt in c.fetchall():
        print(f"  {repr(qn)}: {cnt}")

    # Canonical courses audit
    canonical = [
        (1, "Calculus And Linear Algebra"),
        (2, "Chemistry"),
        (5, "Programming For Problem Solving"),
        (28, "Database Management Systems")
    ]

    print("\n=== CANONICAL COURSES STRUCTURAL BLUEPRINT AUDIT ===")
    for cid, cname in canonical:
        print(f"\n>>> Course {cid}: {cname} <<<")
        c.execute("""
            SELECT e.id, e.year, e.assessment_type, e.term, COUNT(DISTINCT s.id) as num_sec, COUNT(q.id) as num_q, SUM(q.marks) as total_marks
            FROM exams e
            LEFT JOIN sections s ON e.id = s.exam_id
            LEFT JOIN questions q ON s.id = q.section_id
            WHERE e.course_id = ?
            GROUP BY e.id
            ORDER BY e.year, e.id
        """, (cid,))
        exams_summary = c.fetchall()
        print(f"Total exams: {len(exams_summary)}")
        for eid, yr, atype, term, num_sec, num_q, tot_m in exams_summary[:8]:
            print(f"  Exam {eid} | Year: {yr} | Type: {atype} | Term: {term} | Sections: {num_sec} | Questions: {num_q} | Total Scored Marks: {tot_m}")

        # Check section details for this course
        c.execute("""
            SELECT s.name, COUNT(DISTINCT s.id) as sec_instances,
                   AVG(q_per_sec.q_count) as avg_q,
                   AVG(q_per_sec.marks_sum) as avg_marks,
                   GROUP_CONCAT(DISTINCT q_per_sec.distinct_marks) as marks_seen
            FROM sections s
            JOIN exams e ON s.exam_id = e.id
            LEFT JOIN (
                SELECT section_id, COUNT(id) as q_count, SUM(marks) as marks_sum,
                       GROUP_CONCAT(DISTINCT CAST(marks as TEXT)) as distinct_marks
                FROM questions GROUP BY section_id
            ) q_per_sec ON s.id = q_per_sec.section_id
            WHERE e.course_id = ?
            GROUP BY s.name
        """, (cid,))
        sec_breakdown = c.fetchall()
        print(f"  Sections in Course {cid}:")
        for sname, cnt, avg_q, avg_m, m_seen in sec_breakdown:
            avg_q_str = f"{avg_q:.1f}" if avg_q is not None else "N/A"
            avg_m_str = f"{avg_m:.1f}" if avg_m is not None else "N/A"
            print(f"    Sec '{sname}': {cnt} instances | Avg Qs: {avg_q_str} | Avg Marks: {avg_m_str} | Marks seen: {m_seen}")

    conn.close()

if __name__ == '__main__':
    audit_sections_and_questions()
