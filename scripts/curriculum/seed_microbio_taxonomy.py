"""
Additive, idempotent seeder for Course 10: Microbiology (21BTC201T / 21BTB103T).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Biotechnology Syllabus (21BTC201T / 21BTB103T).
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

MICROBIO_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Cell: Basic Unit of Life",
        [
            "Cell Structure and Organelles: Organization and Functions",
            "Cell Cycle, Division, and Meiotic Recombination",
            "Cell Differentiation and Stem Cell Biology",
            "Stem Cell Applications and Ethical Considerations",
        ],
    ),
    (
        2,
        "Macromolecules and Metabolism",
        [
            "Carbohydrate Structure, Classification, and Glucose Metabolism",
            "Lipids and Fatty Acid Metabolism",
            "Amino Acids, Protein Architecture, and Enzymes",
            "Nucleic Acids (DNA and RNA) and Photosynthesis",
        ],
    ),
    (
        3,
        "Microbiology in Human Life",
        [
            "Pathogenic Microorganisms: Bacteria and Viruses",
            "Antibiotics and Antibiotic Resistance Mechanisms",
            "Vaccines and Communicable Disease Control Strategies",
            "Environmental and Industrial Microbiology",
        ],
    ),
    (
        4,
        "Basics of Biosensors and Molecular Motors",
        [
            "Biosensors: Components, Transducers, and Principles",
            "Glucose Sensors and Clinical Diagnostic Applications",
            "Linear Molecular Motors: Actin and Myosin Systems",
            "Rotary Molecular Motors: Flagellar Motor and ATPase",
        ],
    ),
    (
        5,
        "Basics of Biomaterial and its Applications",
        [
            "Classification and Characterization of Biomaterials",
            "Biocompatibility and Mechanical Properties of Scaffolds",
            "Biomaterials for Organ Replacement and Medical Devices",
            "Biomimetic Materials in Dental and Bone Applications",
        ],
    ),
]


def seed_microbio_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 10 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 10")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 10 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 10")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (10, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in MICROBIO_CANONICAL_TAXONOMY:
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Microbiology', 'CANONICAL')",
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
    res = seed_microbio_taxonomy()
    print("Course 10 Taxonomy Seeding Result:", res)
