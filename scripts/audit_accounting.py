import json
import sqlite3
from collections import Counter

# Load manifest
with open('data/manifests/first_year_union_manifest.json', encoding='utf-8') as f:
    manifest = json.load(f)

print(f"Total records in manifest: {len(manifest)}")

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

# Get all document hashes in DB
cur.execute("SELECT id, document_hash, resource_type, processing_status, extraction_status FROM documents")
db_docs = cur.fetchall()
db_doc_hashes = {r[1]: r for r in db_docs}

# Get provenances
cur.execute("SELECT document_id, source_url, resolved_url FROM document_provenances")
db_provs = cur.fetchall()

# Count manifest download statuses
download_statuses = Counter(r.get('download_status') for r in manifest)
print("Manifest download_status breakdown:")
for k, v in download_statuses.items():
    print(f"  {k}: {v}")

# Count classifications
classifications = Counter(r.get('classification') for r in manifest)
print("\nManifest classification breakdown:")
for k, v in classifications.items():
    print(f"  {k}: {v}")

# Count ingestion_status
ingestion_statuses = Counter(r.get('ingestion_status') for r in manifest)
print("\nManifest ingestion_status breakdown:")
for k, v in ingestion_statuses.items():
    print(f"  {k}: {v}")

# In-depth reconciliation
canonical_downloaded = [r for r in manifest if r.get('download_status') == 'DOWNLOADED']
duplicate_records = [r for r in manifest if r.get('download_status') == 'DUPLICATE']
failed_downloads = [r for r in manifest if r.get('download_status') == 'FAILED']
invalid_records = [r for r in manifest if r.get('download_status') in ('INVALID', 'SKIPPED', 'NOT_FOUND', None)]

print(f"\nReconciliation totals:")
print(f"  Canonical DOWNLOADED: {len(canonical_downloaded)}")
print(f"  DUPLICATE records:    {len(duplicate_records)}")
print(f"  FAILED downloads:     {len(failed_downloads)}")
print(f"  INVALID/SKIPPED:      {len(invalid_records)}")
print(f"  Sum:                  {len(canonical_downloaded) + len(duplicate_records) + len(failed_downloads) + len(invalid_records)}")

# Cross-reference canonical DOWNLOADED against DB
downloaded_in_db = [r for r in canonical_downloaded if r.get('sha256') in db_doc_hashes]
downloaded_not_in_db = [r for r in canonical_downloaded if r.get('sha256') not in db_doc_hashes]
print(f"\nCanonical DOWNLOADED in DB:     {len(downloaded_in_db)}")
print(f"Canonical DOWNLOADED not in DB: {len(downloaded_not_in_db)}")
if downloaded_not_in_db:
    for r in downloaded_not_in_db[:5]:
        print("  Missing canonical:", r.get('title'), r.get('sha256'))

# Duplicate records mapped in DB
dup_in_db = [r for r in duplicate_records if r.get('sha256') in db_doc_hashes]
dup_not_in_db = [r for r in duplicate_records if r.get('sha256') not in db_doc_hashes]
print(f"DUPLICATE records in DB:        {len(dup_in_db)}")
print(f"DUPLICATE records not in DB:    {len(dup_not_in_db)}")

# Check DB document types and statuses
cur.execute("SELECT resource_type, extraction_status, processing_status, COUNT(*) FROM documents GROUP BY resource_type, extraction_status, processing_status")
doc_types = cur.fetchall()
print("\nDB Documents breakdown by resource_type, extraction_status, processing_status:")
for rt, es, ps, cnt in doc_types:
    print(f"  resource_type={rt!r:<18} extraction_status={es!r:<22} processing_status={ps!r:<12}: {cnt}")

# Check exams
cur.execute("SELECT COUNT(*) FROM exams")
exam_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT document_id) FROM exams")
exam_doc_count = cur.fetchone()[0]
print(f"\nTotal Exams in DB: {exam_count} (across {exam_doc_count} distinct documents)")

con.close()
