import sqlite3
import re
from collections import defaultdict, Counter

def normalize_section_name(name):
    if not name:
        return "UNKNOWN"
    n = name.upper().strip()
    if re.search(r'\bPART\s*[-–—]?\s*A\b|\bSECTION\s*A\b', n):
        return "PART_A"
    if re.search(r'\bPART\s*[-–—]?\s*B\b|\bSECTION\s*B\b', n):
        return "PART_B"
    if re.search(r'\bPART\s*[-–—]?\s*C\b|\bSECTION\s*C\b', n):
        return "PART_C"
    if re.search(r'\bMODULE\s*[-–—]?\s*I\b|\bMODULE\s*[-–—]?\s*1\b|\bUNIT\s*1\b', n):
        return "MODULE_1"
    if re.search(r'\bMODULE\s*[-–—]?\s*II\b|\bMODULE\s*[-–—]?\s*2\b|\bUNIT\s*2\b', n):
        return "MODULE_2"
    if re.search(r'\bMODULE\s*[-–—]?\s*III\b|\bMODULE\s*[-–—]?\s*3\b|\bUNIT\s*3\b', n):
        return "MODULE_3"
    if re.search(r'\bMODULE\s*[-–—]?\s*IV\b|\bMODULE\s*[-–—]?\s*4\b|\bUNIT\s*4\b', n):
        return "MODULE_4"
    if re.search(r'\bMODULE\s*[-–—]?\s*V\b|\bMODULE\s*[-–—]?\s*5\b|\bUNIT\s*5\b', n):
        return "MODULE_5"
    if "DEFAULT" in n or "MAIN" in n:
        return "DEFAULT"
    return n

def test_blueprint_discovery():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    canonical = [1, 2, 5, 28]

    for cid in canonical:
        c.execute("SELECT name FROM courses WHERE id = ?", (cid,))
        cname = c.fetchone()[0]
        print(f"\n==================================================")
        print(f"COURSE {cid}: {cname}")
        print(f"==================================================")

        c.execute("""
            SELECT e.id, e.year, e.assessment_type
            FROM exams e
            WHERE e.course_id = ?
            ORDER BY e.year, e.id
        """, (cid,))
        exams = c.fetchall()

        blueprints = defaultdict(list)

        for eid, yr, atype in exams:
            c.execute("""
                SELECT s.id, s.name, s.instructions,
                       COUNT(q.id) as q_cnt,
                       SUM(CASE WHEN q.is_alternative = 1 THEN 1 ELSE 0 END) as alt_cnt,
                       GROUP_CONCAT(DISTINCT q.marks) as marks_seen
                FROM sections s
                LEFT JOIN questions q ON s.id = q.section_id
                WHERE s.exam_id = ?
                GROUP BY s.id
                ORDER BY s.id
            """, (eid,))
            sec_rows = c.fetchall()

            sec_signatures = []
            for sid, sname, inst, q_cnt, alt_cnt, m_seen in sec_rows:
                norm_name = normalize_section_name(sname)
                m_list = [float(x) for x in m_seen.split(',') if x and x != 'None'] if m_seen else []
                m_list = sorted(list(set(m_list)))
                m_tag = "/".join(str(m) for m in m_list) if m_list else "unscored"
                sec_sig = f"{norm_name}({q_cnt}Q,alts={alt_cnt},m={m_tag})"
                sec_signatures.append(sec_sig)

            bp_key = " + ".join(sec_signatures) if sec_signatures else "NO_SECTIONS"
            blueprints[bp_key].append({
                "exam_id": eid,
                "year": yr,
                "assessment_type": atype,
                "sections": len(sec_rows)
            })

        print(f"Discovered {len(blueprints)} Distinct Structural Blueprints across {len(exams)} exams:")
        for bp_key, ex_list in sorted(blueprints.items(), key=lambda x: -len(x[1])):
            years = sorted(list(set(e['year'] for e in ex_list if e['year'] is not None)))
            types = sorted(list(set(e['assessment_type'] for e in ex_list if e['assessment_type'] is not None)))
            print(f"\n  Blueprint [{len(ex_list)} papers]:")
            print(f"    Structure: {bp_key}")
            print(f"    Years Observed: {years}")
            print(f"    Assessment Types: {types}")
            print(f"    Exam IDs: {[e['exam_id'] for e in ex_list]}")

    conn.close()

if __name__ == '__main__':
    test_blueprint_discovery()
