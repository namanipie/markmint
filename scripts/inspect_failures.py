import sqlite3
import json

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

print("--- FAILED OR PENDING DOCUMENTS IN DB ---")
cur.execute("SELECT id, title, document_hash, processing_status, extraction_status, original_url FROM documents WHERE extraction_status IN ('failed', 'pending')")
rows = cur.fetchall()
for r in rows:
    print(r)

con.close()

print("\n--- FAILED INGESTIONS IN MANIFEST ---")
with open('data/manifests/first_year_union_manifest.json', encoding='utf-8') as f:
    manifest = json.load(f)

for idx, rec in enumerate(manifest):
    if rec.get('ingestion_status') == 'FAILED':
        print(f"Index {idx}: title={rec.get('title')}, reason={rec.get('failure_reason')}, url={rec.get('source_url')}, local_path={rec.get('local_path')}")
