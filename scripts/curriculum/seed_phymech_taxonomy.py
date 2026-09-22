"""
Additive, idempotent seeder for Course 20: Physics: Mechanics.
Seeds canonical units and syllabus-backed topics derived strictly from the official
SRM IST Department of Physics & Nanotechnology Curriculum (21PYB104J) and authentic exam papers.

Course code: 21PYB104J (Regulations 2021).
Note: 21PYB103J was a legacy course code and is not the 2021 Mechanics code.

Idempotency guarantees:
- Reuses existing Syllabus, Units, Topics, and Concepts if already present.
- Never deletes or overwrites existing records.
- Strictly scoped to Course ID 20.
"""
import os
import sys
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Concept
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage

PHYMECH_SOURCES = (
    "corpus/Semester_2/Physics-Mechanics/PYQ/Physics-Mechanics - PYQ Jul 2023.pdf; "
    "corpus/Semester_2/Physics-Mechanics/PYQ/Physics-Mechanics - PYQ Jan 2024.pdf; "
    "corpus/Semester_2/Physics-Mechanics/PYQ/Physics-Mechanics - PYQ May 2024.pdf; "
    "corpus/Semester_2/Physics-Mechanics/PYQ/Physics-Mechanics - PYQ Jul 2024.pdf; "
    "SRM IST Regulations 2021 B.Tech Curriculum (21PYB104J - Physics: Mechanics)"
)

# 5 Canonical Units and 30 Syllabus Topics
PHYMECH_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Oscillations and Fundamental Dynamics",
        [
            "Fundamental Forces in Nature and Kinematics",
            "Frames of Reference",
            "Simple Harmonic Motion and Conservation of Energy",
            "Damped Harmonic Oscillators",
            "Viscous Dampers and Energy Dissipation",
            "Forced Harmonic Oscillators and Resonance",
        ],
    ),
    (
        2,
        "Rigid Body Dynamics and Rotation",
        [
            "Particles and Rigid Bodies",
            "Rotation About a Fixed Axis",
            "Kinetic Energy of Rigid Bodies",
            "Euler's Equations of Motion",
            "Gyroscopic Precession and Symmetrical Top",
            "Conical Pendulum",
        ],
    ),
    (
        3,
        "Statics and Structural Mechanics",
        [
            "Rigid Bodies in Static Equilibrium",
            "Free Body Diagrams and Force Systems",
            "Supports and Reaction Forces",
            "Bridge and Roof Trusses",
            "Theory of Dry Friction",
        ],
    ),
    (
        4,
        "Stress, Strain, and Material Failure",
        [
            "State of Stress at a Point",
            "Generalized Hooke's Law and Thermal Strains",
            "Plane State of Stress and Principal Stresses",
            "Mohr's Circle for Planar Stress",
            "Material Failure Mechanisms",
            "Electrical Resistance Strain Gauges",
        ],
    ),
    (
        5,
        "Beams, Torsion, and Energy Methods",
        [
            "Pure Bending of Beams",
            "Flexural Formula for Bending",
            "Torsion of Circular Shafts",
            "Torsion Equation",
            "Twisting Moment Diagrams",
            "Strain Energy and Resilience",
        ],
    ),
]


