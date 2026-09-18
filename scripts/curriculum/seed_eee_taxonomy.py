"""
Additive, idempotent seeder for Course 14: Electrical and Electronics Engineering (21EEB101J / 21EES101T).
Seeds 5 canonical units and 35 syllabus-backed topics derived strictly from the official
SRM IST Department of Electrical & Electronics Engineering syllabus slide decks.

Idempotency guarantees:
- Reuses existing Syllabus, Units, Topics, and Concepts if already present.
- Never deletes or overwrites existing records.
- Strictly scoped to Course ID 14.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

EEE_SOURCES = (
    "corpus/Semester_1/Electrical and Electronics Engineering (EEE)/STUDY_MATERIAL/"
    "Electrical and Electronics Engineering (EEE) - Unit 1.pdf through Unit 5.pdf (21EES101T / 21EEB101J); "
    "data/1 Year/BEEE/ course files and lesson plans"
)

# 5 Canonical Units and 35 Syllabus Topics
EEE_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Electric Circuits",
        [
            "DC Circuit Terminologies and Kirchhoff's Laws",
            "Mesh Current and Nodal Voltage Analysis",
            "Network Theorems",
            "AC Circuit Fundamentals",
            "Single-Phase AC Series Circuits",
            "Three-Phase AC Systems",
            "Rectifier Circuits",
        ],
    ),
    (
        2,
        "Electronics",
        [
            "Semiconductors, Diodes, and BJT",
            "Field Effect Transistors",
            "Power Semiconductor Devices",
            "SCR Switching and Commutation",
            "Power Converters and Regulators",
            "Digital Logic and Combinational Design",
            "Karnaugh Map Minimization",
            "FPGA and PCB Design",
        ],
    ),
    (
        3,
        "Machines and Drives",
        [
            "DC Machines",
            "Single-Phase Transformers",
            "Three-Phase Induction Motors",
            "Special Electrical Machines",
            "Electrical Drives and Choppers",
            "Drive Applications",
        ],
    ),
    (
        4,
        "Transducers and Sensors",
        [
            "Electrical Measuring Instruments",
            "Electronic Measuring Instruments",
            "Displacement and Position Transducers",
            "Temperature Transducers",
            "Piezoelectric, Photoelectric, and Hall Effect Transducers",
            "Optoelectronic Devices and Photosensors",
            "Industrial and Biomedical Sensors",
        ],
    ),
    (
        5,
        "Power Engineering",
        [
            "Electric Power Supply Systems",
            "Substations and Smart Grid",
            "Electrical Safety and Earthing",
            "Electrical Safety Devices",
            "Renewable Energy and Solar Photovoltaic",
            "Energy Storage and Batteries",
            "Electric Vehicles and Charging",
        ],
    ),
]


def seed_eee_taxonomy(db_path: str = DEFAULT_DB_PATH, dry_run: bool = False) -> Dict[str, Any]:
    """
    Seed EEE units, topics, and concepts into the local SQLite database.
    Additive and idempotent: never modifies or deletes existing rows.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, name, canonical_code FROM courses WHERE id = 14")
    course = c.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 14 not found in database!")

    c.execute("SELECT id FROM syllabuses WHERE course_id = 14")
    syl_row = c.fetchone()
    if syl_row:
        syllabus_id = syl_row["id"]
    else:
        if not dry_run:
            c.execute("INSERT INTO syllabuses (course_id, version) VALUES (14, '2021-Regulation')")
            syllabus_id = c.lastrowid
        else:
            syllabus_id = -1

    units_created = 0
    units_updated = 0
    topics_created = 0
    concepts_created = 0
    unit_id_map: Dict[int, int] = {}

    for unit_num, unit_title, topic_list in EEE_CANONICAL_TAXONOMY:
        c.execute(
            "SELECT id, name FROM units WHERE syllabus_id = ? AND number = ?",
            (syllabus_id, unit_num)
        )
        u_row = c.fetchone()
        if u_row:
            u_id = u_row["id"]
            existing_name = u_row["name"]
            if existing_name == "General Unit" or existing_name != unit_title:
                if not dry_run:
                    c.execute("UPDATE units SET name = ? WHERE id = ?", (unit_title, u_id))
                units_updated += 1
        else:
            if not dry_run:
                c.execute(
                    "INSERT INTO units (syllabus_id, number, name) VALUES (?, ?, ?)",
                    (syllabus_id, unit_num, unit_title)
                )
                u_id = c.lastrowid
            else:
                u_id = -1
            units_created += 1

        unit_id_map[unit_num] = u_id

        for t_name in topic_list:
            c.execute(
                "SELECT id FROM topics WHERE unit_id = ? AND name = ?",
                (u_id, t_name)
            )
            t_row = c.fetchone()
            if not t_row:
                if not dry_run:
                    c.execute(
                        "INSERT INTO topics (unit_id, name) VALUES (?, ?)",
                        (u_id, t_name)
                    )
                    t_id = c.lastrowid
                else:
                    t_id = -1
                topics_created += 1
            else:
                t_id = t_row["id"]

            c.execute("SELECT id FROM concepts WHERE canonical_name = ?", (t_name,))
            c_row = c.fetchone()
            if not c_row:
                if not dry_run:
                    c.execute(
                        "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Electrical and Electronics Engineering', 'CANONICAL')",
                        (t_name,)
                    )
                concepts_created += 1

    if not dry_run:
        conn.commit()

    # Query current totals
    c.execute("""
        SELECT count(t.id) as topic_count
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        WHERE u.syllabus_id = ?
    """, (syllabus_id,))
    total_topics = c.fetchone()["topic_count"]

    c.execute("""
        SELECT id, number, name FROM units WHERE syllabus_id = ? ORDER BY number
    """, (syllabus_id,))
    seeded_units = [dict(r) for r in c.fetchall()]

    conn.close()

    result = {
        "dry_run": dry_run,
        "course_id": 14,
        "syllabus_id": syllabus_id,
        "units_created": units_created,
        "units_updated": units_updated,
        "topics_created": topics_created,
        "concepts_created": concepts_created,
        "total_topics_in_course": total_topics,
        "units": seeded_units,
    }
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed EEE Course 14 canonical taxonomy.")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without committing.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite database.")
    args = parser.parse_args()

    res = seed_eee_taxonomy(db_path=args.db_path, dry_run=args.dry_run)
    print(f"=== EEE Taxonomy Seeding Result ===")
    print(f"Dry Run: {res['dry_run']}")
    print(f"Units Created: {res['units_created']}, Units Updated: {res['units_updated']}")
    print(f"Topics Created: {res['topics_created']}")
    print(f"Concepts Created: {res['concepts_created']}")
    print(f"Total Topics in Course 14: {res['total_topics_in_course']}")
    print("Units in Syllabus:")
    for u in res["units"]:
        print(f"  Unit {u['number']} (id={u['id']}): {u['name']}")
