"""
Additive, idempotent seeder for Course 19: Electromagnetic Theory, Quantum Mechanics, Waves and Optics.
Seeds canonical units and syllabus-backed topics derived strictly from the official
SRM IST Department of Physics & Nanotechnology Curriculum (21PYB101J / 18PYB101J) and course decks.

Idempotency guarantees:
- Reuses existing Syllabus, Units, Topics, and Concepts if already present.
- Never deletes or overwrites existing records.
- Strictly scoped to Course ID 19.
"""
import os
import sys
from typing import List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Concept, Exam
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage

EMPHY_SOURCES = (
    "corpus/Semester_2/Electromagnetic Physics/LAB/Electromagnetic Physics - Lab Manual.pdf; "
    "corpus/Semester_1/Electromagnetic Theory, Quantum Mechanics, Waves and Optics/STUDY_MATERIAL/Unit 1..5.pdf; "
    "SRM IST B.Tech Regulations 2021 Volume-2 First Year Syllabi Control Copy (21PYB101J)"
)

# 5 Canonical Units and 33 Syllabus Topics
EMPHY_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Electromagnetism and Dielectrics",
        [
            "Vector Calculus and Del Operator",
            "Electrostatics and Charge Distributions",
            "Gauss's Law and Electrostatic Potentials",
            "Electrodynamics and Magnetism",
            "Maxwell's Equations and EM Waves",
            "Dielectric Materials and Polarization",
        ],
    ),
    (
        2,
        "Magnetic Materials",
        [
            "Magnetic Properties and Parameters",
            "Ferromagnetism and Domain Theory",
            "Soft and Hard Magnetic Materials",
            "Ferrites and Spinel Structures",
            "Spintronics and Magnetoresistance",
            "Multiferroic Materials",
        ],
    ),
    (
        3,
        "Quantum Mechanics",
        [
            "Inadequacies of Classical Mechanics and Blackbody Radiation",
            "Photoelectric and Compton Effects",
            "Matter Waves and Uncertainty Principle",
            "Wave Function and Postulates",
            "Schrödinger Wave Equations",
            "Quantum Wells and Potential Barriers",
            "Harmonic Oscillator and Hydrogen Atom",
        ],
    ),
    (
        4,
        "Wave Optics",
        [
            "Superposition and Interference of Light",
            "Fresnel and Fraunhofer Diffraction",
            "Fraunhofer Slit Diffraction",
            "Plane Diffraction Grating",
            "Polarization of Light",
            "Double Refraction and Polarizing Devices",
        ],
    ),
    (
        5,
        "Lasers and Fiber Optics",
        [
            "Laser Principles and Einstein Coefficients",
            "Population Inversion and Pumping Schemes",
            "Gas and Solid State Lasers",
            "Semiconductor Diode Lasers",
            "Optical Fiber Transmission",
            "Fiber Classification and Losses",
            "Fiber Optic Communication and Sensors",
        ],
    ),
]


def seed_emphy_taxonomy():
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == 19).first()
        if not course:
            print("ERROR: Course 19 not found.")
            return

        course.canonical_code = "21PYB101J"
        course.regulation_year = 2021
        course.department = "Physics & Nanotechnology"

        # 1. Syllabus 2021 (Current)
        syllabus_2021 = db.query(Syllabus).filter(
            Syllabus.course_id == 19,
            Syllabus.version == "2021"
        ).first()

        # If existing syllabus has version 1.0, update to 2021
        if not syllabus_2021:
            s_old = db.query(Syllabus).filter(Syllabus.course_id == 19, Syllabus.version == "1.0").first()
            if s_old:
                s_old.version = "2021"
                syllabus_2021 = s_old
            else:
                syllabus_2021 = Syllabus(course_id=19, version="2021")
                db.add(syllabus_2021)
                db.flush()

        # 2. Syllabus 2018 (Legacy)
        syllabus_2018 = db.query(Syllabus).filter(
            Syllabus.course_id == 19,
            Syllabus.version == "2018"
        ).first()
        if not syllabus_2018:
            syllabus_2018 = Syllabus(course_id=19, version="2018")
            db.add(syllabus_2018)
            db.flush()

        unit_records = {}
        topic_records = {}

        for u_num, u_name, topics in EMPHY_CANONICAL_TAXONOMY:
            unit = db.query(Unit).filter(
                Unit.syllabus_id == syllabus_2021.id,
                Unit.number == u_num
            ).first()

            if not unit and u_num == 1:
                # Reuse dummy unit if present
                unit = db.query(Unit).filter(
                    Unit.syllabus_id == syllabus_2021.id,
                    Unit.name == "General Unit"
                ).first()

            if not unit:
                unit = Unit(syllabus_id=syllabus_2021.id, number=u_num, name=u_name)
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

                # Canonical Concept
                concept = db.query(Concept).filter(
                    Concept.canonical_name == t_name,
                    Concept.subject == "Electromagnetic Theory, Quantum Mechanics, Waves and Optics"
                ).first()
                if not concept:
                    concept = Concept(
                        canonical_name=t_name,
                        subject="Electromagnetic Theory, Quantum Mechanics, Waves and Optics",
                        unit_id=unit.id
                    )
                    db.add(concept)

        # 3. Create Assessment Plan for Course 19
        plan = db.query(CourseAssessmentPlan).filter(
            CourseAssessmentPlan.course_id == 19,
            CourseAssessmentPlan.regulation_year == 2021
        ).first()

        if not plan:
            plan = CourseAssessmentPlan(
                course_id=19,
                regulation_year=2021,
                source_title="SRM IST 21PYB101J Assessment Regulations",
                version="1.0",
                provenance={"source": EMPHY_SOURCES}
            )
            db.add(plan)
            db.flush()

            # CT1 Component
            ct1 = AssessmentComponent(
                plan_id=plan.id,
                course_id=19,
                code="CT1",
                canonical_label="Cycle Test 1",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                raw_labels=["CT1", "Cycle Test 1", "CT-1"]
            )
            db.add(ct1)
            db.flush()

            # CT1 Scope: Units 1 and 2
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
                course_id=19,
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
                course_id=19,
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
        print("Course 19 (Electromagnetic Physics) taxonomy and assessment plan seeded successfully!")
        print(f"  Syllabus 2021 ID: {syllabus_2021.id}, Units: {len(unit_records)}, Topics: {len(topic_records)}")
        print(f"  Syllabus 2018 ID: {syllabus_2018.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_emphy_taxonomy()
