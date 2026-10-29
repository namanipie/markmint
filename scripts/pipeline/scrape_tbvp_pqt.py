"""
Dedicated Scraper & Downloader for TBVP (Course 30) and PQT (Course 31).
Downloads all available PYQs, Syllabi, and Study Materials (PPTs) from:
1. Studique API (live)
2. The Helpers cache (downloads.db)
Stores validated PDFs into corpus directory:
  corpus/Semester_3/Transforms and Boundary Value Problems/
  corpus/Semester_4/Probability and Queueing Theory/
"""

import os
import sys
import time
import requests
import hashlib
import sqlite3
import re
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.scraper.downloader import sanitize_filesystem_name

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_valid_pdf(filepath: str) -> bool:
    if not os.path.exists(filepath):
        return False
    size = os.path.getsize(filepath)
    if size < 500:
        return False
    with open(filepath, "rb") as f:
        head = f.read(10)
        f.seek(max(0, size - 2048))
        tail = f.read()
    return head.startswith(b"%PDF-") and b"%%EOF" in tail

def download_gdrive(file_id: str, dest_path: str, max_retries: int = 3) -> bool:
    if os.path.exists(dest_path) and is_valid_pdf(dest_path):
        print(f"    [SKIP] Already on disk ({os.path.getsize(dest_path)} bytes): {dest_path}")
        return True

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    for attempt in range(1, max_retries + 1):
        try:
            print(f"    [DOWNLOAD] {file_id} (Attempt {attempt})...")
            # Session to handle google drive confirm token for large files
            session = requests.Session()
            response = session.get(url, headers=HEADERS, stream=True, timeout=30)
            
            # Check for confirm token
            for key, val in response.cookies.items():
                if key.startswith("download_warning"):
                    url_confirm = f"{url}&confirm={val}"
                    response = session.get(url_confirm, headers=HEADERS, stream=True, timeout=30)
                    break

            if response.status_code == 200:
                temp_dest = dest_path + ".tmp"
                with open(temp_dest, "wb") as f:
                    for chunk in response.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)

                if is_valid_pdf(temp_dest):
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    os.rename(temp_dest, dest_path)
                    print(f"    [OK] Saved: {dest_path} ({os.path.getsize(dest_path)} bytes)")
                    return True
                else:
                    print(f"    [REJECT] Not a valid PDF (size {os.path.getsize(temp_dest)} bytes)")
                    if os.path.exists(temp_dest):
                        os.remove(temp_dest)
            else:
                print(f"    [FAIL] HTTP status {response.status_code}")
        except Exception as e:
            print(f"    [ERROR] {e}")

        time.sleep(2 ** attempt)

    return False

