import json

with open('data/disk_pdf_audit_results.json') as f:
    data = json.load(f)

print('Categories:', data['categories'])
print('\nTop Exam Strings on Paper Headers:')
for k, v in data['top_exam_strings'].items():
    print(f'  {k}: {v}')

# Check some CT papers and what was found on them
ct_papers = [r for r in data['results'] if r['category'] in ['CT1', 'CT2', 'CT3']]
print(f'\nTotal CT papers on disk: {len(ct_papers)}')
for p in ct_papers[:15]:
    print(f"[{p['category']:4}] {p['filename'][:40]:40} | ExamStr: {p['exam_string_on_paper']} | Marks: {p['max_marks']} | Time: {p['duration']}")
