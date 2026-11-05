import json
from collections import defaultdict, Counter

with open('data/paper_unit_audit_results.json') as f:
    data = json.load(f)

exams = data['exams']
print(f"Loaded {len(exams)} classified exams.")

# 1. Overall stats by exam category
cat_stats = defaultdict(lambda: {
    'count': 0,
    'total_questions': 0,
    'total_marks': 0,
    'units': Counter(),
    'marks_by_unit': Counter(),
    'courses': set()
})

# Course level stats: course -> exam_category -> list of exams & unit stats
course_cat_map = defaultdict(lambda: defaultdict(list))

for e in exams:
    cat = e['category']
    c_code = e['course_code']
    c_name = e['course_name']
    
    stats = cat_stats[cat]
    stats['count'] += 1
    stats['total_questions'] += e['total_questions']
    stats['total_marks'] += e['total_marks']
    stats['courses'].add(f"{c_code} ({c_name})")
    
    for u_num, u_info in e['units_breakdown'].items():
        u_int = int(u_num)
        stats['units'][u_int] += u_info['question_count']
        stats['marks_by_unit'][u_int] += u_info['marks']
        
    course_cat_map[c_code][cat].append(e)

print("\n=========================================================================")
print("                      CORPUS EXAM SEPARATION SUMMARY                     ")
print("=========================================================================")
for cat, stats in sorted(cat_stats.items(), key=lambda x: -x[1]['count']):
    total_q = stats['total_questions']
    total_m = stats['total_marks']
    avg_q = total_q / stats['count'] if stats['count'] else 0
    avg_m = total_m / stats['count'] if stats['count'] else 0
    print(f"\n--- {cat} ---")
    print(f"  Papers Count       : {stats['count']}")
    print(f"  Distinct Courses   : {len(stats['courses'])}")
    print(f"  Total Questions    : {total_q} (avg {avg_q:.1f} per paper)")
    print(f"  Total Marks Extracted: {total_m:.0f} (avg {avg_m:.1f} per paper)")
    print("  Unit Breakdown (Question distribution & Marks percentage):")
    total_cat_marks = sum(stats['marks_by_unit'].values()) or 1
    total_cat_qs = sum(stats['units'].values()) or 1
    for u in range(1, 6):
        q_cnt = stats['units'].get(u, 0)
        u_marks = stats['marks_by_unit'].get(u, 0)
        q_pct = (q_cnt / total_cat_qs) * 100
        m_pct = (u_marks / total_cat_marks) * 100
        print(f"    Unit {u}: {q_cnt:4d} questions ({q_pct:5.1f}%) | {u_marks:6.0f} marks ({m_pct:5.1f}%)")

# Now let's examine Course by Course unit mapping for CT1, CT2, and EndSem
course_unit_synthesis = {}

for c_code in sorted(course_cat_map.keys()):
    c_exams = course_cat_map[c_code]
    c_name = c_exams[list(c_exams.keys())[0]][0]['course_name']
    
    course_unit_synthesis[c_code] = {
        'name': c_name,
        'CT1': {'papers': len(c_exams.get('CT1', [])), 'units': Counter(), 'marks': Counter()},
        'CT2': {'papers': len(c_exams.get('CT2', [])), 'units': Counter(), 'marks': Counter()},
        'END_SEMESTER': {'papers': len(c_exams.get('END_SEMESTER', [])), 'units': Counter(), 'marks': Counter()},
        'OTHER': {'papers': len(c_exams.get('CT3_OR_FORMATIVE', [])) + len(c_exams.get('MODEL_EXAM', [])) + len(c_exams.get('UNCLASSIFIED', [])), 'units': Counter()}
    }
    
    for cat in ['CT1', 'CT2', 'END_SEMESTER']:
        for e in c_exams.get(cat, []):
            for u_num, u_info in e['units_breakdown'].items():
                u_int = int(u_num)
                course_unit_synthesis[c_code][cat]['units'][u_int] += u_info['question_count']
                course_unit_synthesis[c_code][cat]['marks'][u_int] += u_info['marks']

# Save course unit synthesis
with open('data/course_unit_synthesis.json', 'w') as f:
    # convert Counters to dicts for JSON
    clean_synthesis = {}
    for c_code, data in course_unit_synthesis.items():
        clean_synthesis[c_code] = {
            'name': data['name'],
            'CT1': {'papers': data['CT1']['papers'], 'units': dict(data['CT1']['units']), 'marks': dict(data['CT1']['marks'])},
            'CT2': {'papers': data['CT2']['papers'], 'units': dict(data['CT2']['units']), 'marks': dict(data['CT2']['marks'])},
            'END_SEMESTER': {'papers': data['END_SEMESTER']['papers'], 'units': dict(data['END_SEMESTER']['units']), 'marks': dict(data['END_SEMESTER']['marks'])}
        }
    json.dump(clean_synthesis, f, indent=2)

print("\nWrote detailed course unit synthesis to data/course_unit_synthesis.json")
