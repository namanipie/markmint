"""Add the next, syllabus-backed taxonomy layer without replacing existing data.

The source descriptions deliberately name the repository materials used to
justify each addition.  The script is idempotent: it only creates a unit,
topic, or concept when the same course-scoped record is not already present.
"""

import sys

sys.path.insert(0, ".")

from backend.core.database import SessionLocal
from backend.models.core import Concept, Course, Syllabus, Topic, Unit


CALCULUS_SOURCES = (
    "data/1 Year/MATHS/18MAB101T Calculus & Linear Algebra.pdf; "
    "data/1 Year/MATHS/18MAB102T.pdf (Advanced Calculus and Complex Analysis)"
)
CHEMISTRY_SOURCES = (
    "data/1 Year/CHEMISTRY/Lesson plan.pdf; "
    "data/1 Year/CHEMISTRY/PPTs/Chemistry Unit 1.pdf through "
    "Chemistry Unit 5.pdf"
)


def get_or_create_unit(db, syllabus, number: int, name: str) -> Unit:
    unit = (
        db.query(Unit)
        .filter(Unit.syllabus_id == syllabus.id, Unit.name == name)
        .first()
    )
    if unit:
        return unit
    unit = Unit(syllabus_id=syllabus.id, number=number, name=name)
    db.add(unit)
    db.flush()
    return unit


def add_topics(db, unit: Unit, topic_names: list[str], source: str) -> int:
    added = 0
    existing = {topic.name for topic in unit.topics}
    for name in topic_names:
        if name in existing:
            continue
        topic = Topic(name=name, unit_id=unit.id)
        db.add(topic)
        db.flush()
        concept = Concept(
            canonical_name=name,
            description=(
                f"Course-specific topic from {unit.name}. "
                f"Source evidence: {source}."
            ),
            subject=(
                "Calculus And Linear Algebra"
                if "Calculus" in source or "MATHS" in source
                else "Chemistry"
            ),
            status="CANONICAL",
            unit_id=unit.id,
        )
        db.add(concept)
        existing.add(name)
        added += 1
    return added


def main() -> None:
    db = SessionLocal()
    try:
        calc = db.query(Course).filter(Course.name == "Calculus And Linear Algebra").one()
        chem = db.query(Course).filter(Course.name == "Chemistry").one()
        calc_syllabus = db.query(Syllabus).filter(Syllabus.course_id == calc.id).first()
        chem_syllabus = db.query(Syllabus).filter(Syllabus.course_id == chem.id).first()
        if not calc_syllabus or not chem_syllabus:
            raise RuntimeError("Both course syllabuses are required")

        added_calc = 0
        matrices = (
            db.query(Unit)
            .filter(Unit.syllabus_id == calc_syllabus.id, Unit.name == "Matrices and Linear Algebra")
            .one()
        )
        added_calc += add_topics(
            db,
            matrices,
            ["Cayley-Hamilton Theorem", "Quadratic Forms"],
            CALCULUS_SOURCES,
        )
        multivariable = (
            db.query(Unit)
            .filter(Unit.syllabus_id == calc_syllabus.id, Unit.name == "Functions of Several Variables")
            .one()
        )
        added_calc += add_topics(db, multivariable, ["Extrema and Optimization"], CALCULUS_SOURCES)
        series = (
            db.query(Unit)
            .filter(Unit.syllabus_id == calc_syllabus.id, Unit.name == "Sequence and Series")
            .one()
        )
        added_calc += add_topics(db, series, ["Taylor Series"], CALCULUS_SOURCES)

        vector = get_or_create_unit(db, calc_syllabus, 8, "Vector Calculus")
        added_calc += add_topics(db, vector, ["Vector Calculus"], CALCULUS_SOURCES)
        complex_analysis = get_or_create_unit(db, calc_syllabus, 9, "Complex Analysis")
        added_calc += add_topics(
            db,
            complex_analysis,
            ["Complex Variables and Analytic Functions", "Conformal Mapping", "Residues and Laurent Series"],
            CALCULUS_SOURCES,
        )

        added_chem = 0
        periodic = (
            db.query(Unit)
            .filter(Unit.syllabus_id == chem_syllabus.id, Unit.name == "Periodic Properties")
            .one()
        )
        added_chem += add_topics(
            db,
            periodic,
            [
                "Electron Affinity",
                "Electronegativity",
                "Ionic Radius",
                "Effective Nuclear Charge and Screening",
                "Polarizability and Polarizing Power",
            ],
            CHEMISTRY_SOURCES,
        )

        quantum = get_or_create_unit(db, chem_syllabus, 6, "Quantum and Atomic Structure")
        added_chem += add_topics(
            db,
            quantum,
            ["Quantum Mechanics and Atomic Structure", "Particle in a Box", "Hydrogen Atomic Orbitals"],
            CHEMISTRY_SOURCES,
        )
        molecular = get_or_create_unit(db, chem_syllabus, 7, "Molecular Orbital Theory")
        added_chem += add_topics(
            db,
            molecular,
            ["Molecular Orbital Theory", "Aromaticity and Pi Molecular Orbitals"],
            CHEMISTRY_SOURCES,
        )
        coordination = get_or_create_unit(db, chem_syllabus, 8, "Coordination and Crystal Field Theory")
        added_chem += add_topics(
            db,
            coordination,
            ["Coordination Chemistry", "Crystal Field Theory", "Coordination Isomerism", "Molecular Symmetry"],
            CHEMISTRY_SOURCES,
        )

        spectroscopy = get_or_create_unit(db, chem_syllabus, 9, "Spectroscopy")
        added_chem += add_topics(
            db,
            spectroscopy,
            [
                "Spectroscopy Fundamentals",
                "Electronic and UV-Visible Spectroscopy",
                "Rotational Spectroscopy",
                "Vibrational and Infrared Spectroscopy",
                "Nuclear Magnetic Resonance",
                "Photoelectron Spectroscopy",
            ],
            CHEMISTRY_SOURCES,
        )
        diffraction = get_or_create_unit(db, chem_syllabus, 10, "Solid State and Diffraction")
        added_chem += add_topics(db, diffraction, ["X-ray Diffraction and Crystal Structure"], CHEMISTRY_SOURCES)

        thermodynamics = get_or_create_unit(db, chem_syllabus, 11, "Thermodynamics and Intermolecular Forces")
        added_chem += add_topics(
            db,
            thermodynamics,
            [
                "Chemical Thermodynamics",
                "Hard and Soft Acids and Bases",
                "Intermolecular Forces",
                "Real Gases and Critical Phenomena",
            ],
            CHEMISTRY_SOURCES,
        )
        electrochem = get_or_create_unit(db, chem_syllabus, 12, "Electrochemistry")
        added_chem += add_topics(
            db,
            electrochem,
            ["Electrochemical Cells and Electrode Potentials", "Solubility Equilibria"],
            CHEMISTRY_SOURCES,
        )

        organic = (
            db.query(Unit)
            .filter(Unit.syllabus_id == chem_syllabus.id, Unit.name == "Stereo Chemistry And Organic Reactions")
            .one()
        )
        added_chem += add_topics(
            db,
            organic,
            [
                "Optical Activity and Chirality",
                "Conformational Analysis",
                "Stereochemical Projections",
                "Organic Reagents and Reaction Types",
                "Organic Oxidation and Reduction",
                "Organic Synthesis and Condensation",
            ],
            CHEMISTRY_SOURCES,
        )

        db.commit()
        print(f"ADDED CALCULUS TOPICS: {added_calc}")
        print(f"ADDED CHEMISTRY TOPICS: {added_chem}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
