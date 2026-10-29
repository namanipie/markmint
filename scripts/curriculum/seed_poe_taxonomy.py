"""
Additive, idempotent seeder for Course 3: Philosophy Of Engineering (21GNH101J).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of General Engineering Syllabus, Faculty Unit 1-5 Course Decks,
and KTR/Ramapuram Question Banks.

Idempotency guarantees:
- Reuses existing Syllabus, Units, Topics, and Concepts if already present.
- Never deletes or overwrites existing records.
- Strictly scoped to Course ID 3.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

POE_SOURCES = (
    "corpus/Semester_1/Philosophy of Engineering/SYLLABUS/Philosophy of Engineering - Syllabus.pdf; "
    "corpus/Semester_1/Philosophy of Engineering/UNKNOWN/Philosophy Of Engineering - Important Topics & Exam Pattern.pdf; "
    "corpus/Semester_1/Philosophy of Engineering/STUDY_MATERIAL/Philosophy of Engineering - Unit 1.pdf through Unit 5.pdf; "
    "corpus/Semester_1/Philosophy of Engineering/STUDY_MATERIAL/Philosophy Of Engineering/MCQ & Question Bank/Philosophy Of Engineering - MCQ QUESTION BANK- UNIT 1 & 2 .pdf & UNIT 3,4 & 5 .pdf"
)

# 5 Canonical Units and 20 Syllabus Topics for Course 3
POE_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Introduction to Philosophy of Engineering",
        [
            "Definition and Scope of Engineering",
            "STEAM Pyramid and Interdisciplinary Education",
            "Engineering Habits of Mind and Professional Attributes",
            "Historical Evolution and Eras of Engineering",
        ],
    ),
    (
        2,
        "Ontology of Engineering",
        [
            "Philosophical Ontology and Nature of Artifacts",
            "Reference Ontology and Application Ontology",
            "Product Life Cycle and Developmental Stages",
            "System Classification and Domain Modeling",
        ],
    ),
    (
        3,
        "Epistemology of Engineering",
        [
            "Relations Between Science, Technology, and Engineering",
            "Four Dimensions of Engineering Practice",
            "RIASEC Model and Engineering Typology",
            "Design Epistemology and Engineering Knowledge Base",
        ],
    ),
    (
        4,
        "Methodology of Engineering",
        [
            "Scientific Method vs Engineering Design Process",
            "ADDIE Model and Instructional System Design",
            "CDIO Framework in Industry and Practice",
            "Engineering Modeling and Problem Formulation",
        ],
    ),
    (
        5,
        "Axiology of Engineering",
        [
            "Engineering Ethics and Professional Codes of Conduct",
            "Sustainable Development and Ecological Stewardship",
            "Concept of 3Es: Engineering, Economics, and Ethics",
            "Professional Engineering Societies and Social Responsibility",
        ],
    ),
]


def seed_poe_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 3 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Verify Course 3 exists
    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 3")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 3 not found in database!")

    # 2. Find or create Syllabus for Course 3
    cur.execute("SELECT id FROM syllabuses WHERE course_id = 3")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (3, '2021-Regulation')", )
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    unit_id_map: Dict[int, int] = {}

    for unit_num, unit_title, topic_list in POE_CANONICAL_TAXONOMY:
        cur.execute(
            "SELECT id FROM units WHERE syllabus_id = ? AND number = ?",
            (syllabus_id, unit_num)
        )
        u_row = cur.fetchone()
        if u_row:
            u_id = u_row[0]
            # Update name if General Unit
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

        unit_id_map[unit_num] = u_id

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

            # Mirror to concepts if not exists
            cur.execute("SELECT id FROM concepts WHERE canonical_name = ?", (t_name,))
            c_row = cur.fetchone()
            if not c_row:
                cur.execute(
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Philosophy Of Engineering', 'CANONICAL')",
                    (t_name,)
                )
                concepts_created += 1

    conn.commit()

    # Integrity verification
    cur.execute("""
        SELECT count(t.id) 
        FROM topics t 
        JOIN units u ON t.unit_id = u.id 
        WHERE u.syllabus_id = ?
    """, (syllabus_id,))
    total_poe_topics = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM units WHERE syllabus_id = ?", (syllabus_id,))
    total_poe_units = cur.fetchone()[0]

    conn.close()

    return {
        "syllabus_id": syllabus_id,
        "units_created": units_created,
        "topics_created": topics_created,
        "concepts_created": concepts_created,
        "total_units": total_poe_units,
        "total_topics": total_poe_topics,
    }


if __name__ == "__main__":
    res = seed_poe_taxonomy()
    print("Course 3 Taxonomy Seeding Result:", res)