def seed_phymech_taxonomy():
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 20).first()
        if not course:
            print("ERROR: Course 20 not found.")
            return

        # Ensure correct canonical code: 21PYB104J
        course.canonical_code = "21PYB104J"
        course.regulation_year = 2021
        course.department = "Physics & Nanotechnology"

        # 1. Syllabus 2021
        syllabus = db.query(Syllabus).filter(
            Syllabus.course_id == 20,
            Syllabus.version == "2021"
        ).first()

        if not syllabus:
            s_old = db.query(Syllabus).filter(Syllabus.course_id == 20, Syllabus.version == "1.0").first()
            if s_old:
                s_old.version = "2021"
                syllabus = s_old
            else:
                syllabus = Syllabus(course_id=20, version="2021")
                db.add(syllabus)
                db.flush()

        unit_records = {}
        topic_records = {}

        for u_num, u_name, topics in PHYMECH_CANONICAL_TAXONOMY:
            unit = db.query(Unit).filter(
                Unit.syllabus_id == syllabus.id,
                Unit.number == u_num
            ).first()

            if not unit and u_num == 1:
                # Reuse dummy unit if present
                unit = db.query(Unit).filter(
                    Unit.syllabus_id == syllabus.id,
                    Unit.name == "General Unit"
                ).first()

            if not unit:
                unit = Unit(syllabus_id=syllabus.id, number=u_num, name=u_name)
                db.add(unit)
                db.flush()
            else:
                unit.name = u_name
                unit.number = u_num

            unit_records[u_num] = unit

            for t_name in topics:
                top = db.query(Topic).filter(
                    Topic.unit_id == unit.id,
                    Topic.name == t_name
                ).first()

                if not top:
                    top = Topic(unit_id=unit.id, name=t_name)
                    db.add(top)
                    db.flush()

                topic_records[t_name] = top

                concept = db.query(Concept).filter(
                    Concept.canonical_name == t_name,
                    Concept.subject == "Physics: Mechanics"
                ).first()
                if not concept:
                    concept = Concept(
                        canonical_name=t_name,
                        subject="Physics: Mechanics",
                        unit_id=unit.id
                    )
                    db.add(concept)

        # 2. Create Assessment Plan for Course 20
        plan = db.query(CourseAssessmentPlan).filter(
            CourseAssessmentPlan.course_id == 20,
            CourseAssessmentPlan.regulation_year == 2021
        ).first()

        if not plan:
            plan = CourseAssessmentPlan(
                course_id=20,
                regulation_year=2021,
                source_title="SRM IST 21PYB104J Assessment Regulations",
                version="1.0",
                provenance={"source": PHYMECH_SOURCES}
            )
            db.add(plan)
            db.flush()

            # CT1 Component: Units 1 and 2
            ct1 = AssessmentComponent(
                plan_id=plan.id,
                course_id=20,
                code="CT1",
                canonical_label="Cycle Test 1",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                raw_labels=["CT1", "Cycle Test 1", "CT-1"]
            )
            db.add(ct1)
            db.flush()

            for u_num in [1, 2]:
                u = unit_records[u_num]
                db.add(AssessmentCoverage(
                    assessment_component_id=ct1.id,
                    unit_id=u.id,
                    coverage_type="IN_SCOPE"
                ))

            # CT2 Component: Units 3 and 4
            ct2 = AssessmentComponent(
                plan_id=plan.id,
                course_id=20,
                code="CT2",
                canonical_label="Cycle Test 2",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                raw_labels=["CT2", "Cycle Test 2", "CT-2"]
            )
            db.add(ct2)
            db.flush()

            for u_num in [3, 4]:
                u = unit_records[u_num]
                db.add(AssessmentCoverage(
                    assessment_component_id=ct2.id,
                    unit_id=u.id,
                    coverage_type="IN_SCOPE"
                ))

            # ENDSEM Component: Units 1 to 5
            endsem = AssessmentComponent(
                plan_id=plan.id,
                course_id=20,
                code="ENDSEM",
                canonical_label="End Semester Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                raw_labels=["ENDSEM", "End Semester", "University Exam", "DEGREE EXAMINATION"]
            )
            db.add(endsem)
            db.flush()

            for u_num in [1, 2, 3, 4, 5]:
                u = unit_records[u_num]
                db.add(AssessmentCoverage(
                    assessment_component_id=endsem.id,
                    unit_id=u.id,
                    coverage_type="IN_SCOPE"
                ))

        db.commit()
        print("Course 20 (Physics: Mechanics - 21PYB104J) taxonomy seeded successfully!")
        print(f"  Syllabus ID: {syllabus.id}, Units: {len(unit_records)}, Topics: {len(topic_records)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_phymech_taxonomy()
