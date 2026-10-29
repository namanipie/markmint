import json
import csv
import base64
import re

def decode_gradex_url(url: str) -> str:
    if not url:
        return ""
    m = re.search(r'action=open&r=([a-zA-Z0-9_\-]+)\.?([a-f0-9]*)', url)
    if not m:
        return url
    b64_str = m.group(1)
    padding = len(b64_str) % 4
    if padding:
        b64_str += '=' * (4 - padding)
    try:
        decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
        return decoded
    except Exception:
        return url

def extract_drive_id(url: str) -> str:
    if not url:
        return ""
    m = re.search(r'([a-zA-Z0-9_\-]{25,})', url)
    return m.group(1) if m else url

def detect_unit(title: str) -> int | None:
    t = title.lower()
    m_unit = re.search(r'\b(?:unit|chapter|module|ch|u)[\s\-_:]*([1-5])\b', t)
    if m_unit:
        return int(m_unit.group(1))
    if re.search(r'\b(?:unit|chapter|module)[\s\-_:]*i\b', t):
        return 1
    if re.search(r'\b(?:unit|chapter|module)[\s\-_:]*ii\b', t):
        return 2
    if re.search(r'\b(?:unit|chapter|module)[\s\-_:]*iii\b', t):
        return 3
    if re.search(r'\b(?:unit|chapter|module)[\s\-_:]*iv\b', t):
        return 4
    if re.search(r'\b(?:unit|chapter|module)[\s\-_:]*v\b', t):
        return 5
    return None

def normalize(s: str) -> str:
    n = re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
    for drop in ['and', 'of', 'in', 'the', 'built', 'environment', 'computational', 'methods', 'quantum', 'mechanics', 'waves', 'optics']:
        n = re.sub(rf'\b{drop}\b', '', n)
    return re.sub(r'\s+', ' ', n).strip()

def match_score(name1: str, name2: str) -> float:
    n1 = normalize(name1)
    n2 = normalize(name2)
    if n1 == n2:
        return 1.0
    if n1 in n2 or n2 in n1:
        return 0.9
    w1 = set(w for w in n1.split() if len(w) > 2)
    w2 = set(w for w in n2.split() if len(w) > 2)
    if not w1 or not w2:
        return 0.0
    inter = w1.intersection(w2)
    return len(inter) / max(len(w1), len(w2))

