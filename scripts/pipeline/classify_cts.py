import json
import re

with open('data/all_cycle_test_papers.json', 'r', encoding='utf-8') as f:
    raw_cts = json.load(f)

# Pure notes / slides regex to exclude
exclude_rx = re.compile(r'(?i)\b(lecture\s*\d+|handout|syllabus|curriculum)\b|\.pptx?$')

# CT Exam Papers regex
ct_paper_rx = re.compile(
    r'(?i)\b(ct\s*[1-3]|cycle\s*test\s*[1-3]|cat\s*[1-3]|mid\s*sem|mid\s*term|model|unit\s*test|surprise|ia\s*[1-3]|ct1|ct2|ct3|cat1|cat2|internal\s*test|compilation|answer\s*key|solution|keys?|ans\s*key|pyq|question\s*paper|qp)\b'
)

ct_folders_whitelist = [
    'pyq ct papers', 'ct papers', 'ct papers compilation pyq', 'ct pyqs',
    'ct1 answer keys 2025', 'pyq ct 2024 & 2025', 'ct pyqs ct - 1', 'ct pyqs ct - 2',
    'important questions: cts and sem', 'all university exam pyqs'
]

verified_papers = []

pps_counter = 1

for item in raw_cts:
    title = item.get('title', '').strip()
    parent = (item.get('parent_folder') or '').strip()
    combined = f"{title} {parent}".lower()

    if exclude_rx.search(title):
        continue

    is_ct_folder = any(wf in parent.lower() for wf in ct_folders_whitelist)
    is_ct_title = bool(ct_paper_rx.search(title))

    if is_ct_folder or is_ct_title:
        # Clean up obfuscated Google Drive filenames if any
        if title.startswith('APznza'):
            clean_title = f"PPS CT Compilation Paper Set {pps_counter}.pdf"
            pps_counter += 1
            item['title'] = clean_title
        elif title.startswith('IMG-') or title.startswith('WhatsApp Image'):
            # It is a photographic capture of exam question paper
            item['title'] = f"Exam Paper Capture ({title})"

        # Classify cycle
        t_low = (item['title'] + " " + parent).lower()
        if any(k in t_low for k in ['ct1', 'ct-1', 'ct 1', 'cat1', 'cat 1', 'cycle test 1', 'cycle test - 1', 'cycle test-1']):
            item['cycle'] = 'CT1'
        elif any(k in t_low for k in ['ct2', 'ct-2', 'ct 2', 'cat2', 'cat 2', 'cycle test 2', 'cycle test - 2', 'cycle test-2']):
            item['cycle'] = 'CT2'
        elif any(k in t_low for k in ['ct3', 'ct-3', 'ct 3', 'cat3', 'cat 3', 'cycle test 3', 'cycle test - 3', 'cycle test-3']):
            item['cycle'] = 'CT3'
        elif 'model' in t_low:
            item['cycle'] = 'MODEL'
        elif 'mid' in t_low:
            item['cycle'] = 'MIDSEM'
        elif any(k in t_low for k in ['key', 'answer', 'solution', 'ans key']):
            item['cycle'] = 'ANSWER_KEY'
        elif 'mcq' in t_low:
            item['cycle'] = 'MCQ'
        else:
            item['cycle'] = 'CT'

        verified_papers.append(item)

print(f"Total raw items: {len(raw_cts)}")
print(f"Verified CT Exam Papers retained: {len(verified_papers)}")

# Cycle breakdown
cycle_dist = {}
for p in verified_papers:
    c = p['cycle']
    cycle_dist[c] = cycle_dist.get(c, 0) + 1

print("\nCycle Breakdown:")
for c, cnt in sorted(cycle_dist.items(), key=lambda x: -x[1]):
    print(f"  {c}: {cnt}")

# Subject breakdown
subj_dist = {}
for p in verified_papers:
    s = p.get('subject') or 'Unknown'
    subj_dist[s] = subj_dist.get(s, 0) + 1

print(f"\nSubject Breakdown ({len(subj_dist)} subjects):")
for s, cnt in sorted(subj_dist.items(), key=lambda x: -x[1]):
    print(f"  {s}: {cnt}")

with open('data/verified_cycle_test_papers.json', 'w', encoding='utf-8') as f:
    json.dump(verified_papers, f, indent=2, ensure_ascii=False)
print("\nSaved verified CT papers to data/verified_cycle_test_papers.json")
