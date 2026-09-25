import sqlite3
import re
from collections import defaultdict

def main():
    conn = sqlite3.connect('production_corpus.db')
    c = conn.cursor()

    # Get all 76 missing exams
    c.execute('''
        SELECT e.id, c.id, c.name, e.assessment_type, d.id, d.title, d.original_url, d.source, d.document_hash
        FROM exams e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN documents d ON e.document_id = d.id
        WHERE e.year IS NULL
        ORDER BY c.name, e.id
    ''')
    missing_exams = c.fetchall()

    print(f"=== DETAILED AUDIT OF {len(missing_exams)} MISSING-YEAR EXAMS ===")

    for row in missing_exams:
        eid, cid, cname, atype, did, title, url, src, doc_hash = row
        
        # Get section instructions and questions
        c.execute('''
            SELECT s.name, s.instructions, count(q.id)
            FROM sections s
            LEFT JOIN questions q ON q.section_id = s.id
            WHERE s.exam_id = ?
            GROUP BY s.id
        ''', (eid,))
        sections = c.fetchall()

        # Get first 5 questions text
        c.execute('''
            SELECT q.question_number, q.original_text, q.classification_input
            FROM sections s
            JOIN questions q ON q.section_id = s.id
            WHERE s.exam_id = ?
            LIMIT 5
        ''', (eid,))
        sample_qs = c.fetchall()

        # Search for year patterns in title, url, instructions, and questions
        texts_to_check = [
            ("title", title or ""),
            ("url", url or ""),
        ]
        for s in sections:
            if s[1]:
                texts_to_check.append(("section_instructions", s[1]))
        for q in sample_qs:
            if q[1]:
                texts_to_check.append(("question_text", q[1]))
            if q[2]:
                texts_to_check.append(("classification_input", q[2]))

        # Look for candidate years
        candidates = []
        for src_label, txt in texts_to_check:
            # 4 digit years
            matches = re.findall(r'\b(20[1-2][0-9])\b', txt)
            for m in matches:
                candidates.append((int(m), src_label, txt[:100].replace('\n', ' ')))
            # Academic sessions like 2023-24, 2022-2023
            sess_matches = re.findall(r'\b(20[1-2][0-9])\s*[-–/]\s*([0-9]{2,4})\b', txt)
            for m1, m2 in sess_matches:
                candidates.append((f"{m1}-{m2}", src_label, txt[:100].replace('\n', ' ')))

        total_q = sum(s[2] for s in sections)
        print(f"\n[EXAM {eid}] Course: {cname} | AssessmentType: {atype} | Total Qs: {total_q}")
        print(f"  Title: {title}")
        print(f"  URL: {url}")
        if candidates:
            print(f"  --> CANDIDATES FOUND ({len(candidates)}):")
            for cand, clabel, ctxt in candidates[:4]:
                print(f"      * {cand} (from {clabel}): {ctxt}")
        else:
            print(f"  --> NO OBVIOUS YEAR FOUND in title/URL/sample questions")

    conn.close()

if __name__ == '__main__':
    main()
