"""
Additive, idempotent seeder for Course 16: Advanced Calculus and Complex Analysis (21MAB102T).
Seeds 5 canonical units and 24 syllabus-backed topics derived strictly from the official
SRM IST Department of Mathematics Syllabus and course lecture decks (21MAB102T).
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")

ACCA_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Multiple Integrals",
        [
            "Double Integrals and Change of Variables",
            "Change of Order of Integration",
            "Triple Integrals and Volume Evaluation",
            "Area and Volume as Multiple Integrals",
        ],
    ),
    (
        2,
        "Vector Calculus",
        [
            "Gradient, Directional Derivative, and Potential Functions",
            "Divergence, Curl, Solenoidal, and Irrotational Fields",
            "Green's Theorem in a Plane",
            "Stokes' Theorem",
            "Gauss Divergence Theorem",
        ],
    ),
    (
        3,
        "Laplace Transforms",
        [
            "Laplace Transforms of Elementary Functions and Shifting Properties",
            "Laplace Transforms of Derivatives, Integrals, and Periodic Functions",
            "Inverse Laplace Transforms and Partial Fractions",
            "Convolution Theorem for Laplace Transforms",
            "Solving Ordinary Differential Equations Using Laplace Transforms",
        ],
    ),
    (
        4,
        "Analytic Functions",
        [
            "Analytic Functions and Cauchy-Riemann Equations",
            "Harmonic Functions and Orthogonal Trajectories",
            "Milne-Thomson Method for Analytic Functions",
            "Conformal Mapping and Standard Transformations",
            "Bilinear Transformations and Cross-Ratio",
        ],
    ),
    (
        5,
        "Complex Integration",
        [
            "Cauchy's Integral Theorem and Cauchy's Integral Formula",
            "Taylor's and Laurent's Series Expansions",
            "Singularities, Poles, and Residues",
            "Cauchy's Residue Theorem",
            "Contour Integration",
        ],
    ),
]


def seed_acca_taxonomy(db_path: str = DEFAULT_DB_PATH, dry_run: bool = False) -> Dict[str, Any]:
    """Seed Course 16 units, topics, and concepts into the local SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id, name, canonical_code FROM courses WHERE id = 16")
    course = c.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 16 not found in database!")

    c.execute("SELECT id FROM syllabuses WHERE course_id = 16")
    syl_row = c.fetchone()
    if syl_row:
        syllabus_id = syl_row["id"]
    else:
        if not dry_run:
            c.execute("INSERT INTO syllabuses (course_id, version) VALUES (16, '2021-Regulation')")
            syllabus_id = c.lastrowid
        else:
            syllabus_id = -1

    units_created = 0
    units_updated = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in ACCA_CANONICAL_TAXONOMY:
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
                        "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Advanced Calculus and Complex Analysis', 'CANONICAL')",
                        (t_name,)
                    )
                concepts_created += 1

    if not dry_run:
        conn.commit()

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

    return {
        "dry_run": dry_run,
        "course_id": 16,
        "syllabus_id": syllabus_id,
        "units_created": units_created,
        "units_updated": units_updated,
        "topics_created": topics_created,
        "concepts_created": concepts_created,
        "total_topics_in_course": total_topics,
        "units": seeded_units,
    }


if __name__ == "__main__":
    res = seed_acca_taxonomy(dry_run=False)
    print("=== ACCA Taxonomy Seeding Result ===")
    print(f"Units: created={res['units_created']}, updated={res['units_updated']}")
    print(f"Topics created: {res['topics_created']}")
    print(f"Total topics: {res['total_topics_in_course']}")
    for u in res["units"]:
        print(f"  Unit {u['number']} (id={u['id']}): {u['name']}")
