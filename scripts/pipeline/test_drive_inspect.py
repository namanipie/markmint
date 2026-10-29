import json

with open('data/verified_cycle_test_papers.json', 'r', encoding='utf-8') as f:
    papers = json.load(f)

print(f"Total papers: {len(papers)}")
for idx in range(128, len(papers)):
    p = papers[idx]
    print(f"{idx+1}. [{p.get('cycle')}] {p.get('subject')}: {p.get('title')}")









