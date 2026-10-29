import urllib.request, json

url_desc = 'http://127.0.0.1:8000/api/practice/cycle-tests/Operating%20Systems?category=descriptive&limit=5'
res_desc = json.loads(urllib.request.urlopen(url_desc).read())
print('DESCRIPTIVE RESULT:')
print('  Total available:', res_desc['total_available'])
print('  Total descriptive:', res_desc['total_descriptive'])
print('  Total mcqs:', res_desc['total_mcqs'])
print('  Category:', res_desc['category'])
for q in res_desc['questions'][:3]:
    txt = q.get('question_text', '')[:60].replace('\n', ' ')
    print(f"   Q{q['q_num']} ({q['marks']}M, is_mcq={q.get('is_mcq')}): {txt}...")

url_mcq = 'http://127.0.0.1:8000/api/practice/cycle-tests/Operating%20Systems?category=mcq&limit=5'
res_mcq = json.loads(urllib.request.urlopen(url_mcq).read())
print('\nMCQ RESULT:')
print('  Total available:', res_mcq['total_available'])
print('  Category:', res_mcq['category'])
for q in res_mcq['questions'][:3]:
    txt = q.get('question_text', '')[:60].replace('\n', ' ')
    print(f"   Q{q['q_num']} ({q['marks']}M, is_mcq={q.get('is_mcq')}): {txt}...")
