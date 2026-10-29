import json
from extract_all_cts import scrape_drive_folder

with open('data/verified_cycle_test_papers.json', 'r', encoding='utf-8') as f:
    papers = json.load(f)

failed_folders = [p for p in papers if not p.get('local_path') and p.get('drive_id')]
print(f"Failed items (subfolders): {len(failed_folders)}")

for ff in failed_folders:
    fid = ff['drive_id']
    subj = ff['subject']
    title = ff['title']
    print(f"Checking {subj} -> {title} (ID: {fid})")
    children = scrape_drive_folder(fid)
    print(f"  Children found: {len(children)}")
    for ch in children:
        print(f"    [{ch['file_id']}] {ch['title']}")
