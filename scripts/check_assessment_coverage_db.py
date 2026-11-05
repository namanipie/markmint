import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
from backend.models.core import Course, Unit
from collections import defaultdict

db = SessionLocal()

print("--- CHECKING REGISTERED ASSESSMENT COVERAGES IN DATABASE ---")
plans = db.query(CourseAssessmentPlan).all()
print(f"Total assessment plans: {len(plans)}")

components = db.query(AssessmentComponent).all()
print(f"Total components: {len(components)}")

comp_by_code = defaultdict(list)
for c in components:
    comp_by_code[c.code].append(c)

print(f"Components by code:")
for code, comps in comp_by_code.items():
    print(f"  {code}: {len(comps)} components")

# Check sample coverage for CT1, CT2, and ENDSEM
for sample_code in ['CT1', 'CT2', 'ENDSEM']:
    comps = comp_by_code.get(sample_code, [])
    if comps:
        sample_comp = comps[0]
        coverages = db.query(AssessmentCoverage).filter(AssessmentCoverage.assessment_component_id == sample_comp.id).all()
        unit_nums = []
        for cov in coverages:
            if cov.unit:
                unit_nums.append(cov.unit.number)
        print(f"Sample {sample_code} (Plan {sample_comp.plan_id}, Course {sample_comp.course.code if sample_comp.course else '?'}):")
        print(f"  Units In-Scope: {sorted(list(set(unit_nums)))}")

db.close()
