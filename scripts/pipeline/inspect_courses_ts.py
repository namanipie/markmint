import re

with open('src/lib/courses.ts', 'r', encoding='utf-8') as f:
    text = f.read()

courses = []
blocks = text.split('{')
for b in blocks:
    if 'id:' in b and 'name:' in b and 'slug:' in b:
        id_m = re.search(r'id:\s*(\d+)', b)
        name_m = re.search(r'name:\s*"([^"]+)"', b)
        slug_m = re.search(r'slug:\s*"([^"]+)"', b)
        code_m = re.search(r'code:\s*"([^"]+)"', b)
        sem_m = re.search(r'semester:\s*(\d+)', b)
        if id_m and name_m and slug_m:
            courses.append({
                'id': int(id_m.group(1)),
                'name': name_m.group(1),
                'slug': slug_m.group(1),
                'code': code_m.group(1) if code_m else '',
                'semester': int(sem_m.group(1)) if sem_m else 1
            })

print(f"Total courses in courses.ts: {len(courses)}")
for c in courses[:15]:
    print(f"  [{c['id']}] {c['name']} (Sem {c['semester']}) -> slug: {c['slug']}")
