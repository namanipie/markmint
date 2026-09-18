"""
Additive, idempotent seeder for Course 18: Electronic System and PCB Design (21ECC101J).
Seeds 5 canonical units and 25 syllabus-backed topics derived strictly from the official
SRM IST Department of Electronics and Communication Engineering Syllabus (21ECC101J).
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

ESPCB_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Semiconductor Fundamentals and Devices",
        [
            "Classification of Semiconductors and Doping",
            "Energy Bands, Fermi Level, and Mass-Action Law",
            "Drift, Diffusion Currents, and Einstein Relationship",
            "PN Junction Diodes, BJT, and MOSFETs",
            "Advanced Nano-MOSFETs, SOI MOSFET, and FinFET",
        ],
    ),
    (
        2,
        "Power Devices and Fabrication",
        [
            "Power Semiconductor Devices and Power Electronics",
            "Power Diodes, Schottky Diode, Gunn Diode, and IMPATT Diode",
            "Thyristor, PNPN Diode, and Silicon Controlled Rectifier (SCR)",
            "Power BJT and Power MOSFET Switching Characteristics",
            "Monolithic IC Fabrication Processes",
        ],
    ),
    (
        3,
        "Power Supplies and Measurement Instruments",
        [
            "Regulated Power Supplies and Rectifiers",
            "Voltage Regulators and Line-Load Regulation",
            "Switched Mode Power Supply (SMPS)",
            "Wave Shaping Circuits and Multivibrators",
            "Electronic Measurement Instruments and Oscilloscopes",
        ],
    ),
    (
        4,
        "PCB Design Concepts",
        [
            "PCB Classifications, Types of Boards, and Manufacturing",
            "PCB Schematic Design and Layout Planning",
            "Mechanical Design Considerations and Stress Analysis",
            "Component Mounting, Assembly, and Soldering Techniques",
            "Electrical Design Considerations, Component Placement, and Routing",
        ],
    ),
    (
        5,
        "Advanced PCB Design and Application",
        [
            "Environmental Factors, Thermal Management, and Cooling of PCBs",
            "Layout Checklists and Design Rules for Analog and Digital PCBs",
            "Signal Integrity, Noise, Cross-talk, and Reflections in PCBs",
            "High-Frequency and Fast-Pulse PCB Design",
            "Microwave and RF PCB Design",
        ],
    ),
]


def seed_espcb_taxonomy(db_path: str = DEFAULT_DB_PATH, dry_run: bool = False) -> Dict[str, Any]:
    """Seed Course 18 units, topics, and concepts into the local SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, name, canonical_code FROM courses WHERE id = 18")
    course = c.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 18 not found in database!")

    c.execute("SELECT id FROM syllabuses WHERE course_id = 18")
    syl_row = c.fetchone()
    if syl_row:
        syllabus_id = syl_row["id"]
    else:
        if not dry_run:
            c.execute("INSERT INTO syllabuses (course_id, version) VALUES (18, '2021-Regulation')")
            syllabus_id = c.lastrowid
        else:
            syllabus_id = -1

    units_created = 0
    units_updated = 0
    topics_created = 0
    topics_existing = 0
    concepts_created = 0

    unit_mapping: Dict[int, int] = {}

    for unit_num, unit_name, topic_names in ESPCB_CANONICAL_TAXONOMY:
        c.execute(
            "SELECT id, name FROM units WHERE syllabus_id = ? AND number = ?",
            (syllabus_id, unit_num),
        )
        existing_unit = c.fetchone()

        if existing_unit:
            u_id = existing_unit["id"]
            if existing_unit["name"] != unit_name:
                if not dry_run:
                    c.execute("UPDATE units SET name = ? WHERE id = ?", (unit_name, u_id))
                units_updated += 1
        else:
            if not dry_run:
                c.execute(
                    "INSERT INTO units (syllabus_id, name, number) VALUES (?, ?, ?)",
                    (syllabus_id, unit_name, unit_num),
                )
                u_id = c.lastrowid
            else:
                u_id = -1
            units_created += 1

        unit_mapping[unit_num] = u_id

        # Insert topics
        for t_name in topic_names:
            c.execute(
                "SELECT id FROM topics WHERE unit_id = ? AND name = ?",
                (u_id, t_name),
            )
            existing_t = c.fetchone()
            if existing_t:
                topics_existing += 1
                t_id = existing_t["id"]
            else:
                if not dry_run:
                    c.execute(
                        "INSERT INTO topics (unit_id, name) VALUES (?, ?)",
                        (u_id, t_name),
                    )
                    t_id = c.lastrowid
                else:
                    t_id = -1
                topics_created += 1

            # Seed default concept
            if not dry_run:
                c.execute("SELECT id FROM concepts WHERE canonical_name = ?", (t_name,))
                if not c.fetchone():
                    c.execute(
                        "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Electronic System and PCB Design', 'CANONICAL')",
                        (t_name,),
                    )
                    concepts_created += 1

    if not dry_run:
        conn.commit()

    # Query final counts
    c.execute(
        """
        SELECT COUNT(u.id) as unit_count, COUNT(t.id) as topic_count
        FROM units u
        LEFT JOIN topics t ON t.unit_id = u.id
        WHERE u.syllabus_id = ?
        """,
        (syllabus_id,),
    )
    final_stats = c.fetchone()
    conn.close()

    return {
        "course_id": 18,
        "course_name": course["name"],
        "syllabus_id": syllabus_id,
        "units_created": units_created,
        "units_updated": units_updated,
        "topics_created": topics_created,
        "topics_existing": topics_existing,
        "concepts_created": concepts_created,
        "total_units": final_stats["unit_count"] if not dry_run else None,
        "total_topics": final_stats["topic_count"] if not dry_run else None,
        "dry_run": dry_run,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed ESPCB taxonomy")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without mutating DB")
    args = parser.parse_args()

    res = seed_espcb_taxonomy(dry_run=args.dry_run)
    print("ESPCB Taxonomy Seeding Result:")
    for k, v in res.items():
        print(f"  {k}: {v}")
