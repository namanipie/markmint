"""
Additive, idempotent seeder for Course 13: Semiconductor Physics and Computational Methods.
Seeds 5 canonical units and 27 syllabus-backed topics derived strictly from the official
SRM IST Department of Physics & Nanotechnology Lesson Plan (21PYB102J) and course decks.

Idempotency guarantees:
- Reuses existing Syllabus, Units, Topics, and Concepts if already present.
- Never deletes or overwrites existing records.
- Strictly scoped to Course ID 13.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SPCM_SOURCES = (
    "corpus/Semester_2/Semiconductor Physics And Computational Methods/UNKNOWN/"
    "Semiconductor Physics And Computational Methods - Lesson Plan.pdf; "
    "corpus/Semester_1/Semiconductor Physics and Computational Methods/STUDY_MATERIAL/"
    "Semiconductor Physics and Computational Methods - Unit 1.pdf through Unit 5.pdf; "
    "corpus/Semester_2/Semiconductor Physics And Computational Methods/PYQ/"
    "Semiconductor Physics And Computational Methods/MCQs & Question Banks/"
    "Semiconductor Physics And Computational Methods - UNIT_1_PHYSICS_QUESTION_BANK_FROM_KTR_CAMPUS_WITH_ANSWERS_FOR_SEMESTER.pdf through UNIT_5_..."
)

# 5 Canonical Units and 27 Syllabus Topics
SPCM_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Free Electron Theory and Energy Bands",
        [
            "Classical Free Electron Theory",
            "Quantum Free Electron Theory",
            "Band Theory and Kronig-Penney Model",
            "Brillouin Zones and Band Gaps",
            "Fermi Surface and Computational Band Structure",
        ],
    ),
    (
        2,
        "Semiconductor Physics and Carrier Transport",
        [
            "Intrinsic Semiconductors",
            "Extrinsic Semiconductors and Doping",
            "Carrier Generation, Recombination, and Continuity",
            "Carrier Transport: Drift and Diffusion",
            "P-N Junction and Biasing",
            "Metal-Semiconductor Contacts",
            "Optoelectronic Devices and LEDs",
        ],
    ),
    (
        3,
        "Optical Processes and Photovoltaic Devices",
        [
            "Optical Transitions and Absorption",
            "Radiative Recombination and Emission",
            "Joint Density of States and Transition Rates",
            "Computational Optics and Optical Loss",
            "Solar Cells and Photovoltaics",
        ],
    ),
    (
        4,
        "Semiconductor Measurements and Transport Equations",
        [
            "Two-Point and Four-Point Probe Measurements",
            "Hall Effect and Carrier Mobility",
            "Hot-Point Probe and Capacitance-Voltage Measurements",
            "Diode Parameter Extraction and TCAD",
            "Boltzmann Transport Equation and Monte Carlo Method",
        ],
    ),
    (
        5,
        "Nanostructures and Characterization",
        [
            "Low-Dimensional Systems and Density of States",
            "Carbon Nanotubes (CNT)",
            "Nanofabrication Techniques",
            "Electron Microscopy and Surface Characterization",
            "Computational Image Processing for Nanomaterials",
        ],
    ),
]


def seed_spcm_taxonomy(db_path: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Seed SPCM units, topics, and concepts into the local SQLite database.
    Additive and idempotent: never modifies or deletes existing rows.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Verify Course 13 exists
    course = c.execute("SELECT id, name, code FROM courses WHERE id = 13").fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 13 (Semiconductor Physics and Computational Methods) not found in database.")

    # 2. Get or create syllabus for Course 13
    syl = c.execute("SELECT id, course_id, version FROM syllabuses WHERE course_id = 13").fetchone()
    if not syl:
        if not dry_run:
            c.execute("INSERT INTO syllabuses (course_id, version) VALUES (13, '1.0')")
            syl_id = c.lastrowid
        else:
            syl_id = 13
    else:
        syl_id = syl["id"]

    # 3. Read existing units for this syllabus
    existing_units = c.execute(
        "SELECT id, number, name FROM units WHERE syllabus_id = ?", (syl_id,)
    ).fetchall()
    unit_by_name = {u["name"]: u["id"] for u in existing_units}
    unit_by_num = {u["number"]: u["id"] for u in existing_units if u["name"] != "General Unit"}

    # 4. Read existing topics for this course
    existing_topics = c.execute("""
        SELECT t.id, t.name, t.unit_id
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        WHERE u.syllabus_id = ?
    """, (syl_id,)).fetchall()
    topic_by_name = {t["name"]: t["id"] for t in existing_topics}

    # 5. Read existing concepts
    existing_concepts = c.execute(
        "SELECT id, canonical_name FROM concepts WHERE subject LIKE '%Semiconductor%'"
    ).fetchall()
    concept_by_name = {cp["canonical_name"]: cp["id"] for cp in existing_concepts}

    units_created = 0
    topics_created = 0
    concepts_created = 0

    unit_id_map: Dict[int, int] = {}

    for unit_num, unit_name, topics in SPCM_CANONICAL_TAXONOMY:
        # Check if unit exists
        if unit_name in unit_by_name:
            uid = unit_by_name[unit_name]
        elif unit_num in unit_by_num:
            uid = unit_by_num[unit_num]
        else:
            if not dry_run:
                c.execute(
                    "INSERT INTO units (syllabus_id, number, name) VALUES (?, ?, ?)",
                    (syl_id, unit_num, unit_name),
                )
                uid = c.lastrowid
                unit_by_name[unit_name] = uid
            else:
                uid = 100 + unit_num
            units_created += 1
        unit_id_map[unit_num] = uid

        for tname in topics:
            if tname not in topic_by_name:
                if not dry_run:
                    c.execute(
                        "INSERT INTO topics (name, unit_id) VALUES (?, ?)",
                        (tname, uid),
                    )
                    tid = c.lastrowid
                    topic_by_name[tname] = tid
                else:
                    tid = 200 + topics_created
                topics_created += 1
            else:
                tid = topic_by_name[tname]

            if tname not in concept_by_name:
                desc = f"Course-specific topic from {unit_name}: {tname}. Source evidence: {SPCM_SOURCES}"
                if not dry_run:
                    c.execute("""
                        INSERT INTO concepts (canonical_name, description, status, subject, unit_id)
                        VALUES (?, ?, 'CANONICAL', 'Semiconductor Physics and Computational Methods', ?)
                    """, (tname, desc, uid))
                    cid = c.lastrowid
                    concept_by_name[tname] = cid
                else:
                    cid = 300 + concepts_created
                concepts_created += 1

    if not dry_run:
        conn.commit()

    # Final counts
    final_units = c.execute(
        "SELECT count(*) FROM units WHERE syllabus_id = ?", (syl_id,)
    ).fetchone()[0]
    final_topics = c.execute("""
        SELECT count(*)
        FROM topics t
        JOIN units u ON t.unit_id = u.id
        WHERE u.syllabus_id = ?
    """, (syl_id,)).fetchone()[0]
    final_concepts = c.execute(
        "SELECT count(*) FROM concepts WHERE subject LIKE '%Semiconductor%'"
    ).fetchone()[0]

    conn.close()

    return {
        "dry_run": dry_run,
        "units_created": units_created,
        "topics_created": topics_created,
        "concepts_created": concepts_created,
        "total_units_for_course": final_units,
        "total_topics_for_course": final_topics,
        "total_concepts_for_course": final_concepts,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed SPCM canonical taxonomy into SQLite database.")
    parser.add_argument("--db", default="production_corpus.db", help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Simulate seeding without committing")
    args = parser.parse_args()

    result = seed_spcm_taxonomy(args.db, dry_run=args.dry_run)
    print("SPCM Taxonomy Seeder Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