def collect_and_download_tbvp_pqt():
    print("=" * 70)
    print("  MARKMINT TARGETED SCARPER: TBVP & PQT")
    print("=" * 70)

    stats = {
        "discovered": 0,
        "downloaded": 0,
        "failed": 0,
    }

    downloaded_records: List[Dict[str, Any]] = []

    # 1. Fetch Studique catalog
    print("\n[Phase 1] Querying Studique API...")
    try:
        r = requests.get("https://studique.in/api/resource/list", headers=HEADERS, timeout=15)
        studique_data = r.json()
        for subj in studique_data.get("subjects", []):
            name = subj.get("name", "")
            is_tbvp = "transforms" in name.lower() and "boundary" in name.lower()
            is_pqt = "probability" in name.lower() and "queueing" in name.lower()

            if not (is_tbvp or is_pqt):
                continue

            sem = 3 if is_tbvp else 4
            canonical_name = "Transforms and Boundary Value Problems" if is_tbvp else "Probability and Queueing Theory"
            course_id = 30 if is_tbvp else 31

            print(f"\nProcessing Studique subject: {name} (Course {course_id}, Sem {sem})")

            # PYQs
            for pyq in subj.get("pyqs", []):
                p_name = pyq.get("name", "PYQ")
                fkey = pyq.get("fileKey")
                if not fkey:
                    continue
                stats["discovered"] += 1
                safe_title = sanitize_filesystem_name(f"{canonical_name} - PYQ {p_name}")
                dest = os.path.join("corpus", f"Semester_{sem}", canonical_name, "EXAMINATION_PAPERS", f"{safe_title}.pdf")
                ok = download_gdrive(fkey, dest)
                if ok:
                    stats["downloaded"] += 1
                    downloaded_records.append({
                        "source": "Studique",
                        "course_id": course_id,
                        "subject": canonical_name,
                        "semester": sem,
                        "type": "PYQ",
                        "title": f"{canonical_name} - PYQ {p_name}",
                        "path": dest,
                        "sha256": compute_sha256(dest),
                        "file_id": fkey
                    })
                else:
                    stats["failed"] += 1

            # PPTs (Study Material)
            for ppt in subj.get("ppts", []):
                p_name = ppt.get("name", "Lecture Notes")
                fkey = ppt.get("fileKey")
                if not fkey:
                    continue
                stats["discovered"] += 1
                safe_title = sanitize_filesystem_name(f"{canonical_name} - {p_name}")
                dest = os.path.join("corpus", f"Semester_{sem}", canonical_name, "STUDY_MATERIAL", f"{safe_title}.pdf")
                ok = download_gdrive(fkey, dest)
                if ok:
                    stats["downloaded"] += 1
                    downloaded_records.append({
                        "source": "Studique",
                        "course_id": course_id,
                        "subject": canonical_name,
                        "semester": sem,
                        "type": "STUDY_MATERIAL",
                        "title": f"{canonical_name} - {p_name}",
                        "path": dest,
                        "sha256": compute_sha256(dest),
                        "file_id": fkey
                    })
                else:
                    stats["failed"] += 1

            # Syllabus
            for syl in subj.get("syllabus", []):
                p_name = syl.get("name", "Syllabus")
                fkey = syl.get("fileKey")
                if not fkey:
                    continue
                stats["discovered"] += 1
                safe_title = sanitize_filesystem_name(f"{canonical_name} - {p_name}")
                dest = os.path.join("corpus", f"Semester_{sem}", canonical_name, "SYLLABUS", f"{safe_title}.pdf")
                ok = download_gdrive(fkey, dest)
                if ok:
                    stats["downloaded"] += 1
                    downloaded_records.append({
                        "source": "Studique",
                        "course_id": course_id,
                        "subject": canonical_name,
                        "semester": sem,
                        "type": "SYLLABUS",
                        "title": f"{canonical_name} - {p_name}",
                        "path": dest,
                        "sha256": compute_sha256(dest),
                        "file_id": fkey
                    })
                else:
                    stats["failed"] += 1

    except Exception as e:
        print(f"[Error querying Studique] {e}")

    # 2. Fetch The Helpers entries from downloads.db
    print("\n[Phase 2] Querying The Helpers cache (downloads.db)...")
    db_cache_path = os.path.join("data", ".download_cache", "downloads.db")
    if os.path.exists(db_cache_path):
        conn = sqlite3.connect(db_cache_path)
        c = conn.cursor()
        rows = c.execute("SELECT id, local_path, source_metadata, sha256, url_normalized FROM downloads").fetchall()
        for r in rows:
            meta = r[2] or ""
            is_tbvp = "transforms" in meta.lower() and "boundary" in meta.lower()
            is_pqt = "probability" in meta.lower() and "queueing" in meta.lower()

            if not (is_tbvp or is_pqt):
                continue

            sem = 3 if is_tbvp else 4
            canonical_name = "Transforms and Boundary Value Problems" if is_tbvp else "Probability and Queueing Theory"
            course_id = 30 if is_tbvp else 31

            url = r[4] or ""
            # Extract Google drive file ID from URL
            m_id = re.search(r'id=([A-Za-z0-9_-]{25,})', url)
            if not m_id:
                continue
            file_id = m_id.group(1)

            filename = os.path.basename(r[1])
            title = filename[:-4] if filename.endswith(".pdf") else filename
            stats["discovered"] += 1

            dest = os.path.join("corpus", f"Semester_{sem}", canonical_name, "EXAMINATION_PAPERS", f"{sanitize_filesystem_name(title)}.pdf")
            ok = download_gdrive(file_id, dest)
            if ok:
                stats["downloaded"] += 1
                downloaded_records.append({
                    "source": "TheHelpers",
                    "course_id": course_id,
                    "subject": canonical_name,
                    "semester": sem,
                    "type": "PYQ",
                    "title": f"{canonical_name} - {title}",
                    "path": dest,
                    "sha256": compute_sha256(dest),
                    "file_id": file_id
                })
            else:
                stats["failed"] += 1
        conn.close()

    print(f"\n[Scrape Summary]")
    print(f"  Discovered: {stats['discovered']}")
    print(f"  Successfully Downloaded / Verified: {stats['downloaded']}")
    print(f"  Failed: {stats['failed']}")

    return downloaded_records

if __name__ == "__main__":
    records = collect_and_download_tbvp_pqt()
    print(f"\nTotal verified files ready for ingestion: {len(records)}")
