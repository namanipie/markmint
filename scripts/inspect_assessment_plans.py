import sqlite3
import os
import glob

con = sqlite3.connect("production_corpus.db")
cur = con.cursor()

print("--- Syllabuses Table ---")
cur.execute("SELECT id, course_id, version FROM syllabuses")
for row in cur.fetchall():
    print(row)

print("\n--- Documents with 'syllabus', 'plan', or 'assessment' ---")
cur.execute("""
SELECT id, title, original_url, subject, resource_type 
FROM documents 
WHERE resource_type = 'SYLLABUS' 
   OR lower(title) LIKE '%syllabus%' 
   OR lower(title) LIKE '%plan%' 
   OR lower(title) LIKE '%assessment%'
   OR lower(original_url) LIKE '%syllabus%'
   OR lower(original_url) LIKE '%plan%'
""")
for row in cur.fetchall():
    print(row)

print("\n--- Local filesystem files with 'assessment' or 'plan' or 'syllabus' ---")
for ext in ["*.pdf", "*.docx", "*.doc", "*.txt"]:
    for p in glob.glob(f"data/**/{ext}", recursive=True):
        low = os.path.basename(p).lower()
        if any(w in low for w in ["assessment", "plan", "syllabus", "scheme", "detailed", "test"]):
            print(f"{os.path.getsize(p)} bytes: {p}")
