import urllib.request
import json

courses = [
    ('Calculus And Linear Algebra', 1),
    ('Chemistry', 2),
    ('Programming For Problem Solving', 5),
    ('Database Management Systems', 28)
]

for name, cid in courses:
    print("=" * 60)
    print(f"COURSE: {name} (ID: {cid})")
    print("=" * 60)
    for cycle in ["ALL", "CT1", "CT2", "ENDSEM"]:
        url = f"http://127.0.0.1:8000/api/analysis/dna?course_id={cid}&assessment_cycle={cycle}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                sample = data.get("sample_size", {})
                cd = data.get("cognitive_demand_distribution", {})
                bp = data.get("assessment_blueprints", [])
                fo = data.get("temporal_unit_focus", [])
                top_fo = data.get("topic_historical_footprints", [])
                temp_uqt = data.get("temporal_unit_question_type_breakdown", [])
                print(f"  Cycle [{cycle}]:")
                print(f"    Papers: {sample.get('papers')}, Qs: {sample.get('questions')}, Sufficiency: {sample.get('sufficiency')}, Years: {sample.get('years')}")
                print(f"    Blueprints: {len(bp) if isinstance(bp, list) else len(bp.get('blueprints', []))} observed structures")
                print(f"    Cognitive Demand: Total={cd.get('total_questions')}, Unclassified={cd.get('unclassified_count')} ({cd.get('unclassified_percentage', 0):.1%}), MarksReliable={cd.get('is_marks_reliable')}")
                print(f"    Focus Evolution: Units={len(fo)}, Topics={len(top_fo)}, Temporal UxQT rows={len(temp_uqt)}")
        except Exception as e:
            print(f"  Cycle [{cycle}]: ERROR: {e}")
