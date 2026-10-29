import sqlite3
import json

# 1. Update DB
con = sqlite3.connect('production_corpus.db')
cur = con.cursor()
cur.execute('''
    UPDATE documents 
    SET resource_type = 'STUDY_MATERIAL', extraction_status = 'completed_empty'
    WHERE id = 73
''')
con.commit()
print('DB Document 73 updated:', cur.execute('SELECT id, title, resource_type, extraction_status FROM documents WHERE id = 73').fetchone())
con.close()

# 2. Update Manifest
mpath = 'data/manifests/first_year_union_manifest.json'
with open(mpath, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

rec = manifest[538]
rec['classification'] = 'STUDY_MATERIAL'
rec['classification_confidence'] = 0.95
rec['classification_reasons'] = [
    'Detected assessment type: CT1',
    "Contains keyword 'PYQ'",
    'Contains CT assessment pattern (CT1/CT2/CT3)',
    "Prioritized explicit 'notes' in filename over inherited folder keywords"
]
rec['ingestion_status'] = 'INGESTED'
rec['failure_reason'] = None

with open(mpath, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)

print('Manifest record 538 updated successfully.')

# 3. Update Checkpoint
cpath = 'data/manifests/ingestion_checkpoint.json'
with open(cpath, 'r', encoding='utf-8') as f:
    checkpoint = json.load(f)

sha = rec['sha256']
checkpoint[sha] = {
    'status': 'INGESTED',
    'method': 'EMPTY_PAGES',
    'error': None
}
with open(cpath, 'w', encoding='utf-8') as f:
    json.dump(checkpoint, f, indent=2)

print('Checkpoint updated for', sha)
