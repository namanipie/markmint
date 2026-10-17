"""
Dedicated Downloader and Corpus Stager for Semesters 7 & 8 Core & Professional Elective Courses:
- Course 38: Internet of Things (SEM7-IOT / 21CSC401T)
- Course 39: Digital Image Processing (SEM7-DIP / 21CSC402T)
- Course 40: Security Governance, Risk and Compliance (SEM7-GRC / 21CSS401T)
- Course 41: Security Risk Management and Principles (SEM7-SRMP / 21CSC403T)
- Course 42: Information Security (SEM7-IS / 21CSC404T)
- Course 43: Digital Signal Processing (SEM8-DSP / 21ECC302J)

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
        "id": 38,
        "name": "Internet of Things",
        "code": "SEM7-IOT",
        "canonical_code": "21CSC401T",
        "semester": 7,
        "department": "Computing Technologies",
        "studique_key": "Internet of Things (IoT)"
    },
    {
        "id": 39,
        "name": "Digital Image Processing",
        "code": "SEM7-DIP",
        "canonical_code": "21CSC402T",
        "semester": 7,
        "department": "Computing Technologies",
        "studique_key": "Digital Image Processing (DIP)"
    },
    {
        "id": 40,
        "name": "Security Governance, Risk and Compliance",
        "code": "SEM7-GRC",
        "canonical_code": "21CSS401T",
        "semester": 7,
        "department": "Computing Technologies",
        "studique_key": "Security Governance, Risk and Compliance (GRC)"
    },
    {
        "id": 41,
        "name": "Security Risk Management and Principles",
        "code": "SEM7-SRMP",
        "canonical_code": "21CSC403T",
        "semester": 7,
        "department": "Computing Technologies",
        "studique_key": "Security Risk Management and Principles (SRMP)"
    },
    {
        "id": 42,
        "name": "Information Security",
        "code": "SEM7-IS",
        "canonical_code": "21CSC404T",
        "semester": 7,
        "department": "Computing Technologies",
        "studique_key": "Information Security (IS)"
    },
    {
        "id": 43,
        "name": "Digital Signal Processing",
        "code": "SEM8-DSP",
        "canonical_code": "21ECC302J",
        "semester": 8,
        "department": "Electronics and Communication Engineering",
        "studique_key": "Digital Signal Processing (DSP)"
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
    print("  MARKMINT SEMESTERS 7 & 8 CORPUS INGESTION")
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
