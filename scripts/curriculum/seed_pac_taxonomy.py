"""
Additive, idempotent seeder for Course 11: Physical And Analytical Chemistry (21CHC101J).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Chemistry / Chemical Engineering Syllabus (21CHC101J).
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PAC_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Properties of Solutions",
        [
            "Ideal and Non-Ideal Solutions: Raoult's Law and Deviations",
            "Vapor Pressure-Composition and Boiling Point Phase Diagrams",
            "Distillation Techniques: Fractional, Immiscible, and Steam Distillation",
            "Colligative Properties and Molecular Weight Determination",
        ],
    ),
    (
        2,
        "Chemical Equilibrium",
        [
            "Gibbs Free Energy, Chemical Potential, and Reaction Spontaneity",
            "Law of Mass Action and Thermodynamic Equilibrium Constants (Kp, Kc, Kx)",
            "Temperature and Pressure Dependence: Van't Hoff Equation",
            "Le Chatelier's Principle and Dynamic Physical-Chemical Equilibria",
        ],
    ),
    (
        3,
        "Phase Equilibrium",
        [
            "Gibbs Phase Rule: Phases, Components, and Degrees of Freedom",
            "One-Component Systems: Water, CO2, and Sulphur Phase Diagrams",
            "Three-Component Systems and Triangular Phase Diagrams",
            "Nernst Distribution Law and Solute Association/Dissociation",
        ],
    ),
    (
        4,
        "Colloids and Photochemistry",
        [
            "Colloidal Dispersions: Classification, Tyndall Effect, and Brownian Movement",
            "Electrical and Electrokinetic Properties: Zeta Potential and Electrophoresis",
            "Laws of Photochemistry and Quantum Yield",
            "Photochemical Kinetics: Hydrogen-Chlorine and Hydrogen-Bromine Reactions",
        ],
    ),
    (
        5,
        "Instrumental Methods of Analysis",
        [
            "Analytical Measurement Errors, Accuracy, Precision, and Calibration",
            "Molecular Spectroscopy: UV-Vis and Infrared (IR) Spectroscopy",
            "Atomic Absorption Spectroscopy and Optical Instrumentation",
            "Chromatographic Separation Techniques: TLC, GC, and HPLC",
        ],
    ),
]


def seed_pac_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 11 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 11")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 11 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 11")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (11, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in PAC_CANONICAL_TAXONOMY:
        cur.execute(
            "SELECT id FROM units WHERE syllabus_id = ? AND number = ?",
            (syllabus_id, unit_num)
        )
        u_row = cur.fetchone()
        if u_row:
            u_id = u_row[0]
            cur.execute("SELECT name FROM units WHERE id = ?", (u_id,))
            existing_name = cur.fetchone()[0]
            if existing_name == "General Unit" or existing_name != unit_title:
                cur.execute("UPDATE units SET name = ? WHERE id = ?", (unit_title, u_id))
        else:
            cur.execute(
                "INSERT INTO units (syllabus_id, number, name) VALUES (?, ?, ?)",
                (syllabus_id, unit_num, unit_title)
            )
            u_id = cur.lastrowid
            units_created += 1

        for t_name in topic_list:
            cur.execute(
                "SELECT id FROM topics WHERE unit_id = ? AND name = ?",
                (u_id, t_name)
            )
            t_row = cur.fetchone()
            if not t_row:
                cur.execute(
                    "INSERT INTO topics (unit_id, name) VALUES (?, ?)",
                    (u_id, t_name)
                )
                t_id = cur.lastrowid
                topics_created += 1
            else:
                t_id = t_row[0]

            cur.execute("SELECT id FROM concepts WHERE canonical_name = ?", (t_name,))
            c_row = cur.fetchone()
            if not c_row:
                cur.execute(
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Physical And Analytical Chemistry', 'CANONICAL')",
                    (t_name,)
                )
                concepts_created += 1

    conn.commit()

    cur.execute("""
        SELECT count(t.id) 
        FROM topics t 
        JOIN units u ON t.unit_id = u.id 
        WHERE u.syllabus_id = ?
    """, (syllabus_id,))
    total_topics = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM units WHERE syllabus_id = ?", (syllabus_id,))
    total_units = cur.fetchone()[0]

    conn.close()

    return {
        "syllabus_id": syllabus_id,
        "units_created": units_created,
        "topics_created": topics_created,
        "concepts_created": concepts_created,
        "total_units": total_units,
        "total_topics": total_topics,
    }


if __name__ == "__main__":
    res = seed_pac_taxonomy()
    print("Course 11 Taxonomy Seeding Result:", res)
