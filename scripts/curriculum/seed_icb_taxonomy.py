"""
Additive, idempotent seeder for Course 4: Introduction To Computational Biology (21BTB102T).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Biotechnology Syllabus (21BTB102T) and course decks.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

ICB_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Cell and Evolution",
        [
            "Cell Theory and Whittaker's Kingdom Classification",
            "Cell Organelles and Cellular Homeostasis",
            "Cell Division, Replication, and Tissue Differentiation",
            "Stem Cells and Genetic Algorithms in Evolution",
        ],
    ),
    (
        2,
        "Basics in Biochemistry",
        [
            "Biomolecules: Carbohydrates, Lipids, and Proteins",
            "Nucleic Acids, Enzymes, and Hormones",
            "Human Genome Project and Genomics",
            "Sequence Databases and BLAST Search Tool",
        ],
    ),
    (
        3,
        "Structure Biology",
        [
            "Protein Synthesis: Transcription and Translation",
            "Protein Secondary and Tertiary Structure",
            "Structural Databases and Molecular Visualizing Tools",
            "Secondary Structure Prediction Algorithms",
        ],
    ),
    (
        4,
        "Neurobiology",
        [
            "Neuronal Anatomy, Glial Cells, and Brain Organization",
            "Biological Neural Mechanisms and Synaptic Transmission",
            "Artificial Neural Networks and Biological Comparison",
            "Machine Learning and Data Mining in Biology",
        ],
    ),
    (
        5,
        "Immunobiology",
        [
            "Elements of the Immune System and Immune Responses",
            "Active and Passive Immunity and Antibodies",
            "Immunoinformatics and Epitope Prediction",
            "Computational Vaccine Design and Target Discovery",
        ],
    ),
]


def seed_icb_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 4 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 4")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 4 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 4")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (4, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in ICB_CANONICAL_TAXONOMY:
        cur.execute(
            "SELECT id FROM units WHERE syllabus_id = ? AND number = ?",
            (syllabus_id, unit_num)
        )
        u_row = cur.fetchone()
        if u_row:
            u_id = u_row[0]
            cur.execute("SELECT name FROM units WHERE id = ?", (u_id,))
            existing_name = cur.fetchone()[0]
            if existing_name == "General Unit":
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Introduction To Computational Biology', 'CANONICAL')",
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
    res = seed_icb_taxonomy()
    print("Course 4 Taxonomy Seeding Result:", res)
