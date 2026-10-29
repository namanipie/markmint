"""
Additive, idempotent seeder for Course 5: Programming For Problem Solving (21CSS101J).
Seeds 5 canonical units and 20 syllabus-backed topics derived strictly from the official
SRM IST Department of Computer Science & Engineering Syllabus (21CSS101J) and course decks.
"""
import os
import sys
import sqlite3
from typing import Dict, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PPS_CANONICAL_TAXONOMY: List[Tuple[int, str, List[str]]] = [
    (
        1,
        "Problem Solving and C Basics",
        [
            "Problem Solving Process, Algorithms, and Flowcharts",
            "Pseudocode and Program Design Techniques",
            "C Program Structure, Tokens, Keywords, and Identifiers",
            "Data Types, Variables, Constants, Operators, and Expressions",
        ],
    ),
    (
        2,
        "Control Flow, Arrays, and Pointers",
        [
            "Conditional Branching: if, if-else, nested if, and switch-case",
            "Iteration and Loops: for, while, do-while, and Jump Statements",
            "One-Dimensional and Multi-Dimensional Arrays",
            "Pointers, Address-of Operator, Dereferencing, and Pointer Arithmetic",
        ],
    ),
    (
        3,
        "Strings, Functions, and Storage Classes",
        [
            "Character Arrays and String Handling Functions",
            "User-Defined Functions and Parameter Passing Techniques",
            "Recursion and Recursive Problem Solving",
            "Storage Classes, Variable Scope, and Linkage",
        ],
    ),
    (
        4,
        "Introduction to Python and Data Structures",
        [
            "Python Language Basics, Variables, and Built-in Data Types",
            "Python Control Structures and Comprehensions",
            "Python Data Structures: Lists, Tuples, Sets, and Dictionaries",
            "Python Functions, Modules, and Exception Handling",
        ],
    ),
    (
        5,
        "Data Analysis with NumPy and Pandas",
        [
            "NumPy Array Creation, Attributes, Indexing, and Slicing",
            "Numerical Operations and Descriptive Statistics with NumPy",
            "Pandas Series and DataFrame Data Structures",
            "Data Manipulation, Querying, and Tabular Operations in Pandas",
        ],
    ),
]


def seed_pps_taxonomy(db_path: str = "production_corpus.db") -> Dict[str, int]:
    """Additive idempotent seeding of Course 5 units and topics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, canonical_code FROM courses WHERE id = 5")
    course = cur.fetchone()
    if not course:
        conn.close()
        raise ValueError("Course ID 5 not found in database!")

    cur.execute("SELECT id FROM syllabuses WHERE course_id = 5")
    syl_row = cur.fetchone()
    if syl_row:
        syllabus_id = syl_row[0]
    else:
        cur.execute("INSERT INTO syllabuses (course_id, version) VALUES (5, '2021-Regulation')")
        syllabus_id = cur.lastrowid

    units_created = 0
    topics_created = 0
    concepts_created = 0

    for unit_num, unit_title, topic_list in PPS_CANONICAL_TAXONOMY:
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
                    "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, 'Programming For Problem Solving', 'CANONICAL')",
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
    res = seed_pps_taxonomy()
    print("Course 5 Taxonomy Seeding Result:", res)
