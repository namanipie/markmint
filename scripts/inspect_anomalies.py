import sqlite3
import json

with open('data/manifests/first_year_union_manifest.json', encoding='utf-8') as f:
    manifest = json.load(f)
manifest_by_hash = {r.get('sha256'): r for r in manifest if r.get('sha256')}

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

def inspect_q(qid):
    cur.execute('''
        SELECT q.id, q.section_id, q.question_number, q.original_text, q.marks,
               q.structured_content, q.extraction_method,
               s.name as s_name, e.id as e_id, e.year, e.assessment_type,
               d.id as doc_id, d.title, d.original_url, d.document_hash
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN documents d ON e.document_id = d.id
        WHERE q.id = ?
    ''', (qid,))
    row = cur.fetchone()
    if not row:
        print(f"QID {qid} not found")
        return
    rec = manifest_by_hash.get(row[14])
    lpath = rec.get('local_path') if rec else None
    print(f"\n==================== QID {qid} ====================")
    print(f"  Section: {row[7]} | Exam ID: {row[8]} (Year: {row[9]}, Type: {row[10]})")
    print(f"  Doc ID: {row[11]} | Title: {row[12]}")
    print(f"  Local Path: {lpath}")
    print(f"  QNum: {row[2]} | Marks: {row[4]} | ExtMethod: {row[6]}")
    print(f"  Original Text:\n{repr(row[3])}")
    print(f"  Structured Content:\n{repr(row[5])}")

inspect_q(3087)
inspect_q(4673)
inspect_q(6660)

cur.execute('''
    SELECT q.id, q.original_text, q.marks, d.title, d.document_hash
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    JOIN documents d ON e.document_id = d.id
    WHERE (
        (LENGTH(q.original_text) - LENGTH(REPLACE(q.original_text, '$', ''))) % 2 != 0
        AND LENGTH(q.original_text) - LENGTH(REPLACE(q.original_text, '$', '')) > 0
    )
    OR ABS((LENGTH(q.original_text) - LENGTH(REPLACE(q.original_text, '{', ''))) - 
           (LENGTH(q.original_text) - LENGTH(REPLACE(q.original_text, '}', '')))) > 2
''')
print("\n=== ALL BROKEN MATH QUESTIONS IN DB ===")
rows = cur.fetchall()
for r in rows:
    qid, qtext, marks, title, dhash = r
    rec = manifest_by_hash.get(dhash)
    lpath = rec.get('local_path') if rec else None
    print(f"\n[QID: {qid} | Marks: {marks} | Doc: {title[:40]}]")
    print(f"  Path: {lpath}")
    print(f"  Text: {repr(qtext[:120])}")

con.close()
