"""
Additive, idempotent seeder for Course 6: Fundamental Of Economics (FOE) (18MSS101T).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Economics Syllabus (18MSS101T / 21MGH101T), course decks, and Question Bank.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

FOE_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Introduction to Economics and Consumer Behaviour",
        [
            "Definitions, Nature, and Scope of Economics",
            "Microeconomics, Macroeconomics, and Central Economic Problems",
            "Cardinal Utility Analysis and Law of Diminishing Marginal Utility",
            "Consumer Preferences and Indifference Curve Analysis",
        ],
    ),
    (
        2,
        "Demand, Supply, and Market Equilibrium",
        [
            "Theory of Demand, Law of Demand, and Demand Elasticity",
            "Income Elasticity and Cross Elasticity of Demand",
            "Theory of Supply, Law of Supply, and Elasticity of Supply",
            "Market Equilibrium and Consumer Surplus",
        ],
    ),
    (
        3,
        "Production and Cost Analysis",
        [
            "Factors of Production and Short-Run Production Function",
            "Law of Variable Proportions and Returns to Scale",
            "Cost Analysis: Short-Run and Long-Run Cost Curves",
            "Revenue Concepts, Cost Minimization, and Profit Maximization",
        ],
    ),
    (
        4,
        "Market Structures and Pricing",
        [
            "Perfect Competition: Features and Equilibrium Analysis",
            "Monopoly: Characteristics, Pricing, and Price Discrimination",
            "Monopolistic Competition: Product Differentiation and Equilibrium",
            "Oligopoly: Characteristics, Cartels, and Price Rigidity",
        ],
    ),
    (
        5,
        "Money, Banking, and Macroeconomic Aggregates",
        [
            "Money: Functions, Evolution, and Quantity Theory",
            "Commercial Banking, Credit Creation, and Central Bank Monetary Policy",
            "Inflation, Deflation, and Business Cycles",
            "National Income Accounting and Balance of Payments",
        ],
    ),
]


def seed_foe_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 6 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 6")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 6 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 6")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (6, '2018-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in FOE_CANONICAL_TAXONOMY:
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Fundamental Of Economics (FOE)', 'CANONICAL')",
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
    res = seed_foe_taxonomy()
    print("Course 6 Taxonomy Seeding Result:", res)
