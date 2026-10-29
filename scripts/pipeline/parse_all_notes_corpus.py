import json
import csv
import base64
import re
from pathlib import Path

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
    # Check "unit 1", "unit-1", "unit 01", "u1"
    m_unit = re.search(r'\b(?:unit|chapter|module|ch|u)[\s\-_:]*([1-5])\b', t)
    if m_unit:
        return int(m_unit.group(1))
    
    # Check roman numerals
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

def normalize_subject_name(name: str) -> str:
    n = re.sub(r'[^a-z0-9]+', ' ', name.lower()).strip()
    # common contractions
    n = re.sub(r'\band\b', '', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def main():
    print("=== Step 1: Loading all note sources ===")

    # 1. Load existing course resources
    with open('src/lib/course-resources.json', 'r', encoding='utf-8') as f:
        existing_catalog = json.load(f)

    # 2. Load TheHelpers
    with open('thehelpers_complete_catalog_utf8.json', 'r', encoding='utf-8') as f:
        thehelpers = json.load(f)

    # 3. Load Studique
    with open('data/studique_resources.json', 'r', encoding='utf-8') as f:
        studique_data = json.load(f).get('subjects', [])

    # 4. Load GradeX CSV
    gradex_subjects = []
    with open('data/gradex_subdeck_resources.csv', 'r', encoding='utf-8') as f:
        raw_lines = []
        for line in f:
            l = line.strip()
            if l.startswith('"') and l.endswith('"'):
                l = l[1:-1]
            raw_lines.append(l)
        
        reader = csv.reader(raw_lines)
        try:
            header = next(reader)
            for row in reader:
                if len(row) >= 3:
                    gradex_subjects.append({
                        'semester': row[0],
                        'subject': row[1],
                        'ppts_raw': row[2] if len(row) > 2 else '',
                        'syllabus_raw': row[4] if len(row) > 4 else ''
                    })
        except Exception as e:
            print("CSV parse error:", e)

    print(f"Loaded: {len(existing_catalog)} catalog courses, {len(thehelpers)} TheHelpers, {len(studique_data)} Studique, {len(gradex_subjects)} GradeX subjects")

    # Group notes by normalized subject
    all_raw_notes_by_subject = {}

    def add_note(subj: str, title: str, url: str, source: str):
        if not subj or not url or not title:
            return
        drive_id = extract_drive_id(url)
        unit = detect_unit(title)
        
        s_norm = normalize_subject_name(subj)
        if s_norm not in all_raw_notes_by_subject:
            all_raw_notes_by_subject[s_norm] = {
                'raw_name': subj,
                'notes_by_drive_id': {},
                'syllabus_url': None
            }
        
        entry = {
            'title': title.strip(),
            'unit': unit,
            'url': url.strip(),
            'source': source,
            'drive_id': drive_id
        }
        
        # Deduplicate by drive_id
        if drive_id and drive_id in all_raw_notes_by_subject[s_norm]['notes_by_drive_id']:
            existing = all_raw_notes_by_subject[s_norm]['notes_by_drive_id'][drive_id]
            if len(entry['title']) > len(existing['title']):
                existing['title'] = entry['title']
            if entry['unit'] and not existing['unit']:
                existing['unit'] = entry['unit']
            if source not in existing['source']:
                existing['source'] = f"{existing['source']}, {source}"
        else:
            all_raw_notes_by_subject[s_norm]['notes_by_drive_id'][drive_id or url] = entry

    # Ingest TheHelpers notes
    for subj_name, data in thehelpers.items():
        notes = data.get('notes', [])
        for n in notes:
            name = n.get('name') or n.get('title')
            url = n.get('url')
            add_note(subj_name, name, url, "TheHelper")

    # Ingest Studique PPTs
    for sub in studique_data:
        subj_name = sub.get('name')
        ppts = sub.get('ppts', [])
        for p in ppts:
            name = p.get('name') or "Lecture Presentation"
            file_key = p.get('fileKey')
            if file_key:
                url = f"https://drive.google.com/file/d/{file_key}/view?usp=sharing"
                add_note(subj_name, f"{name} (Professor Slides)", url, "Studique")

    # Ingest GradeX PPTs & Materials
    for sub in gradex_subjects:
        subj_name = sub['subject']
        ppts_str = sub['ppts_raw']
        if ppts_str:
            entries = [e.strip() for e in ppts_str.split(',') if '|' in e]
            for ent in entries:
                parts = ent.split('|', 1)
                if len(parts) == 2:
                    raw_title, raw_url = parts[0], parts[1]
                    dec_url = decode_gradex_url(raw_url)
                    add_note(subj_name, raw_title, dec_url, "GradeX")

    total_gathered_notes = sum(len(v['notes_by_drive_id']) for v in all_raw_notes_by_subject.values())
    print(f"\nGathered {total_gathered_notes} unique deduplicated notes across {len(all_raw_notes_by_subject)} subject groups")

    # === Step 2: Map to existing course catalog ===
    matched_count = 0
    updated_catalog = {}

    for slug, course_obj in existing_catalog.items():
        c_name = course_obj.get('courseName', '')
        c_code = course_obj.get('courseCode', '')
        c_norm = normalize_subject_name(c_name)
        c_slug_norm = normalize_subject_name(slug)

        # Retain existing notes
        existing_notes_map = {}
        for n in course_obj.get('notes', []):
            d_id = extract_drive_id(n.get('url', ''))
            existing_notes_map[d_id or n.get('url')] = n

        # Find best matching subject in all_raw_notes_by_subject
        matched_notes = []
        best_subj_group = None
        for s_norm, s_data in all_raw_notes_by_subject.items():
            # Exact match or strong substring match
            if s_norm == c_norm or s_norm == c_slug_norm or (len(s_norm) > 4 and s_norm in c_norm) or (len(c_norm) > 4 and c_norm in s_norm):
                best_subj_group = s_data
                break
        
        # If still not found, check partial words
        if not best_subj_group:
            c_words = set(w for w in c_norm.split() if len(w) > 3)
            for s_norm, s_data in all_raw_notes_by_subject.items():
                s_words = set(w for w in s_norm.split() if len(w) > 3)
                if c_words and s_words and len(c_words.intersection(s_words)) >= min(len(c_words), len(s_words)):
                    best_subj_group = s_data
                    break

        if best_subj_group:
            for d_id, note_entry in best_subj_group['notes_by_drive_id'].items():
                if d_id not in existing_notes_map:
                    existing_notes_map[d_id] = {
                        'title': note_entry['title'],
                        'unit': note_entry['unit'],
                        'url': note_entry['url'],
                        'source': note_entry['source']
                    }
            matched_count += 1

        # Re-sort all notes: Unit 1, Unit 2, Unit 3, Unit 4, Unit 5, then others
        all_notes = list(existing_notes_map.values())
        all_notes.sort(key=lambda x: (x.get('unit') is None, x.get('unit') or 99, x.get('title', '')))

        course_obj['notes'] = all_notes
        course_obj['notesCount'] = len(all_notes)
        updated_catalog[slug] = course_obj

    print(f"\nMatched and enriched {matched_count} courses in course-resources.json")
    new_total_notes = sum(len(c.get('notes', [])) for c in updated_catalog.values())
    print(f"Total notes in course-resources.json before: {sum(len(c.get('notes', [])) for c in existing_catalog.values())}")
    print(f"Total notes in course-resources.json after:  {new_total_notes}")

    # Also check if we can add any missing core subjects from Studique/GradeX into the catalog
    with open('src/lib/course-resources.json', 'w', encoding='utf-8') as f:
        json.dump(updated_catalog, f, indent=2)

    print("Saved updated course-resources.json successfully!")

if __name__ == '__main__':
    main()
