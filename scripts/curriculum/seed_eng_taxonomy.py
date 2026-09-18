"""
Seed script for Course 15: Communicative English (21LEH101T).

Updates Unit 36 and inserts Units 114-117.
Inserts Topics 464-488.
Also populates the concepts table for completeness.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "production_corpus.db")

UNITS = [
    (36, 15, "Fundamentals of Communication and Listening Skills", 1),
    (114, 15, "Grammar and Vocabulary in Context", 2),
    (115, 15, "Professional Correspondence and Mechanics of Writing", 3),
    (116, 15, "Institutional Documents, Reports and Proposals", 4),
    (117, 15, "Presentation Skills, Academic Integrity and Workplace Ethics", 5),
]

TOPICS = [
    # Unit 1: Fundamentals of Communication and Listening Skills (36)
    (464, 36, "Communication Process, Channels, and Models"),
    (465, 36, "Barriers to Effective Communication"),
    (466, 36, "Types of Listening (Active, Passive, Critical, Empathetic)"),
    (467, 36, "Listening Comprehension, Reading Techniques, and Note-Taking"),
    (468, 36, "Non-Verbal Communication (Kinesics, Proxemics, Paralanguage)"),

    # Unit 2: Grammar and Vocabulary in Context (114)
    (469, 114, "Subject-Verb Agreement (Concord)"),
    (470, 114, "Tenses, Aspects, and Conditional Clauses"),
    (471, 114, "Active and Passive Voice Transformations"),
    (472, 114, "Direct and Indirect (Reported) Speech"),
    (473, 114, "Degrees of Comparison, Conjunctions, and Question Tags"),

    # Unit 3: Professional Correspondence and Mechanics of Writing (115)
    (474, 115, "Mechanics of Writing (Punctuation, Capitalization, Parallelism)"),
    (475, 115, "Paragraph Development, Topic Sentences, and Précis Writing"),
    (476, 115, "Formal Letters (Inquiry, Complaint, Permission)"),
    (477, 115, "Professional E-mail Writing and Netiquette"),
    (478, 115, "Resume, Curriculum Vitae (CV), and Job Applications"),

    # Unit 4: Institutional Documents, Reports and Proposals (116)
    (479, 116, "Notice, Agenda, and Minutes of Meetings"),
    (480, 116, "Technical and Business Report Writing"),
    (481, 116, "Project Proposal Writing and Feasibility Studies"),
    (482, 116, "Transcoding: Information Transfer from Charts/Graphs to Text"),
    (483, 116, "Technical Vocabulary, Synonyms, Antonyms, and Word Formation (Prefixes/Suffixes)"),

    # Unit 5: Presentation Skills, Academic Integrity and Workplace Ethics (117)
    (484, 117, "Public Speaking, Speech Delivery, and Audience Analysis"),
    (485, 117, "Group Discussion (GD) Techniques and Leadership"),
    (486, 117, "Presentation Skills, Visual Aids, and Slide Design"),
    (487, 117, "Academic Integrity, Plagiarism, Paraphrasing, and Referencing"),
    (488, 117, "Workplace Ethics, Interpersonal Skills, Synchronous and Asynchronous Communication"),
]


def seed_eng_taxonomy():
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
                (name, "Communicative English", "active"),
            )

    conn.commit()
    conn.close()
    print("Seeding Communicative English taxonomy completed successfully.")


if __name__ == "__main__":
    seed_eng_taxonomy()
