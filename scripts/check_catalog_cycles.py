import json

with open('src/lib/courses-catalog.json', encoding='utf-8') as f:
    catalog = json.load(f)

print(f"Total catalog courses: {len(catalog)}")
for c in catalog[:6]:
    code = c.get('code')
    name = c.get('name')
    cycles = c.get('assessmentCycles', [])
    print(f"{code} - {name}:")
    for cy in cycles:
        print(f"  {cy.get('id')}: {cy.get('name')} | Units: {cy.get('units')}")
