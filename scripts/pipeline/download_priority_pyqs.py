#!/usr/bin/env python3
"""
MarkMint Priority PYQ Downloader
Downloads verified past exam papers (PDFs) from Google Drive archives for the top priority courses.
"""

import os
import sys
import json
import re
import time
import urllib.request
import urllib.parse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESOURCES_JSON = os.path.join(BASE_DIR, "src", "lib", "course-resources.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "downloads", "priority_pyqs")

PRIORITY_COURSES = [
    "calculus-and-linear-algebra",
    "advanced-calculus-and-complex-analysis",
    "transforms-and-boundary-value-problems",
    "probability-and-queueing-theory",
    "discrete-mathematics",
    "programming-for-problem-solving",
    "data-structures-and-algorithms",
    "design-and-analysis-of-algorithms",
    "operating-systems",
    "computer-organization-and-architecture",
    "computer-networks",
    "compiler-design",
    "artificial-intelligence",
    "chemistry",
    "semiconductor-physics-and-computational-methods"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
}

def extract_drive_id(url):
    m = re.search(r'drive\.google\.com/(?:file/d/|drive/folders/|open\?id=|uc\?id=|uc\?export=download&id=)([a-zA-Z0-9_\-]+)', url)
    return m.group(1) if m else None

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()

def download_drive_file(drive_id, dest_path):
    """Download file from Google Drive, handling large file warning token if needed."""
    url = f"https://drive.google.com/uc?export=download&id={drive_id}"
    req = urllib.request.Request(url, headers=HEADERS)
    
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content_type = resp.headers.get('content-type', '').lower()
            data = resp.read()
            
            # If Google Drive serves a confirmation page for large files
            if 'text/html' in content_type and b'confirm=' in data:
                m = re.search(r'confirm=([0-9a-zA-Z_\-]+)', data.decode('utf-8', errors='ignore'))
                if m:
                    confirm_code = m.group(1)
                    confirm_url = f"https://drive.google.com/uc?export=download&confirm={confirm_code}&id={drive_id}"
                    req2 = urllib.request.Request(confirm_url, headers=HEADERS)
                    with urllib.request.urlopen(req2, timeout=25) as resp2:
                        data = resp2.read()

            if len(data) > 500:  # Valid non-empty file
                with open(dest_path, 'wb') as f:
                    f.write(data)
                return True, len(data)
            else:
                return False, f"File too small ({len(data)} bytes)"
    except Exception as e:
        return False, str(e)

def main():
    if not os.path.exists(RESOURCES_JSON):
        print(f"Error: {RESOURCES_JSON} not found!")
        sys.exit(1)

    with open(RESOURCES_JSON, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    manifest_path = os.path.join(OUTPUT_DIR, "download_manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    print(f"=== Starting MarkMint Priority PYQ Downloader ===")
    print(f"Targeting {len(PRIORITY_COURSES)} core courses...")

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    for slug in PRIORITY_COURSES:
        course_data = catalog.get(slug)
        if not course_data:
            # Try fuzzy match
            match = next((v for k, v in catalog.items() if slug in k or k in slug), None)
            course_data = match

        if not course_data:
            print(f"[-] Course '{slug}' not found in catalog, skipping.")
            continue

        c_name = course_data['courseName']
        pyqs = course_data.get('pyqs', [])
        course_dir = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(course_dir, exist_ok=True)

        print(f"\n[{slug}] {c_name}: {len(pyqs)} cataloged papers")

        for idx, p in enumerate(pyqs):
            title = p.get('title', f"Paper_{idx+1}")
            url = p.get('url', '')
            exam_type = p.get('examType', 'ENDSEM')
            year = p.get('year') or 'UnknownYear'
            drive_id = extract_drive_id(url)

            if not drive_id:
                continue

            file_id_key = f"{slug}_{drive_id}"
            clean_title = sanitize_filename(f"{exam_type}_{year}_{title}")
            dest_filename = f"{clean_title}.pdf" if not clean_title.lower().endswith('.pdf') else clean_title
            dest_path = os.path.join(course_dir, dest_filename)

            # Check if already downloaded
            if file_id_key in manifest and os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
                total_skipped += 1
                continue

            print(f"  --> Downloading: {dest_filename[:45]}...", end=" ", flush=True)
            success, result = download_drive_file(drive_id, dest_path)

            if success:
                print(f"[OK] ({result // 1024} KB)")
                total_downloaded += 1
                manifest[file_id_key] = {
                    "courseSlug": slug,
                    "courseName": c_name,
                    "examType": exam_type,
                    "year": year,
                    "title": title,
                    "driveId": drive_id,
                    "localPath": os.path.relpath(dest_path, BASE_DIR),
                    "sizeBytes": result,
                    "downloadedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            else:
                print(f"[FAIL] ({result})")
                total_failed += 1

            time.sleep(0.3)  # Respectful rate pacing

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n=== Download Batch Completed ===")
    print(f" - Downloaded: {total_downloaded} papers")
    print(f" - Already Cached: {total_skipped} papers")
    print(f" - Failed/Inaccessible: {total_failed} papers")
    print(f" - Total in Local Manifest: {len(manifest)} papers")
    print(f" - Manifest saved to: {os.path.relpath(manifest_path, BASE_DIR)}")

if __name__ == "__main__":
    main()
