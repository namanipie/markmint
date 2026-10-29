import sqlite3
from collections import Counter

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

# 1. Total study_evidence rows
cur.execute("SELECT COUNT(*) FROM study_evidences")
total_evidence = cur.fetchone()[0]
print(f"Total StudyEvidence rows: {total_evidence}")

# 2. Check source documents: are any from PYQs?
cur.execute('''
    SELECT d.resource_type, COUNT(se.id)
    FROM study_evidences se
    JOIN documents d ON se.document_id = d.id
    GROUP BY d.resource_type
''')
by_res_type = cur.fetchall()
print("\nStudyEvidence by Document resource_type:")
for rt, cnt in by_res_type:
    print(f"  {str(rt):<25}: {cnt} rows")

# Check if any PYQ document generated study evidence
cur.execute('''
    SELECT se.id, d.id, d.title, d.resource_type, c.canonical_name
    FROM study_evidences se
    JOIN documents d ON se.document_id = d.id
    LEFT JOIN concepts c ON se.concept_id = c.id
    WHERE d.resource_type IN ('PYQ', 'examination papers / PYQs', 'CT papers')
''')
pyq_evidences = cur.fetchall()
print(f"\nStudyEvidence rows from PYQ documents (must be 0): {len(pyq_evidences)}")

# 3. Check concept quality: garbage/headers/fragments
cur.execute('''
    SELECT c.canonical_name, COUNT(*) as cnt
    FROM study_evidences se
    JOIN concepts c ON se.concept_id = c.id
    GROUP BY c.canonical_name
    ORDER BY cnt DESC
    LIMIT 25
''')
top_concepts = cur.fetchall()
print("\nTop 25 most frequent concepts in StudyEvidence:")
for cname, cnt in top_concepts:
    print(f"  {cnt:3d}x : {cname}")

# Sample StudyEvidence rows across multiple documents
cur.execute('''
    SELECT se.id, d.title, c.canonical_name, se.knowledge_type, se.confidence, se.original_text
    FROM study_evidences se
    JOIN documents d ON se.document_id = d.id
    JOIN concepts c ON se.concept_id = c.id
    ORDER BY se.id DESC
    LIMIT 15
''')
samples = cur.fetchall()
print(f"\nSample 15 StudyEvidence rows:")
for s in samples:
    seid, dtitle, cname, ktype, conf, otext = s
    otext_clean = (otext or '')[:80].replace('\n', ' ')
    print(f"  ID {seid:4d} | Doc: {dtitle[:30]:30s} | Concept: {cname[:25]:25s} | Type: {ktype} | Conf: {conf} | Text: {otext_clean}")

# 4. Investigate empty knowledge extraction documents (completed_empty)
cur.execute('''
    SELECT d.id, d.title, d.resource_type, d.original_url
    FROM documents d
    WHERE d.extraction_status = 'completed_empty'
    LIMIT 15
''')
empty_docs = cur.fetchall()
print(f"\nSample empty knowledge documents (completed_empty):")
for ed in empty_docs:
    print(f"  Doc {ed[0]:3d} | Type: {ed[2]} | Title: {ed[1][:60]}")

# 5. Check total unique concepts created
cur.execute("SELECT COUNT(*) FROM concepts")
total_concepts = cur.fetchone()[0]
print(f"\nTotal unique Concepts in DB: {total_concepts}")

con.close()
