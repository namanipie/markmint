import urllib.request
import json

courses = [
    ("Calculus And Linear Algebra", 1),
    ("Chemistry", 2),
    ("Programming For Problem Solving", 5),
    ("Database Management Systems", 28)
]

cycles = ["ALL", "CT1", "CT2", "ENDSEM"]

for name, cid in courses:
    print(f"\n=======================================================")
    print(f"AUDITING COURSE: {name} (ID: {cid})")
    print(f"=======================================================")
    for cycle in cycles:
        url = f"http://127.0.0.1:8000/api/analysis/dna?course_id={cid}&assessment_cycle={cycle}"
        try:
            with urllib.request.urlopen(url) as resp:
                d = json.loads(resp.read().decode('utf-8'))
                ss = d.get("sample_size", {})
                print(f"  Cycle [{cycle}]: papers={ss.get('papers')}, questions={ss.get('questions')}, years={ss.get('years')}, sufficiency={ss.get('sufficiency')}")
                
                # Check units
                units = d.get("units", [])
                print(f"    Units: {len(units)} units")
                
                # Check question types
                qtypes = d.get("question_types", [])
                print(f"    Question Types: {len(qtypes)} types ({[qt['question_type'] for qt in qtypes[:4]]})")
                
                # Check temporal unit x qtype
                temp_uqt = d.get("temporal_unit_question_type_breakdown", [])
                print(f"    Temporal Unit x QType: {len(temp_uqt)} rows")
                
                # Check focus evolution
                u_focus = d.get("temporal_unit_focus", [])
                top_focus = d.get("topic_historical_footprints", [])
                print(f"    Focus: Unit temporal rows={len(u_focus)}, Topic footprints={len(top_focus)}")
                
                # Check blueprints
                bp = d.get("assessment_blueprints", [])
                print(f"    Blueprints: {len(bp)} clusters")
                for idx, c in enumerate(bp[:2]):
                    rep = c.get("representative_blueprint", {})
                    print(f"      - Cluster {idx+1}: {c.get('cluster_signature')} | {c.get('matching_paper_count')} papers ({c.get('years_observed')}) | Sections: {[s.get('section_name') for s in rep.get('sections', [])]}")
                
                # Check cognitive demand
                cd = d.get("cognitive_demand_distribution", {})
                items = cd.get("items", [])
                print(f"    Cognitive Demand: Total={cd.get('total_questions')}, MarksReliable={cd.get('is_marks_reliable')}")
                for it in items:
                    print(f"      - {it.get('demand')}: {it.get('question_count')} Qs ({it.get('percentage'):.1%}), MarksPct={it.get('marks_percentage')}")
                
                # Check marks distribution
                md = d.get("marks_distribution", {})
                buckets = md.get("buckets", [])
                print(f"    Marks Dist: Avg={md.get('avg_marks')}, Unscored={md.get('unscored_question_count')} ({md.get('unscored_percentage', 0):.1%}), Tiers={len(buckets)}")
                
                # Check question patterns
                ps = d.get("pattern_summary", {})
                stems = ps.get("stem_patterns", [])
                reps = ps.get("repetition_breakdown", {})
                top_fams = ps.get("top_recurring_families", [])
                print(f"    Patterns: RepetitionExact={reps.get('exact_repeat_count')}, Stems={len(stems)}, TopFamilies={len(top_fams)}")

        except Exception as e:
            print(f"  Cycle [{cycle}] FAILED: {e}")
