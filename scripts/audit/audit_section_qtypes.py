import sqlite3
from collections import defaultdict

def audit_section_qtypes_and_units():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    c.execute("""
        SELECT s.name, q.question_type, COUNT(q.id)
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        GROUP BY s.name, q.question_type
        ORDER BY s.name, COUNT(q.id) DESC
    """)
    rows = c.fetchall()

    sec_qtypes = defaultdict(lambda: defaultdict(int))
    for sname, qtype, cnt in rows:
        n = sname.upper().strip()
        if "PART - A" in n or "PART A" in n or "SECTION A" in n:
            sec_qtypes["PART_A"][qtype] += cnt
        elif "PART - B" in n or "PART B" in n or "SECTION B" in n:
            sec_qtypes["PART_B"][qtype] += cnt
        elif "PART - C" in n or "PART C" in n or "SECTION C" in n:
            sec_qtypes["PART_C"][qtype] += cnt

    print("=== QUESTION TYPES BY CANONICAL SECTION ===")
    for sec in ["PART_A", "PART_B", "PART_C"]:
        print(f"\n--- {sec} ---")
        total = sum(sec_qtypes[sec].values())
        for qt, cnt in sorted(sec_qtypes[sec].items(), key=lambda x: -x[1]):
            print(f"  {qt}: {cnt} ({cnt/total*100:.1f}%)")

    conn.close()

if __name__ == '__main__':
    audit_section_qtypes_and_units()
