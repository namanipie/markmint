import os
import sys
import json
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.scraper.downloader import ResourceDownloader

def check_uniqueness():
    conn = sqlite3.connect("production_corpus.db")
    c = conn.cursor()
    
    # Map hash -> doc info
    db_hashes = {}
    for r in c.execute("SELECT document_hash, id, title, subject FROM documents").fetchall():
        if r[0]:
            db_hashes[r[0]] = {"id": r[1], "title": r[2], "subject": r[3]}
            
    with open("data/s3_s4/second_year_inventory.json", "r", encoding="utf-8") as f:
        inv = json.load(f)
        
    dl = ResourceDownloader()
    
    # Filter candidates in Category A
    cat_a_items = [it for it in inv["items"] if it["category"] == "A"]
    print(f"Total Category A candidate exam items to verify: {len(cat_a_items)}")
    
    new_genuine_papers = []
    already_in_db = []
    failed_downloads = []
    
    # Test each candidate
    for idx, it in enumerate(cat_a_items, 1):
        url = it["resolved_url"] or it["source_url"]
        cid = it["course_id"]
        title = it["title"]
        site = it["source_site"]
        
        print(f"[{idx}/{len(cat_a_items)}] Checking [{site}] Course {cid}: {title}...")
        path, err = dl.download_to_temp(url)
        if not path or err:
            print(f"   FAILED download: {err}")
            failed_downloads.append({"item": it, "error": err})
            continue
            
        v = dl.validate_pdf_file(path)
        if not v.is_valid:
            print(f"   INVALID PDF: {v.failure_reason}")
            failed_downloads.append({"item": it, "error": v.failure_reason})
            if os.path.exists(path):
                os.remove(path)
            continue
            
        file_hash = v.sha256
        it["sha256"] = file_hash
        it["file_size"] = v.file_size
        it["local_temp_path"] = path
        
        if file_hash in db_hashes:
            match = db_hashes[file_hash]
            print(f"   ALREADY IN DB! Match: Doc #{match['id']} - {match['title']}")
            already_in_db.append({"item": it, "db_match": match})
            # Clean up temp
            if os.path.exists(path):
                os.remove(path)
        else:
            print(f"   NEW GENUINE PAPER! Hash: {file_hash[:12]} ({v.file_size} bytes)")
            new_genuine_papers.append(it)
            
    print("\n==================================================")
    print("VERIFICATION OF CATEGORY A CANDIDATE EXAM PAPERS")
    print("==================================================")
    print(f"Total Tested:           {len(cat_a_items)}")
    print(f"Already in DB (Hash):   {len(already_in_db)}")
    print(f"Failed / Invalid:       {len(failed_downloads)}")
    print(f"Truly NEW Genuine Exams:{len(new_genuine_papers)}")
    print("==================================================")
    
    for p in new_genuine_papers:
        print(f"  NEW: Course {p['course_id']} [{p['canonical_code']}] - {p['title']} (Year={p['year']}, Type={p['assessment_type']}, Hash={p['sha256'][:10]})")
        
    out_path = "data/s3_s4/verified_new_candidates.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "truly_new_papers": new_genuine_papers,
            "already_in_db": already_in_db,
            "failed": failed_downloads
        }, f, indent=2)
    print(f"\nSaved report to {out_path}")

if __name__ == "__main__":
    check_uniqueness()
