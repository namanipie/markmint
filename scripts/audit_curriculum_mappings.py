import sqlite3
from collections import defaultdict, Counter

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

# Get all courses
cur.execute("SELECT id, code, name FROM courses ORDER BY id")
courses = cur.fetchall()

print(f"Total courses: {len(courses)}\n")

# For each course, find distinct document titles and manifest subjects mapped to it
cur.execute('''
    SELECT 
        c.id, c.code, c.name,
        d.id as doc_id, d.title, d.original_url
    FROM courses c
    JOIN exams e ON e.course_id = c.id
    JOIN documents d ON e.document_id = d.id
    GROUP BY c.id, d.id
''')
mappings = cur.fetchall()

course_docs = defaultdict(list)
for cid, ccode, cname, did, dtitle, durl in mappings:
    course_docs[(cid, ccode, cname)].append((did, dtitle))

suspicious_mappings = []

for (cid, ccode, cname), doc_list in sorted(course_docs.items()):
    print(f"=== Course {cid:2d} | {ccode:15s} | {cname} (Docs: {len(doc_list)}) ===")
    sample_titles = [t for _, t in doc_list[:5]]
    for st in sample_titles:
        print(f"    - {st[:80]}")
    
    # Check for possible cross-contamination
    for did, dtitle in doc_list:
        t_low = dtitle.lower()
        if 'chemistry' in cname.lower() and ('physics' in t_low or 'biology' in t_low):
            suspicious_mappings.append((cid, cname, did, dtitle, "Chemistry course has Physics/Biology title"))
        elif 'physics' in cname.lower() and ('chemistry' in t_low or 'biology' in t_low):
            suspicious_mappings.append((cid, cname, did, dtitle, "Physics course has Chemistry/Biology title"))
        elif 'biology' in cname.lower() and ('calculus' in t_low or 'mechanics' in t_low):
            suspicious_mappings.append((cid, cname, did, dtitle, "Biology course has Calculus/Mechanics title"))

print(f"\nPotential suspicious cross-discipline mappings found: {len(suspicious_mappings)}")
for sm in suspicious_mappings:
    print("  Alert:", sm)

# Audit unmapped documents
cur.execute("SELECT id, title, subject, resource_type, original_url FROM documents WHERE processing_status = 'unmapped'")
unmapped_docs = cur.fetchall()
print(f"\nUnmapped documents in DB: {len(unmapped_docs)}")
unmapped_subjects = Counter(d[2] for d in unmapped_docs)
print("Unmapped subjects breakdown:")
for subj, cnt in unmapped_subjects.items():
    print(f"  {subj}: {cnt}")

con.close()
