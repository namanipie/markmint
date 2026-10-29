import json
import os

def_dir = 'backend/services/taxonomy_registry/definitions'
second_year_files = [
    'course_22_prob.json',
    'course_24_dsa.json',
    'course_25_os.json',
    'course_26_coa.json',
    'course_27_daa.json',
    'course_28_dbms.json',
    'course_29_ai.json',
    'course_30_tbvp.json',
    'course_31_pqt.json',
]

def main():
    single_token_guards = {}
    for fname in second_year_files:
        fpath = os.path.join(def_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        course_name = data['course']['name']
        single_token_guards[course_name] = []
        for u in data['units']:
            for t in u['topics']:
                for ng in t.get('negative_guards', []):
                    if len(ng.strip().split()) == 1:
                        single_token_guards[course_name].append((t['name'], ng))

    for cname, guards in single_token_guards.items():
        print(f'=== {cname} ({len(guards)} single-token guards) ===')
        for tname, ng in guards[:10]:
            print(f'   Topic "{tname}": "{ng}"')
        if len(guards) > 10:
            print(f'   ... and {len(guards)-10} more')
        print()

if __name__ == '__main__':
    main()
