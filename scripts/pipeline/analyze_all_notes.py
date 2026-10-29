import json
import re

def normalize(name):
    return re.sub(r'[^a-z0-9]+', ' ', name.lower()).strip()

def main():
    with open('src/lib/course-resources.json', 'r', encoding='utf-8') as f:
        existing = json.load(f)

    with open('thehelpers_complete_catalog_utf8.json', 'r', encoding='utf-8') as f:
        thehelpers = json.load(f)

    with open('data/gradex_catalog_parsed.json', 'r', encoding='utf-8') as f:
        gradex = json.load(f)

    with open('data/studique_resources.json', 'r', encoding='utf-8') as f:
        studique = json.load(f).get('subjects', [])

    print(f"Existing catalog courses: {len(existing)}")
    print(f"TheHelpers subjects: {len(thehelpers)}")
    print(f"GradeX subjects: {len(gradex)}")
    print(f"Studique subjects: {len(studique)}")

    # Total notes count in sources
    th_notes = sum(len(v.get('notes', [])) for v in thehelpers.values())
    gx_ppts = sum(len(v.get('ppts', [])) for v in gradex)
    st_ppts = sum(len(v.get('ppts', [])) for v in studique)

    print(f"\nRaw Source Notes/PPTs:")
    print(f"  TheHelpers Notes: {th_notes}")
    print(f"  GradeX PPTs & Materials: {gx_ppts}")
    print(f"  Studique Unit PPTs: {st_ppts}")
    print(f"  Total Raw Notes Available: {th_notes + gx_ppts + st_ppts}")

if __name__ == '__main__':
    main()
