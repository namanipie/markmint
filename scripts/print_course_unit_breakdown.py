import json

with open('data/course_unit_synthesis.json') as f:
    courses = json.load(f)

print(f"Total Courses in synthesis: {len(courses)}")

# Key courses to inspect
sample_keys = [
    'SEM1-CALC', 'SEM1-CHEM', 'SEM1-PPS', 'SEM1-ENG', 'SEM1-SPCM', 'SEM1-EEE',
    'SEM2-ACCA', 'SEM2-OODP',
    'SEM3-DSA', 'SEM3-DM', 'SEM3-COA',
    'SEM4-DAA', 'SEM4-OS', 'SEM4-PQT'
]

for c_code in sample_keys:
    if c_code in courses:
        c = courses[c_code]
        print(f"\n=================================================================")
        print(f"Course: {c_code} - {c['name']}")
        print(f"=================================================================")
        print(f"  CT1 ({c['CT1']['papers']} papers):")
        print(f"    Units (Qs)   : {c['CT1']['units']}")
        print(f"    Marks        : {c['CT1']['marks']}")
        print(f"  CT2 ({c['CT2']['papers']} papers):")
        print(f"    Units (Qs)   : {c['CT2']['units']}")
        print(f"    Marks        : {c['CT2']['marks']}")
        print(f"  EndSem ({c['END_SEMESTER']['papers']} papers):")
        print(f"    Units (Qs)   : {c['END_SEMESTER']['units']}")
        print(f"    Marks        : {c['END_SEMESTER']['marks']}")
