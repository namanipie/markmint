import json

with open('src/lib/courses-catalog.json', 'r', encoding='utf-8') as f:
    courses = json.load(f)

for c in sorted(courses, key=lambda x: (x.get('semester', 1), x.get('id', 0))):
    print(f"Sem {c.get('semester', 1)} | id={c.get('id')}: {c.get('name')} [{c.get('code')}] -> {c.get('slug')}")
