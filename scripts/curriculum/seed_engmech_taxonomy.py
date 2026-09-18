"""
Additive, idempotent seeder for Course 21: Engineering Mechanics (21MEB101T).
Seeds 5 canonical units and 25 syllabus-backed topics derived strictly from the official
SRM IST Department of Mechanical Engineering Syllabus (21MEB101T / 21MES101T).
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

ENGMECH_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Statics of Particles and Rigid Bodies",
        [
            "Force Systems, Resultant of Forces, and Parallelogram Law",
            "Free Body Diagrams, Equilibrium of Particles, and Lami's Theorem",
            "Moments, Couples, and Varignon's Theorem",
            "Equilibrium of Rigid Bodies and Types of Supports",
            "Analysis of Simple Trusses and Method of Joints",
        ],
    ),
    (
        2,
        "Friction and Its Applications",
        [
            "Laws of Dry Friction, Limiting Friction, and Coefficient of Friction",
            "Angle of Friction, Cone of Friction, and Angle of Repose",
            "Friction on Horizontal and Inclined Planes",
            "Ladder Friction and Wedge Friction",
            "Belt Friction and Screw Jack Friction",
        ],
    ),
    (
        3,
        "Centroid and Moment of Inertia",
        [
            "Centroid of Lines, Simple Areas, and Composite Figures",
            "Centre of Gravity of Solid Bodies",
            "Moment of Inertia of Areas and Parallel Axis Theorem",
            "Perpendicular Axis Theorem and Polar Moment of Inertia",
            "Mass Moment of Inertia of Standard Geometries",
        ],
    ),
    (
        4,
        "Dynamics of Particles: Kinematics and Kinetics",
        [
            "Rectilinear Motion: Position, Velocity, and Acceleration",
            "Curvilinear Motion and Projectile Motion",
            "Newton's Second Law and D'Alembert's Principle for Particles",
            "Work-Energy Principle for Particles",
            "Impulse-Momentum Principle and Impact of Elastic Bodies",
        ],
    ),
    (
        5,
        "Kinematics and Kinetics of Rigid Bodies",
        [
            "Translation and Rotation of Rigid Bodies About a Fixed Axis",
            "General Plane Motion and Instantaneous Centre of Rotation",
            "Equations of Motion for Plane Motion of Rigid Bodies",
            "Work-Energy Principle for Rigid Bodies",
            "Impulse and Angular Momentum for Rigid Bodies",
        ],
    ),
]


def seed_engmech_taxonomy(db_path: str = DEFAULT_DB_PATH, dry_run: bool = False) -> Dict[str, Any]:
    """Seed Course 21 units, topics, and concepts into the local SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, name, canonical_code FROM courses WHERE id = 21")
    course = c.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 21 not found in database!")

    c.execute("SELECT id FROM syllabuses WHERE course_id = 21")
    syl_row = c.fetchone()
    if syl_row:
        syllabus_id = syl_row["id"]
    else:
        if not dry_run:
            c.execute("INSERT INTO syllabuses (course_id, version) VALUES (21, '2021-Regulation')")
            syllabus_id = c.lastrowid
        else:
            syllabus_id = -1

    units_created = 0
    units_updated = 0
    topics_created = 0
    topics_existing = 0
    concepts_created = 0

    unit_mapping: Dict[int, int] = {}

    for unit_num, unit_name, topic_names in ENGMECH_CANONICAL_TAXONOMY:
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
                        "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Engineering Mechanics', 'CANONICAL')",
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
        "course_id": 21,
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
    parser = argparse.ArgumentParser(description="Seed Engineering Mechanics taxonomy")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without mutating DB")
    args = parser.parse_args()

    res = seed_engmech_taxonomy(dry_run=args.dry_run)
    print("Engineering Mechanics Taxonomy Seeding Result:")
    for k, v in res.items():
        print(f"  {k}: {v}")
