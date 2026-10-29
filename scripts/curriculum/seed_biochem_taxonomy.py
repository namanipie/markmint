"""
Additive, idempotent seeder for Course 12: Biochemistry (21BTC101T).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Biotechnology Syllabus (21BTC101T).
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

BIOCHEM_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Introduction to Biochemistry",
        [
            "Chemical Bonds, pH, Buffers, and Water in Biological Systems",
            "Carbohydrate Architecture: Monosaccharides, Polysaccharides, and Glycoproteins",
            "Amino Acids and Protein Organization: Primary to Quaternary Structure",
            "Lipids, Biological Membranes, and Nucleic Acid Structure",
        ],
    ),
    (
        2,
        "Introduction to Metabolism, Bioenergetics and Photosynthesis",
        [
            "Bioenergetics, High Energy Compounds, and Thermodynamics of Metabolism",
            "Mitochondrial Electron Transport Chain and Complexes",
            "Oxidative Phosphorylation, Chemiosmotic Theory, and Shuttle Pathways",
            "Photosynthesis: Light Reactions, Photophosphorylation, and Carbon Fixation",
        ],
    ),
    (
        3,
        "Carbohydrate Metabolism",
        [
            "Glycolysis and Pyruvate Dehydrogenase Complex",
            "Citric Acid Cycle (TCA Cycle) and Amphibolic Nature",
            "Gluconeogenesis and Glycogen Metabolism (Glycogenesis and Glycogenolysis)",
            "Hormonal Regulation of Blood Glucose: Insulin, Glucagon, and Diabetes",
        ],
    ),
    (
        4,
        "Protein Turnover and Amino Acids Metabolism",
        [
            "Protein Turnover, Proteolysis, and PEST Sequences",
            "Transamination, Deamination, and Decarboxylation of Amino Acids",
            "Urea Cycle, Ammonia Toxicity, and Inborn Errors of Metabolism",
            "Biosynthesis and Degradation of Essential and Non-Essential Amino Acids",
        ],
    ),
    (
        5,
        "Fatty Acid and Nucleic Acids Metabolisms",
        [
            "Mobilization of Lipids and Beta-Oxidation of Fatty Acids",
            "Ketogenesis, Ketone Bodies, and Lipid Metabolism Disorders",
            "Biosynthesis of Fatty Acids, Cholesterol, Eicosanoids, and Lipoproteins",
            "Purine and Pyrimidine Nucleotide Biosynthesis and Degradation",
        ],
    ),
]


def seed_biochem_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 12 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 12")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 12 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 12")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (12, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in BIOCHEM_CANONICAL_TAXONOMY:
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Biochemistry', 'CANONICAL')",
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
    res = seed_biochem_taxonomy()
    print("Course 12 Taxonomy Seeding Result:", res)
