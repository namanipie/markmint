"""
Dedicated Downloader and Corpus Stager for Semesters 5 & 6 Core Courses:
- Course 32: Discrete Mathematics (SEM5-DM / 21MAB301T)
- Course 33: Formal Languages and Automata (SEM5-FLA / 21CSC301T)
- Course 34: Computer Networks (SEM5-CN / 21CSC302J)
- Course 35: Software Engineering and Project Management (SEM6-SEPM / 21CSC303J)
- Course 36: Compiler Design (SEM6-CD / 21CSC305J)
- Course 37: Data Science (SEM6-DS / 21CSC304P)

Downloads all authentic PYQs and unit materials from Studique API into corpus/.
"""

import os
import sys
import time
import requests
import hashlib
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.services.scraper.downloader import sanitize_filesystem_name

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

COURSE_TARGETS = [
    {
        "id": 32,
        "name": "Discrete Mathematics",
        "code": "SEM5-DM",
        "canonical_code": "21MAB301T",
        "semester": 5,
        "department": "Mathematics",
        "studique_key": "Discrete Mathematics (DM)"
    },
    {
        "id": 33,
        "name": "Formal Languages and Automata",
        "code": "SEM5-FLA",
        "canonical_code": "21CSC301T",
        "semester": 5,
        "department": "Computing Technologies",
        "studique_key": "Formal Languages and Automata (FLA)"
    },
    {
        "id": 34,
        "name": "Computer Networks",
        "code": "SEM5-CN",
        "canonical_code": "21CSC302J",
        "semester": 5,
        "department": "Computing Technologies",
        "studique_key": "Computer Networks (CN)"
    },
    {
        "id": 35,
        "name": "Software Engineering and Project Management",
        "code": "SEM6-SEPM",
        "canonical_code": "21CSC303J",
        "semester": 6,
        "department": "Computing Technologies",
        "studique_key": "Software Engineering and Project Management (SEPM)"
    },
    {
        "id": 36,
        "name": "Compiler Design",
        "code": "SEM6-CD",
        "canonical_code": "21CSC305J",
        "semester": 6,
        "department": "Computing Technologies",
        "studique_key": "Compiler Design (CD)"
    },
    {
        "id": 37,
        "name": "Data Science",
        "code": "SEM6-DS",
        "canonical_code": "21CSC304P",
        "semester": 6,
        "department": "Computing Technologies",
        "studique_key": "Data Science (DS)"
    }
]

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

def download_gdrive(file_id: str, dest_path: str, max_retries: int = 2) -> bool:
    if os.path.exists(dest_path) and is_valid_pdf(dest_path):
        print(f"    [SKIP] Already on disk ({os.path.getsize(dest_path)} bytes): {dest_path}")
        return True

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    for attempt in range(1, max_retries + 1):
        temp_dest = dest_path + ".tmp"
        try:
            session = requests.Session()
            response = session.get(url, headers=HEADERS, stream=True, timeout=12)
            
            for key, val in response.cookies.items():
                if key.startswith("download_warning"):
                    url_confirm = f"{url}&confirm={val}"
                    response = session.get(url_confirm, headers=HEADERS, stream=True, timeout=12)
                    break

            if response.status_code == 200:
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
                    print(f"    [REJECT] Not valid PDF ({os.path.getsize(temp_dest)} bytes)")
                    if os.path.exists(temp_dest):
                        os.remove(temp_dest)
            else:
                print(f"    [FAIL] HTTP status {response.status_code}")
        except Exception as e:
            print(f"    [ERROR] {e}")
            if os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except Exception:
                    pass

        time.sleep(1)

    return False

def run_download():
    print("=" * 70)
    print("  MARKMINT SEMESTERS 5 & 6 CORPUS INGESTION")
    print("=" * 70)

    r = requests.get("https://studique.in/api/resource/list", headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print(f"Failed to fetch Studique catalog: {r.status_code}")
        return

    data = r.json()
    subject_map = {s.get("name"): s for s in data.get("subjects", [])}

    total_downloaded = 0
    total_found = 0

    for target in COURSE_TARGETS:
        skey = target["studique_key"]
        subj = subject_map.get(skey)
        if not subj:
            print(f"Subject '{skey}' not found in Studique API")
            continue

        cname = target["name"]
        sem = target["semester"]
        pyqs = subj.get("pyqs", [])
        ppts = subj.get("ppts", [])
        print(f"\nProcessing Course {target['id']}: {cname} (Sem {sem}) - {len(pyqs)} PYQs, {len(ppts)} PPTs")

    print("\n--- PHASE 1: DOWNLOADING ALL EXAMINATION PAPERS (PYQs) ---")
    for target in COURSE_TARGETS:
        skey = target["studique_key"]
        subj = subject_map.get(skey)
        if not subj:
            continue

        cname = target["name"]
        sem = target["semester"]
        pyqs = subj.get("pyqs", [])
        print(f"\n[Course {target['id']}] {cname} (Sem {sem}): {len(pyqs)} PYQs to download...")

        for pyq in pyqs:
            total_found += 1
            pname = pyq.get("name", "PYQ")
            fkey = pyq.get("fileKey")
            if not fkey:
                continue
            safe_title = sanitize_filesystem_name(f"{cname} - PYQ {pname}")
            dest = os.path.join(BASE_DIR, "corpus", f"Semester_{sem}", cname, "EXAMINATION_PAPERS", f"{safe_title}.pdf")
            if download_gdrive(fkey, dest):
                total_downloaded += 1

    print("\n--- PHASE 2: DOWNLOADING STUDY MATERIALS (PPTS) ---")
    for target in COURSE_TARGETS:
        skey = target["studique_key"]
        subj = subject_map.get(skey)
        if not subj:
            continue

        cname = target["name"]
        sem = target["semester"]
        ppts = subj.get("ppts", [])
        print(f"\n[Course {target['id']}] {cname} (Sem {sem}): {len(ppts)} Slide decks...")

        for ppt in ppts:
            total_found += 1
            pname = ppt.get("name", "Slide")
            fkey = ppt.get("fileKey")
            if not fkey:
                continue
            safe_title = sanitize_filesystem_name(f"{cname} - Notes {pname}")
            dest = os.path.join(BASE_DIR, "corpus", f"Semester_{sem}", cname, "STUDY_MATERIAL", f"{safe_title}.pdf")
            if download_gdrive(fkey, dest):
                total_downloaded += 1


    print("\n" + "=" * 70)
    print(f"Summary: Discovered {total_found} assets, Downloaded/Verified {total_downloaded} files.")
    print("=" * 70)

if __name__ == "__main__":
    run_download()
