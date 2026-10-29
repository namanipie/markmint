"""
Seeds Course 30 (Transforms and Boundary Value Problems) and Course 31 (Probability and Queueing Theory)
into MarkMint production database.
- Registers canonical courses with codes 21MAB201T and 21MAB204T.
- Seeds 5 canonical units per SRMIST Regulation 2021 syllabus.
- Creates CourseAssessmentPlans with CLA1, CLA2, and ENDSEM components.
- Links branch curriculum mappings to Courses 30 and 31.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, CurriculumMapping
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage

COURSES_DATA = [
    {
        "id": 30,
        "name": "Transforms and Boundary Value Problems",
        "code": "SEM3-TBVP",
        "canonical_code": "21MAB201T",
        "regulation_year": 2021,
        "department": "Mathematics",
        "semester": 3,
        "units": [
            {"number": 1, "name": "Partial Differential Equations"},
            {"number": 2, "name": "Fourier Series"},
            {"number": 3, "name": "Applications of Partial Differential Equations"},
            {"number": 4, "name": "Two Dimensional Heat Equations"},
            {"number": 5, "name": "Fourier Transforms"},
        ],
        "mapping_filter": lambda name: "transforms" in name.lower() and "boundary" in name.lower()
    },
    {
        "id": 31,
        "name": "Probability and Queueing Theory",
        "code": "SEM4-PQT",
        "canonical_code": "21MAB204T",
        "regulation_year": 2021,
        "department": "Mathematics",
        "semester": 4,
        "units": [
            {"number": 1, "name": "Random Variables and Standard Distributions"},
            {"number": 2, "name": "Two-Dimensional Random Variables"},
            {"number": 3, "name": "Random Processes and Markov Chains"},
            {"number": 4, "name": "Queueing Models (Single Server)"},
            {"number": 5, "name": "Advanced Queueing Models (Multi-Server)"},
        ],
        "mapping_filter": lambda name: "probability" in name.lower() and "queueing" in name.lower()
    }
]

def seed_courses():
    db = SessionLocal()
    try:
        for cdata in COURSES_DATA:
            cid = cdata["id"]
            course = db.query(Course).filter(Course.id == cid).first()
            if not course:
                course = db.query(Course).filter(Course.code == cdata["code"]).first()
            if not course:
                course = db.query(Course).filter(Course.canonical_code == cdata["canonical_code"]).first()

            if not course:
                course = Course(
                    id=cid,
                    name=cdata["name"],
                    code=cdata["code"],
                    canonical_code=cdata["canonical_code"],
                    regulation_year=cdata["regulation_year"],
                    department=cdata["department"]
                )
                db.add(course)
                db.flush()
                print(f"[Course Created] ID {course.id}: {course.name} ({course.canonical_code})")
            else:
                course.name = cdata["name"]
                course.code = cdata["code"]
                course.canonical_code = cdata["canonical_code"]
                course.regulation_year = cdata["regulation_year"]
                course.department = cdata["department"]
                db.flush()
                print(f"[Course Updated] ID {course.id}: {course.name} ({course.canonical_code})")

            # Syllabus
            syllabus = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
            if not syllabus:
                syllabus = Syllabus(course_id=course.id, version="2021")
                db.add(syllabus)
                db.flush()
                print(f"  [Syllabus Created] for {course.name}")

            # Units
            unit_map = {}
            for u in cdata["units"]:
                unit = db.query(Unit).filter(
                    Unit.syllabus_id == syllabus.id,
                    Unit.number == u["number"]
                ).first()
                if not unit:
                    unit = Unit(
                        syllabus_id=syllabus.id,
                        number=u["number"],
                        name=u["name"]
                    )
                    db.add(unit)
                    db.flush()
                    print(f"  [Unit Created] Unit {unit.number}: {unit.name} (id={unit.id})")
                else:
                    unit.name = u["name"]
                    db.flush()
                unit_map[unit.number] = unit

            # Course Assessment Plan
            plan = db.query(CourseAssessmentPlan).filter(
                CourseAssessmentPlan.course_id == course.id,
                CourseAssessmentPlan.regulation_year == 2021
            ).first()
            if not plan:
                plan = CourseAssessmentPlan(
                    course_id=course.id,
                    regulation_year=2021,
                    source_title=f"Regulation 2021 {course.name} Assessment Scheme",
                    version="1.0"
                )
                db.add(plan)
                db.flush()

                cla1 = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=course.id,
                    code="CLA1",
                    canonical_label="Continuous Learning Assessment 1",
                    student_label="CLA-1",
                    role="FORMATIVE_TEST",
                    sequence=1,
                    marks=50.0,
                    raw_labels=["CLA1", "CLA-1", "CT1", "Cycle Test 1"]
                )
                cla2 = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=course.id,
                    code="CLA2",
                    canonical_label="Continuous Learning Assessment 2",
                    student_label="CLA-2",
                    role="FORMATIVE_TEST",
                    sequence=2,
                    marks=50.0,
                    raw_labels=["CLA2", "CLA-2", "CT2", "Cycle Test 2"]
                )
                endsem = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=course.id,
                    code="ENDSEM",
                    canonical_label="End Semester Examination",
                    student_label="End Semester",
                    role="SUMMATIVE_EXAM",
                    sequence=3,
                    marks=100.0,
                    raw_labels=["END_SEM", "ENDSEM", "End Semester", "Semester Exam", "DEGREE EXAMINATION"]
                )
                db.add_all([cla1, cla2, endsem])
                db.flush()

                # Coverage
                db.add(AssessmentCoverage(assessment_component_id=cla1.id, unit_id=unit_map[1].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla1.id, unit_id=unit_map[2].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_map[3].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_map[4].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_map[5].id, coverage_type="IN_SCOPE"))
                for unum in range(1, 6):
                    db.add(AssessmentCoverage(assessment_component_id=endsem.id, unit_id=unit_map[unum].id, coverage_type="IN_SCOPE"))
                db.flush()
                print(f"  [Assessment Plan Created] for {course.name}")

            # Link Curriculum Mappings
            mappings = db.query(CurriculumMapping).filter(
                CurriculumMapping.semester == cdata["semester"]
            ).all()
            linked = 0
            for m in mappings:
                if cdata["mapping_filter"](m.subject_name):
                    m.course_id = course.id
                    m.status = "MATCHED"
                    linked += 1
            db.flush()
            print(f"  [Mappings Linked] {linked} branch mappings linked to {course.name}")

        db.commit()
        print("\n[SUCCESS] Seeded Course 30 and Course 31 with full curriculum linking.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_courses()
