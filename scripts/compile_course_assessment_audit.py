import sqlite3

con = sqlite3.connect("production_corpus.db")
cur = con.cursor()

cur.execute("""
SELECT c.id, c.canonical_code, c.name, c.department, c.regulation_year, s.version
FROM courses c
LEFT JOIN syllabuses s ON s.course_id = c.id
ORDER BY c.id
""")
courses = cur.fetchall()

print(f"Total courses: {len(courses)}")
for c in courses:
    cid, code, name, dept, reg, s_ver = c
    # Check exams for this course
    cur.execute("SELECT DISTINCT assessment_type FROM exams WHERE course_id = ?", (cid,))
    raw_types = [r[0] for r in cur.fetchall() if r[0] is not None]
    
    # Check units for this course
    cur.execute("""
    SELECT u.number, u.name 
    FROM units u
    JOIN syllabuses s ON u.syllabus_id = s.id
    WHERE s.course_id = ?
    ORDER BY u.number
    """, (cid,))
    units = cur.fetchall()
    unit_nums = [u[0] for u in units]
    
    print(f"\nCourse {cid}: {code} - {name} (Reg {reg})")
    print(f"  Raw Assessment Types in DB: {raw_types}")
    print(f"  Units Count: {len(units)}, Numbers: {unit_nums}")