def main():
    with open('src/lib/courses-catalog.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    with open('src/lib/course-resources.json', 'r', encoding='utf-8') as f:
        course_resources = json.load(f)

    with open('thehelpers_complete_catalog_utf8.json', 'r', encoding='utf-8') as f:
        thehelpers = json.load(f)

    with open('data/studique_resources.json', 'r', encoding='utf-8') as f:
        studique = json.load(f).get('subjects', [])

    gradex = []
    with open('data/gradex_subdeck_resources.csv', 'r', encoding='utf-8') as f:
        raw_lines = [l.strip()[1:-1] if l.strip().startswith('"') and l.strip().endswith('"') else l.strip() for l in f]
        reader = csv.reader(raw_lines)
        next(reader, None)
        for row in reader:
            if len(row) >= 3:
                gradex.append({'subject': row[1], 'ppts_raw': row[2], 'syllabus_raw': row[4] if len(row) > 4 else ''})

    updated_resources = {}

    for c in catalog:
        c_slug = c['slug']
        c_name = c['name']
        c_code = c.get('code', '')
        c_sem = c.get('semester', 1)

        existing_group = course_resources.get(c_slug, {
            'courseId': c['id'],
            'courseName': c_name,
            'courseCode': c_code,
            'semester': c_sem,
            'syllabusUrl': None,
            'pyqsCount': 0,
            'notesCount': 0,
            'pyqs': [],
            'notes': []
        })

        # Preserve existing pyqs and syllabusUrl
        pyqs = existing_group.get('pyqs', [])
        syllabus_url = existing_group.get('syllabusUrl')

        notes_dict = {}

        # 1. Existing notes in course-resources.json
        for n in existing_group.get('notes', []):
            d_id = extract_drive_id(n.get('url', ''))
            notes_dict[d_id or n.get('url')] = {
                'title': n.get('title'),
                'unit': n.get('unit'),
                'url': n.get('url'),
                'source': n.get('source', 'MarkMint Verified')
            }

        # 2. Check TheHelpers
        for th_name, th_data in thehelpers.items():
            if match_score(c_name, th_name) >= 0.6:
                for n in th_data.get('notes', []):
                    title = n.get('name') or n.get('title')
                    url = n.get('url')
                    if title and url:
                        d_id = extract_drive_id(url)
                        unit = detect_unit(title)
                        if d_id not in notes_dict:
                            notes_dict[d_id or url] = {
                                'title': title,
                                'unit': unit,
                                'url': url,
                                'source': 'TheHelper'
                            }
                        else:
                            if 'TheHelper' not in notes_dict[d_id]['source']:
                                notes_dict[d_id]['source'] += ', TheHelper'
                            if unit and not notes_dict[d_id]['unit']:
                                notes_dict[d_id]['unit'] = unit

        # 3. Check Studique
        for st in studique:
            st_name = st.get('name', '')
            if match_score(c_name, st_name) >= 0.6:
                for p in st.get('ppts', []):
                    title = p.get('name') or "Lecture Presentation"
                    file_key = p.get('fileKey')
                    if file_key:
                        url = f"https://drive.google.com/file/d/{file_key}/view?usp=sharing"
                        unit = detect_unit(title)
                        if not unit and 'unit' in title.lower():
                            m = re.search(r'([1-5])', title)
                            if m: unit = int(m.group(1))
                        clean_title = f"{title}: Faculty Lecture Presentation" if "unit" in title.lower() else title
                        if file_key not in notes_dict:
                            notes_dict[file_key] = {
                                'title': clean_title,
                                'unit': unit,
                                'url': url,
                                'source': 'Studique'
                            }
                        else:
                            if 'Studique' not in notes_dict[file_key]['source']:
                                notes_dict[file_key]['source'] += ', Studique'
                            if unit and not notes_dict[file_key]['unit']:
                                notes_dict[file_key]['unit'] = unit

        # 4. Check GradeX
        for gx in gradex:
            gx_name = gx['subject']
            if match_score(c_name, gx_name) >= 0.6:
                ppts_str = gx['ppts_raw']
                if ppts_str:
                    entries = [e.strip() for e in ppts_str.split(',') if '|' in e]
                    for ent in entries:
                        parts = ent.split('|', 1)
                        if len(parts) == 2:
                            title, raw_url = parts[0], parts[1]
                            dec_url = decode_gradex_url(raw_url)
                            d_id = extract_drive_id(dec_url)
                            unit = detect_unit(title)
                            if d_id in notes_dict:
                                if 'GradeX' not in notes_dict[d_id]['source']:
                                    notes_dict[d_id]['source'] += ', GradeX'
                                if unit and not notes_dict[d_id]['unit']:
                                    notes_dict[d_id]['unit'] = unit
                            else:
                                notes_dict[d_id or dec_url] = {
                                    'title': title,
                                    'unit': unit,
                                    'url': dec_url,
                                    'source': 'GradeX'
                                }

        notes_list = list(notes_dict.values())
        # Sort notes by unit 1..5, then others
        notes_list.sort(key=lambda x: (x['unit'] is None, x['unit'] or 99, x['title']))

        existing_group['notes'] = notes_list
        existing_group['notesCount'] = len(notes_list)
        existing_group['pyqsCount'] = len(pyqs)

        updated_resources[c_slug] = existing_group

    total_notes = sum(c['notesCount'] for c in updated_resources.values())
    total_pyqs = sum(c['pyqsCount'] for c in updated_resources.values())

    with open('src/lib/course-resources.json', 'w', encoding='utf-8') as f:
        json.dump(updated_resources, f, indent=2)

    print(f"SUCCESS: Ingested {total_notes} notes & lecture presentations and {total_pyqs} PYQs across {len(updated_resources)} courses in src/lib/course-resources.json")

if __name__ == '__main__':
    main()
