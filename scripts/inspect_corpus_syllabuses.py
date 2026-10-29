import sqlite3

c = sqlite3.connect("production_corpus.db")

print("=" * 80)
print("SYLLABUS DOCUMENTS IN DATABASE:")
print("=" * 80)
rows = c.execute("SELECT id, title, subject, semester, original_url FROM documents WHERE resource_type = 'SYLLABUS'").fetchall()
for r in rows:
    print(r)

print("\n" + "=" * 80)
print("DOCUMENTS GROUPED BY SUBJECT FOR ALL NON-EXAM TYPES:")
print("=" * 80)
non_exam_rows = c.execute("""
    SELECT subject, resource_type, count(*), group_concat(title, ' | ')
    FROM documents 
    WHERE resource_type IN ('SYLLABUS', 'STUDY_MATERIAL', 'lecture notes', 'question banks', 'important questions')
    GROUP BY subject, resource_type
    ORDER BY subject, resource_type
""").fetchall()

for r in non_exam_rows:
    titles_summary = (r[3][:100] + '...') if r[3] and len(r[3]) > 100 else r[3]
    print(f"[{r[0]}] {r[1]}: {r[2]} docs -> {titles_summary}")
