import json
from pathlib import Path
from extract_all_cts import scrape_drive_folder
from download_verified_cts import download_drive_file, sanitize_filename

def main():
    with open('data/verified_cycle_test_papers.json', 'r', encoding='utf-8') as f:
        papers = json.load(f)

    failed_folders = [p for p in papers if not p.get('local_path') and p.get('drive_id')]
    print(f"Unpacking & downloading {len(failed_folders)} subfolder collections...")

    base_dir = Path("data/downloads/cycle_tests")
    newly_added = []

    for ff in failed_folders:
        fid = ff['drive_id']
        subj = ff['subject']
        safe_subj = sanitize_filename(subj)
        subj_dir = base_dir / safe_subj
        subj_dir.mkdir(parents=True, exist_ok=True)

        children = scrape_drive_folder(fid)
        print(f"[{subj}] Found {len(children)} child files in '{ff['title']}'")

        for ch in children:
            cid = ch['file_id']
            ctitle = ch['title']
            
            # Skip if it is another nested folder
            if ctitle in ['CT1', 'CT2', 'CT3'] and not ('.' in ctitle):
                # Unpack one more level
                grandchildren = scrape_drive_folder(cid)
                for gc in grandchildren:
                    gid = gc['file_id']
                    gtitle = gc['title']
                    clean_title = sanitize_filename(gtitle)
                    dest = subj_dir / f"{ctitle}_{clean_title}"
                    ok, msg = download_drive_file(gid, dest)
                    print(f"  --> [{ctitle}] {gtitle}: {msg}")
                    newly_added.append({
                        'source': ff['source'] + '+subfolder',
                        'semester': ff.get('semester', ''),
                        'subject': subj,
                        'category': 'pyqs',
                        'title': f"{ctitle} {gtitle}",
                        'url': f"https://drive.google.com/file/d/{gid}/view",
                        'drive_id': gid,
                        'drive_type': 'file',
                        'parent_folder': ff['title'],
                        'cycle': ctitle,
                        'local_path': str(dest).replace('\\', '/'),
                        'file_size_kb': dest.stat().st_size // 1024 if dest.exists() else 0
                    })
                continue

            cycle = ff.get('cycle', 'CT')
            if 'ct1' in ctitle.lower() or 'ct-1' in ctitle.lower():
                cycle = 'CT1'
            elif 'ct2' in ctitle.lower() or 'ct-2' in ctitle.lower():
                cycle = 'CT2'
            elif 'ct3' in ctitle.lower() or 'ct-3' in ctitle.lower():
                cycle = 'CT3'

            clean_title = sanitize_filename(ctitle)
            dest = subj_dir / f"{cycle}_{clean_title}"
            ok, msg = download_drive_file(cid, dest)
            print(f"  --> [{cycle}] {ctitle}: {msg}")

            newly_added.append({
                'source': ff['source'] + '+subfolder',
                'semester': ff.get('semester', ''),
                'subject': subj,
                'category': 'pyqs',
                'title': ctitle,
                'url': f"https://drive.google.com/file/d/{cid}/view",
                'drive_id': cid,
                'drive_type': 'file',
                'parent_folder': ff['title'],
                'cycle': cycle,
                'local_path': str(dest).replace('\\', '/'),
                'file_size_kb': dest.stat().st_size // 1024 if dest.exists() else 0
            })

    print(f"\nSuccessfully unpacked and downloaded {len(newly_added)} child CT papers!")
    
    # Filter out failed subfolder entries from papers and append new file entries
    valid_papers = [p for p in papers if p.get('local_path')] + newly_added
    with open('data/verified_cycle_test_papers.json', 'w', encoding='utf-8') as f:
        json.dump(valid_papers, f, indent=2, ensure_ascii=False)

    print(f"Updated data/verified_cycle_test_papers.json with {len(valid_papers)} total verified files.")

if __name__ == '__main__':
    main()
