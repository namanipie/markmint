import json
import csv
import base64
import re
import urllib.request
import urllib.parse
import html
import sys

CT_REGEX = re.compile(
    r'(?i)\b(ct\s*[1-3]|cycle\s*test\s*[1-3]|cat\s*[1-3]|mid\s*sem|mid\s*term|internal\s*test|model|unit\s*test|surprise|ia\s*[1-3]|ct1|ct2|ct3|cat1|cat2)\b'
)

def decode_gradex_url(raw_url: str) -> str:
    m = re.search(r'action=open&r=([A-Za-z0-9+/=]+)', raw_url)
    if m:
        try:
            return base64.b64decode(m.group(1)).decode('utf-8', errors='ignore')
        except Exception:
            return raw_url
    return raw_url

def extract_drive_id(url: str):
    m = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return m.group(1), 'file'
    m = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if m:
        if 'folders' in url:
            return m.group(1), 'folder'
        return m.group(1), 'file'
    m = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
    if m:
        return m.group(1), 'folder'
    return None, None

def scrape_drive_folder(folder_id: str):
    """Scrapes files inside a public Google Drive folder using embeddedfolderview."""
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    items = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            page_html = resp.read().decode('utf-8', errors='ignore')

        # Matches id="entry-FILEID" and title in class="flip-entry-title"
        for m in re.finditer(r'id="entry-([a-zA-Z0-9_-]+)"[\s\S]*?<div class="flip-entry-title">([^<]+)</div>', page_html):
            file_id = m.group(1)
            title = html.unescape(m.group(2).strip())
            items.append({
                'file_id': file_id,
                'title': title,
                'url': f'https://drive.google.com/file/d/{file_id}/view'
            })
    except Exception as e:
        print(f"    [!] Error scraping folder {folder_id}: {e}")
        
    return items

