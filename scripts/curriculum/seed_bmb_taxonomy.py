"""
Additive, idempotent seeder for Course 7: Biomedical Sensors (21BMB101T).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Biomedical Engineering Syllabus (21BMC101J / 21BMB101T) and course decks.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

BMB_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Measurement System and Medical Instrumentation",
        [
            "Functional Elements and Terminologies of Measurement Systems",
            "Classification and Display of Electrical Parameters",
            "Advantages and Architecture of Electronic Instruments",
            "Functional Elements and Salient Features of Medical Instruments",
        ],
    ),
    (
        2,
        "Temperature Transducers",
        [
            "Principles, Types, and Classification of Transducers",
            "Resistance Temperature Detectors (RTD): Principles and Applications",
            "Thermistors: Characteristics, Construction, and Working",
            "Thermocouples: Seebeck Effect, Operating Principles, and Applications",
        ],
    ),
    (
        3,
        "Pressure and Magnetic Transducers",
        [
            "Strain Gauges and Load Cells: Principles and Construction",
            "Capacitive Transducers: Working Principles and Operation",
            "Piezoelectric Transducers: Piezoelectric Effect and Applications",
            "Linear Variable Differential Transformers (LVDT): Construction and Operation",
        ],
    ),
    (
        4,
        "Optical Transducers",
        [
            "Photodiodes: Operating Principles and Characteristic Curves",
            "Phototransistors: Construction and Working Principles",
            "Light Dependent Resistors (LDR) and Photoconductive Cells",
            "Photovoltaic Cells and Optical Sensor Applications",
        ],
    ),
    (
        5,
        "Medical Applications of Sensors",
        [
            "Pulse Oximetry and Blood Oxygen Saturation (SpO2) Monitoring",
            "Heart Rate Sensors and Photoplethysmography (PPG)",
            "Blood Pressure Sensors: Systolic and Diastolic Measurement",
            "Infrared (IR) Sensors in Clinical and Biomedical Diagnostics",
        ],
    ),
]


def seed_bmb_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 7 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 7")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 7 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 7")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (7, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in BMB_CANONICAL_TAXONOMY:
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Biomedical Sensors', 'CANONICAL')",
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
    res = seed_bmb_taxonomy()
    print("Course 7 Taxonomy Seeding Result:", res)
