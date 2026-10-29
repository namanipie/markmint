import json
import os
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

def sanitize_filename(name: str) -> str:
    # Remove characters forbidden on Windows
    s = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Collapse multiple spaces or underscores
    s = re.sub(r'[\s_]+', ' ', s).strip()
    return s[:150]

def download_drive_file(file_id: str, dest_path: Path):
    if dest_path.exists() and dest_path.stat().st_size > 500:
        return True, "already exists"

    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Check if it was a redirect to a confirm token page
            final_url = resp.geturl()
            content = resp.read()

            # If Google Drive returns HTML asking for confirmation
            if b"Google Drive - Virus scan warning" in content or b"download_warning" in content:
                m = re.search(r'href="(/uc\?export=download[^"]+)"', content.decode('utf-8', errors='ignore'))
                if m:
                    confirm_url = "https://drive.google.com" + html.unescape(m.group(1))
                    req2 = urllib.request.Request(confirm_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req2, timeout=30) as resp2:
                        content = resp2.read()

            if len(content) < 500 and (b"<html" in content.lower() or b"<!doctype" in content.lower()):
                return False, f"Returned HTML instead of binary ({len(content)} bytes)"

            with open(dest_path, 'wb') as f:
                f.write(content)
            return True, f"Downloaded {len(content) // 1024} KB"
    except Exception as e:
        return False, str(e)

def main():
    print("==================================================")
    print("MarkMint: Verified Cycle Test (CT) Downloader")
    print("==================================================")

    catalog_path = 'data/verified_cycle_test_papers.json'
    with open(catalog_path, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    print(f"Loaded {len(papers)} verified Cycle Test papers to download.")

    base_dir = Path("data/downloads/cycle_tests")
    base_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0

    for idx, p in enumerate(papers, 1):
        subj = p.get('subject') or 'General'
        safe_subj = sanitize_filename(subj)
        subj_dir = base_dir / safe_subj
        subj_dir.mkdir(parents=True, exist_ok=True)

        cycle = p.get('cycle', 'CT')
        title = p.get('title', f"paper_{idx}")
        drive_id = p.get('drive_id')

        # Determine extension
        ext = ".pdf"
        if ".docx" in title.lower():
            ext = ".docx"
        elif ".jpg" in title.lower():
            ext = ".jpg"
        elif ".jpeg" in title.lower():
            ext = ".jpeg"
        elif ".png" in title.lower():
            ext = ".png"

        clean_title = sanitize_filename(title)
        if not clean_title.lower().endswith(ext):
            clean_title += ext

        dest_file = subj_dir / f"{cycle}_{clean_title}"

        print(f"[{idx}/{len(papers)}] [{cycle}] {subj}: {clean_title}...", end="", flush=True)

        if not drive_id:
            print(" [SKIP: No Drive ID]")
            fail_count += 1
            continue

        ok, msg = download_drive_file(drive_id, dest_file)
        if ok:
            print(f" [OK: {msg}]")
            p['local_path'] = str(dest_file).replace('\\', '/')
            p['file_size_kb'] = dest_file.stat().st_size // 1024
            success_count += 1
        else:
            print(f" [FAIL: {msg}]")
            fail_count += 1

        time.sleep(0.3)

    print("\n==================================================")
    print(f"Download complete: {success_count} succeeded, {fail_count} failed")
    print("==================================================")

    # Re-save catalog with local paths and file sizes
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    print(f"Updated {catalog_path} with local paths and verified sizes.")

if __name__ == '__main__':
    main()