def main():
    print("==================================================")
    print("MarkMint: Exhaustive Cycle Test (CT) Extractor")
    print("==================================================")
    sys.stdout.flush()

    # 1. Parse GradeX CSV with clean outer quote stripping
    gradex_items = []
    lines = []
    with open('data/gradex_subdeck_resources.csv', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            lines.append(line)

    reader = csv.DictReader(lines)
    for r in reader:
        sem = (r.get('semester') or '').strip()
        subj = (r.get('subject') or '').strip()
        for cat in ['pyqs', 'ppts', 'syllabus']:
            val = r.get(cat, '')
            if not val:
                continue
            pairs = re.findall(r'([^,|]+)\|([^\s,]+)', val)
            for title, raw_url in pairs:
                title = title.strip()
                url = decode_gradex_url(raw_url.strip())
                gradex_items.append({
                    'source': 'gradex',
                    'semester': sem,
                    'subject': subj,
                    'category': cat,
                    'title': title,
                    'url': url
                })

    print(f"[GradeX] Loaded {len(gradex_items)} total resource items across {len(set(x['subject'] for x in gradex_items))} subjects")

    # 2. Parse TheHelpers
    thehelpers_items = []
    with open('thehelpers_complete_catalog_utf8.json', 'r', encoding='utf-8') as f:
        th = json.load(f)
        for subj_name, data in th.items():
            for p in data.get('pyqs', []):
                thehelpers_items.append({
                    'source': 'thehelpers',
                    'semester': '',
                    'subject': subj_name,
                    'category': 'pyqs',
                    'title': p.get('name', ''),
                    'url': p.get('url', '')
                })
            for n in data.get('notes', []):
                thehelpers_items.append({
                    'source': 'thehelpers',
                    'semester': '',
                    'subject': subj_name,
                    'category': 'ppts',
                    'title': n.get('name', ''),
                    'url': n.get('url', '')
                })

    print(f"[TheHelpers] Loaded {len(thehelpers_items)} total resource items")

    # 3. Parse Studique
    studique_items = []
    with open('data/studique_resources.json', 'r', encoding='utf-8') as f:
        st = json.load(f)
        for s in st.get('subjects', []):
            subj_name = s.get('name', '').strip()
            for p in s.get('pyqs', []):
                key = p.get('fileKey', '')
                url = f"https://drive.google.com/file/d/{key}/view" if key else ""
                studique_items.append({
                    'source': 'studique',
                    'semester': s.get('semester', ''),
                    'subject': subj_name,
                    'category': 'pyqs',
                    'title': p.get('name', ''),
                    'url': url,
                    'file_id': key
                })
            for n in s.get('ppts', []):
                key = n.get('fileKey', '')
                url = f"https://drive.google.com/file/d/{key}/view" if key else ""
                studique_items.append({
                    'source': 'studique',
                    'semester': s.get('semester', ''),
                    'subject': subj_name,
                    'category': 'ppts',
                    'title': n.get('name', ''),
                    'url': url,
                    'file_id': key
                })

    print(f"[Studique] Loaded {len(studique_items)} total resource items")

    all_resources = gradex_items + thehelpers_items + studique_items
    print(f"[Total Scraped Corpus] {len(all_resources)} total resource links across all 3 platforms")
    sys.stdout.flush()

    # 4. Filter for Cycle Tests (CTs) & Folders
    direct_cts = []
    ct_folders = []

    for item in all_resources:
        title = item['title']
        url = item['url']
        drive_id, drive_type = extract_drive_id(url)
        item['drive_id'] = drive_id
        item['drive_type'] = drive_type

        is_ct_title = bool(CT_REGEX.search(title))
        is_folder = (drive_type == 'folder') or ('drive/folders' in url) or ('folders' in url)

        if is_ct_title:
            if is_folder:
                ct_folders.append(item)
            else:
                direct_cts.append(item)
        elif is_folder and any(k in title.lower() for k in ['ct', 'cycle', 'question', 'pyq', 'bank', 'test', 'exam', 'imp']):
            ct_folders.append(item)

    print(f"\n[Filtering Results]")
    print(f"Direct CT paper files found: {len(direct_cts)}")
    print(f"Dedicated CT / Question Folders found: {len(ct_folders)}")
    sys.stdout.flush()

    # 5. Expand CT Google Drive Folders
    print("\n[Folder Unpacking] Scraping nested files from Drive Folders...")
    unpacked_cts = []
    for fld in ct_folders:
        fid = fld.get('drive_id')
        if not fid:
            continue
        print(f"  Unpacking folder: '{fld['title']}' ({fld['subject']}) [ID: {fid}]")
        sys.stdout.flush()
        child_files = scrape_drive_folder(fid)
        print(f"    Found {len(child_files)} files in folder")
        sys.stdout.flush()
        for child in child_files:
            unpacked_cts.append({
                'source': fld['source'] + '+folder',
                'semester': fld['semester'],
                'subject': fld['subject'],
                'category': 'pyqs',
                'title': child['title'],
                'url': child['url'],
                'drive_id': child['file_id'],
                'drive_type': 'file',
                'parent_folder': fld['title'],
                'parent_folder_id': fid
            })

    total_cts = direct_cts + unpacked_cts
    print(f"\n[Success] Raw discovered CT papers & questions: {len(total_cts)} ({len(direct_cts)} direct + {len(unpacked_cts)} from folders)")

    # Deduplicate by drive_id or url
    seen = set()
    deduped_cts = []
    for c in total_cts:
        key = c.get('drive_id') or c.get('url')
        if key and key not in seen:
            seen.add(key)
            deduped_cts.append(c)

    print(f"[Deduplication] Retained {len(deduped_cts)} unique Cycle Test papers across all subjects")

    # Classify CT cycle (CT1, CT2, CT3, Model, Midsem)
    for c in deduped_cts:
        txt = (c['title'] + " " + c.get('parent_folder', '')).lower()
        if 'ct1' in txt or 'ct-1' in txt or 'ct 1' in txt or 'cat1' in txt or 'cat 1' in txt:
            c['cycle'] = 'CT1'
        elif 'ct2' in txt or 'ct-2' in txt or 'ct 2' in txt or 'cat2' in txt or 'cat 2' in txt:
            c['cycle'] = 'CT2'
        elif 'ct3' in txt or 'ct-3' in txt or 'ct 3' in txt or 'cat3' in txt or 'cat 3' in txt:
            c['cycle'] = 'CT3'
        elif 'model' in txt:
            c['cycle'] = 'MODEL'
        elif 'mid' in txt:
            c['cycle'] = 'MIDSEM'
        elif 'key' in txt or 'answer' in txt or 'solution' in txt:
            c['cycle'] = 'ANSWER_KEY'
        elif 'mcq' in txt:
            c['cycle'] = 'MCQ'
        else:
            c['cycle'] = 'CT'

    # Save to data/all_cycle_test_papers.json
    out_path = 'data/all_cycle_test_papers.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(deduped_cts, f, indent=2, ensure_ascii=False)
    print(f"[Saved] CT Catalog written to {out_path}")

    # Summary by subject
    subj_counts = {}
    cycle_counts = {}
    for c in deduped_cts:
        s = c.get('subject') or 'Unknown'
        cyc = c.get('cycle') or 'CT'
        subj_counts[s] = subj_counts.get(s, 0) + 1
        cycle_counts[cyc] = cycle_counts.get(cyc, 0) + 1

    print("\nCT Breakdown by Assessment Cycle:")
    for cyc, cnt in sorted(cycle_counts.items(), key=lambda x: -x[1]):
        print(f"  {cyc}: {cnt} items")

    print("\nCT Papers by Subject (Top 30):")
    for s, cnt in sorted(subj_counts.items(), key=lambda x: -x[1])[:30]:
        print(f"  {s}: {cnt} CT papers/items")
    sys.stdout.flush()

if __name__ == '__main__':
    main()
