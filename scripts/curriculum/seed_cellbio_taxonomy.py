"""
Additive, idempotent seeder for Course 9: Cell Biology (21BTC102J / 21BTB105T).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Biotechnology Syllabus (21BTC102J / 21BTB105T) and course decks.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CELLBIO_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Overview of Cells and Cell Research",
        [
            "Origin, Evolution, and Organization of Prokaryotic and Eukaryotic Cells",
            "Experimental Model Organisms and Microscopy Tools in Cell Biology",
            "Molecular Composition of Cells: Macromolecules and Water",
            "Structure, Composition, and Dynamics of the Plasma Membrane",
        ],
    ),
    (
        2,
        "Cell Structure and Function: Organelles",
        [
            "Nuclear Structure, Nuclear Envelope, and Nucleolus",
            "Endoplasmic Reticulum and Golgi Apparatus in Protein Processing",
            "Lysosomes, Peroxisomes, and Endocytic Sorting",
            "Bioenergetics of Mitochondria and Chloroplasts",
        ],
    ),
    (
        3,
        "Cytoskeleton and Cellular Transport",
        [
            "Actin and Myosin Filaments: Structure and Muscle Contraction",
            "Microtubules, Centrosomes, and Intermediate Filaments",
            "Passive and Active Membrane Transport and Ion Channels",
            "Cell-Cell Interactions: Adhesion, Tight Junctions, and Gap Junctions",
        ],
    ),
    (
        4,
        "Cell Signaling and Transduction Pathways",
        [
            "Principles and Modes of Intercellular Signaling: Autocrine, Paracrine, Endocrine",
            "Cell Surface Receptors and Ligand Binding Mechanisms",
            "G-Protein Coupled Receptor (GPCR) Pathways and Second Messengers",
            "Receptor Tyrosine Kinases and MAPK Signaling Cascades",
        ],
    ),
    (
        5,
        "Cell Regulation, Cancer, and Stem Cells",
        [
            "Cell Cycle Checkpoints, Cyclins, and CDKs",
            "Mechanisms of Mitosis, Meiosis, and Chromosome Segregation",
            "Programmed Cell Death: Apoptosis vs Necrosis Pathways",
            "Molecular Biology of Cancer, Oncogenes, and Stem Cell Therapeutics",
        ],
    ),
]


def seed_cellbio_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 9 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 9")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 9 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 9")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (9, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in CELLBIO_CANONICAL_TAXONOMY:
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Cell Biology', 'CANONICAL')",
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
    res = seed_cellbio_taxonomy()
    print("Course 9 Taxonomy Seeding Result:", res)
