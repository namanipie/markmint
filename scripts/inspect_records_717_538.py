import json
import sqlite3
import os
import hashlib

with open('data/manifests/first_year_union_manifest.json', encoding='utf-8') as f:
    manifest = json.load(f)

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

def inspect_rec(idx, rec):
    print(f"\n==================== RECORD {idx} ====================")
    for k, v in rec.items():
        print(f"  {k}: {v}")
    
    sha = rec.get('sha256')
    if sha:
        cur.execute("SELECT id, title, document_hash, resource_type, processing_status, extraction_status FROM documents WHERE document_hash = ?", (sha,))
        docs = cur.fetchall()
        print(f"  DB matching documents by sha ({len(docs)}):")
        for d in docs:
            print("    ", d)
    
    url = rec.get('source_url')
    if url:
        cur.execute("SELECT id, title, document_hash FROM documents WHERE original_url = ?", (url,))
        docs_url = cur.fetchall()
        print(f"  DB matching documents by url ({len(docs_url)}):")
        for d in docs_url:
            print("    ", d)

    local_path = rec.get('local_path')
    if local_path and os.path.exists(local_path):
        size = os.path.getsize(local_path)
        with open(local_path, 'rb') as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest()
        print(f"  Local file exists: {local_path} ({size} bytes)")
        print(f"  Actual SHA-256:    {actual_sha}")
        print(f"  Hash matches:      {actual_sha == sha}")
    else:
        print(f"  Local file exists: False (path: {local_path})")

inspect_rec(717, manifest[717])
inspect_rec(538, manifest[538])

con.close()
