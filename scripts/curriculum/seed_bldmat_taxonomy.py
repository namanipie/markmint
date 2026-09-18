"""
Seed script for Course 23: Building Materials in the Built Environment (21CEB101T).

Updates Unit 44 and inserts Units 110-113.
Inserts Topics 439-463.
Also populates the concepts table for completeness.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "production_corpus.db")

UNITS = [
    (44, 23, "Stones, Bricks, Cement and Steel", 1),
    (110, 23, "Paints, Glass, Plastics and Insulating Materials", 2),
    (111, 23, "Building Construction, Fire Safety and Termite Protection", 3),
    (112, 23, "Alternative, Modern and Waste-Based Building Materials", 4),
    (113, 23, "Green Buildings, Ventilation and Environmental Quality", 5),
]

TOPICS = [
    # Unit 1: Stones, Bricks, Cement and Steel (44)
    (439, 44, "Testing and Properties of Building Stones"),
    (440, 44, "Brick Manufacturing, Quality, and Masonry Bonds"),
    (441, 44, "Cement Manufacturing, Chemical Composition, and Bogue's Compounds"),
    (442, 44, "Cement Types, Grades, and Physical Testing"),
    (443, 44, "Structural Timber and Steel (Mild Steel, TMT Bars, and Specific Gravity)"),

    # Unit 2: Paints, Glass, Plastics and Insulating Materials (110)
    (444, 110, "Paints: Composition, Types, and Painting Defects"),
    (445, 110, "Varnishes, Resins, and Distempers"),
    (446, 110, "Types, Composition, and Market Forms of Glass"),
    (447, 110, "Plastics and Polymers in Construction (PVC, Thermoplastics, Thermosets)"),
    (448, 110, "Damp Proofing Courses (DPC) and Thermal Insulating Materials"),

    # Unit 3: Building Construction, Fire Safety and Termite Protection (111)
    (449, 111, "Cavity Wall Construction and Masonry Types"),
    (450, 111, "Staircase Design, Components, and Types of Stairs"),
    (451, 111, "Fire Resisting Properties of Building Materials"),
    (452, 111, "Fire Alarm Systems and Fire Ventilation"),
    (453, 111, "Anti-Termite Treatment and Termite Protection Methods"),

    # Unit 4: Alternative, Modern and Waste-Based Building Materials (112)
    (454, 112, "Ferrocement: Raw Materials, Wire Mesh Reinforcement, and Properties"),
    (455, 112, "Ferrocement Construction Procedure, Applications, and Advantages"),
    (456, 112, "Fly Ash Properties and Soil-Cement Blocks"),
    (457, 112, "Gypsum and Industrial Byproduct Utilization"),
    (458, 112, "Agro-Industrial Waste and Artificial Aggregate Substitutes"),

    # Unit 5: Green Buildings, Ventilation and Environmental Quality (113)
    (459, 113, "Green Building Concepts, Principles, and Zero Energy Buildings"),
    (460, 113, "Green Building Rating Systems and GRIHA Certification"),
    (461, 113, "Natural Ventilation: Wind Effect, Stack Effect, and Ventilators"),
    (462, 113, "Indoor Air Quality (IAQ), Air Pollutants, and AQI"),
    (463, 113, "Waterproofing Materials and Moisture Intrusion Control"),
]


def seed_bldmat_taxonomy():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for unit_id, syllabus_id, name, number in UNITS:
        c.execute("SELECT id FROM units WHERE id = ?", (unit_id,))
        if c.fetchone():
            c.execute(
                "UPDATE units SET syllabus_id = ?, name = ?, number = ? WHERE id = ?",
                (syllabus_id, name, number, unit_id),
            )
            print(f"Updated unit {unit_id}: {name}")
        else:
            c.execute(
                "INSERT INTO units (id, syllabus_id, name, number) VALUES (?, ?, ?, ?)",
                (unit_id, syllabus_id, name, number),
            )
            print(f"Inserted unit {unit_id}: {name}")

    for topic_id, unit_id, name in TOPICS:
        c.execute("SELECT id FROM topics WHERE id = ?", (topic_id,))
        if c.fetchone():
            c.execute(
                "UPDATE topics SET unit_id = ?, name = ? WHERE id = ?",
                (unit_id, name, topic_id),
            )
            print(f"Updated topic {topic_id}: {name}")
        else:
            c.execute(
                "INSERT INTO topics (id, unit_id, name) VALUES (?, ?, ?)",
                (topic_id, unit_id, name),
            )
            print(f"Inserted topic {topic_id}: {name}")

    for topic_id, _, name in TOPICS:
        c.execute("SELECT id FROM concepts WHERE canonical_name = ?", (name,))
        if not c.fetchone():
            c.execute(
                "INSERT INTO concepts (canonical_name, subject, status) VALUES (?, ?, ?)",
                (name, "Building Materials in the Built Environment", "active"),
            )

    conn.commit()
    conn.close()
    print("Seeding Building Materials taxonomy completed successfully.")


if __name__ == "__main__":
    seed_bldmat_taxonomy()
