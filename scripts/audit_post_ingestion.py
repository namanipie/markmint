import sqlite3
import json

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()
tables = [
    'courses', 'syllabuses', 'units', 'topics',
    'curriculum_mappings', 'student_topic_progress',
    'documents', 'document_provenances',
    'exams', 'sections', 'questions', 'study_evidences'
]
counts = {t: cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in tables}

cur.execute('PRAGMA foreign_key_check')
fk_violations = cur.fetchall()

cur.execute('SELECT COUNT(*) FROM questions WHERE section_id NOT IN (SELECT id FROM sections)')
orphan_questions = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM sections WHERE exam_id NOT IN (SELECT id FROM exams)')
orphan_sections = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM exams WHERE document_id NOT IN (SELECT id FROM documents)')
orphan_exams = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM document_provenances WHERE document_id NOT IN (SELECT id FROM documents)')
orphan_prov = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM study_evidences WHERE document_id NOT IN (SELECT id FROM documents)')
orphan_evidence = cur.fetchone()[0]

cur.execute('SELECT processing_status, extraction_status, COUNT(*) FROM documents GROUP BY processing_status, extraction_status')
doc_statuses = cur.fetchall()

cur.execute("SELECT id, title, document_hash FROM documents WHERE original_url LIKE '%1qwoWNyZmigsLqKgqQ8CXbF7Y7auCvaF3%'")
q_docs = cur.fetchall()

con.close()

with open('data/full_ingestion_pre_baseline.json') as f:
    baseline = json.load(f)['counts']

diff = {t: counts[t] - baseline[t] for t in tables}

print('=== TABLE COUNTS AND DELTAS ===')
for t in tables:
    print(f'{t:25s}: Baseline={baseline[t]:5d} | Current={counts[t]:5d} | Delta=+{diff[t]}')

print('\n=== INTEGRITY CHECKS ===')
print('FK Violations:', len(fk_violations))
print('Orphan Questions:', orphan_questions)
print('Orphan Sections:', orphan_sections)
print('Orphan Exams:', orphan_exams)
print('Orphan Provenances:', orphan_prov)
print('Orphan Study Evidences:', orphan_evidence)

print('\n=== DOCUMENT STATUS BREAKDOWN ===')
for ps, es, cnt in doc_statuses:
    print(f'processing_status={ps!r:<12} extraction_status={es!r:<20}: {cnt}')

print('\n=== QUARANTINED RECORD 717 IN DB ===')
print('Matches found (must be 0):', len(q_docs))
