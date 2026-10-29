import sqlite3
from collections import defaultdict

def audit_section_units():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    canonical = [1, 2, 5, 28]
    for cid in canonical:
        c.execute("SELECT name FROM courses WHERE id = ?", (cid,))
        cname = c.fetchone()[0]
        print(f"\nCourse {cid}: {cname}")

        c.execute("""
            SELECT s.name, u.number, COUNT(DISTINCT q.id)
            FROM questions q
            JOIN sections s ON q.section_id = s.id
            JOIN exams e ON s.exam_id = e.id
            JOIN question_topic qt ON q.id = qt.question_id
            JOIN topics t ON qt.topic_id = t.id
            JOIN units u ON t.unit_id = u.id
            WHERE e.course_id = ?
            GROUP BY s.name, u.number
            ORDER BY s.name, u.number
        """, (cid,))

        sec_units = defaultdict(lambda: defaultdict(int))
        for sname, unum, cnt in c.fetchall():
            n = sname.upper().strip()
            if "PART - A" in n or "PART A" in n or "SECTION A" in n:
                sec_units["PART_A"][unum] += cnt
            elif "PART - B" in n or "PART B" in n or "SECTION B" in n:
                sec_units["PART_B"][unum] += cnt
            elif "PART - C" in n or "PART C" in n or "SECTION C" in n:
                sec_units["PART_C"][unum] += cnt

        for sec in ["PART_A", "PART_B", "PART_C"]:
            u_map = dict(sec_units[sec])
            print(f"  {sec}: Units {dict(sorted(u_map.items()))}")

    conn.close()

if __name__ == '__main__':
    audit_section_units()
