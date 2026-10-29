import json
import re

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

# Map scraped subject names to MarkMint course slugs
SUBJECT_TO_SLUG = {
    'calculus and linear algebra': 'calculus-and-linear-algebra',
    'advanced calculus and complex analysis': 'advanced-calculus-and-complex-analysis',
    'chemistry': 'chemistry',
    'programming for problem solving': 'programming-for-problem-solving',
    'electromagnetic physics': 'electromagnetic-physics',
    'semiconductor physics and computational methods': 'semiconductor-physics-and-computational-methods',
    'data structures and algorithm': 'data-structures-and-algorithms',
    'data structures and algorithms': 'data-structures-and-algorithms',
    'design and analysis of algorithms': 'design-and-analysis-of-algorithms',
    'operating systems': 'operating-systems',
    'database management systems': 'database-management-systems',
    'computer organization and architecture': 'computer-organization-and-architecture',
    'artificial intelligence': 'artificial-intelligence',
    'transforms and boundary value problems': 'transforms-and-boundary-value-problems',
    'electrical and electronics engineering': 'basic-electrical-and-electronics-engineering',
    'basic electrical and electronics engineering': 'basic-electrical-and-electronics-engineering',
    'communicative english': 'communicative-english',
    'machine learning': 'machine-learning',
    'computer networks': 'computer-networks',
    'solid state devices': 'solid-state-devices',
    'electronic system and pcb design': 'electronic-system-and-pcb-design',
    'introduction to computational biology': 'introduction-to-computational-biology',
    'biochemistry': 'biochemistry',
    'philosophy of engineering': 'philosophy-of-engineering',
    'social engineering': 'social-engineering',
    'foreign languages': 'foreign-languages'
}

def main():
    print("==================================================")
    print("MarkMint: Integrating CT Papers into Course Catalog")
    print("==================================================")

    with open('data/verified_cycle_test_papers.json', 'r', encoding='utf-8') as f:
        ct_papers = json.load(f)

    with open('src/lib/course-resources.json', 'r', encoding='utf-8') as f:
        course_catalog = json.load(f)

    total_added = 0
    matched_subjects = set()

    for p in ct_papers:
        subj = p.get('subject', '').strip().lower()
        slug = SUBJECT_TO_SLUG.get(subj) or slugify(subj)

        # Check if course exists in catalog
        course = course_catalog.get(slug)
        if not course:
            # Try fuzzy match
            for cslug, cdata in course_catalog.items():
                if subj in cdata.get('courseName', '').lower() or cdata.get('courseName', '').lower() in subj:
                    course = cdata
                    slug = cslug
                    break

        if not course:
            continue

        matched_subjects.add(course['courseName'])

        # Check if paper already exists in pyqs by url or title
        existing_urls = {q.get('url') for q in course.get('pyqs', [])}
        existing_titles = {q.get('title', '').lower() for q in course.get('pyqs', [])}

        url = p.get('url')
        title = p.get('title')

        if url in existing_urls or title.lower() in existing_titles:
            continue

        # Format into course pyq entry
        cycle = p.get('cycle', 'CT')
        exam_type = cycle if cycle in ['CT1', 'CT2', 'CT3', 'MODEL', 'MIDSEM'] else 'CT'

        # Extract year if in title
        year_m = re.search(r'\b(201[89]|202[0-6])\b', title)
        year = int(year_m.group(1)) if year_m else None

        source_label = "GradeX CT Deck" if 'gradex' in p.get('source', '') else "TheHelper CT Archive"

        new_entry = {
            'title': title,
            'examType': exam_type,
            'year': year,
            'url': url,
            'source': source_label,
            'driveId': p.get('drive_id'),
            'parentFolder': p.get('parent_folder')
        }

        # Place CTs at the top of pyqs list
        course['pyqs'].insert(0, new_entry)
        course['pyqsCount'] = len(course['pyqs'])
        total_added += 1

    print(f"Added {total_added} verified Cycle Test papers into {len(matched_subjects)} courses:")
    for s in sorted(matched_subjects):
        # Find course by name
        c = None
        for cdata in course_catalog.values():
            if cdata.get('courseName') == s:
                c = cdata
                break
        if c:
            ct_count = sum(1 for q in c.get('pyqs', []) if q.get('examType') in ['CT1', 'CT2', 'CT3', 'CT', 'MODEL'])
            print(f"  {s}: {c.get('pyqsCount')} total PYQs ({ct_count} Cycle Tests)")

    with open('src/lib/course-resources.json', 'w', encoding='utf-8') as f:
        json.dump(course_catalog, f, indent=2, ensure_ascii=False)

    print("\nUpdated src/lib/course-resources.json successfully.")


if __name__ == '__main__':
    main()
