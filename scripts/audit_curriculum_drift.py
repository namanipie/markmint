"""
Deep Architecture and Data Audit for Syllabus / Curriculum Drift Slice.

Analyzes:
1. Database schema and table relationships for Course, Syllabus, Unit, Topic, Question.
2. Mapping coverage across all courses and specifically the 4 canonical courses:
   - Calculus And Linear Algebra (Course 1)
   - Chemistry (Course 2)
   - Programming For Problem Solving (Course 5)
   - Database Management Systems (Course 28)
3. Longitudinal year-by-year topic and unit representation.
4. Statistical sparsity vs true curriculum emergence/disappearance.
5. Distinction between Exam Sampling Drift vs Formal Syllabus Revision.
"""

import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict

def audit():
    conn = sqlite3.connect("production_corpus.db")
    c = conn.cursor()

    print("=" * 80)
    print("SYLLABUS / CURRICULUM DRIFT: ARCHITECTURE & DATA AUDIT")
    print("=" * 80)

    # 1. Database Tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    print(f"\n1. Database Tables ({len(tables)}):")
    print("  " + ", ".join(tables))

    # 2. Overall Questions and Mapping Coverage
    c.execute("SELECT count(*) FROM questions")
    total_q = c.fetchone()[0]

    c.execute("SELECT count(DISTINCT question_id) FROM question_topic")
    mapped_q = c.fetchone()[0]

    c.execute("""
        SELECT count(DISTINCT q.id)
        FROM questions q
        JOIN question_topic qt ON qt.question_id = q.id
        JOIN topics t ON qt.topic_id = t.id
        WHERE t.unit_id IS NOT NULL
    """)
    unit_mapped_q = c.fetchone()[0]

    print(f"\n2. Overall Question Taxonomy Mapping:")
    print(f"  Total Questions:               {total_q}")
    print(f"  Mapped to at least one Topic: {mapped_q} ({mapped_q/total_q*100:.2f}%)")
    print(f"  Mapped to Unit (via Topic):   {unit_mapped_q} ({unit_mapped_q/total_q*100:.2f}%)")
    print(f"  Unmapped Questions (No Unit):  {total_q - unit_mapped_q} ({(total_q - unit_mapped_q)/total_q*100:.2f}%)")

    # 3. Canonical Courses Detailed Audit
    canonical_courses = [
        (1, "Calculus And Linear Algebra"),
        (2, "Chemistry"),
        (5, "Programming For Problem Solving"),
        (28, "Database Management Systems"),
    ]

    print("\n" + "=" * 80)
    print("3. CANONICAL COURSES DETAILED AUDIT")
    print("=" * 80)

    for cid, cname in canonical_courses:
        print(f"\n[{cid}] COURSE: {cname}")
        
        # Course metadata
        c.execute("SELECT code, canonical_code, regulation_year, department FROM courses WHERE id = ?", (cid,))
        code, c_code, reg_yr, dept = c.fetchone()
        print(f"  Code: {code} | Canonical Code: {c_code} | Reg Year: {reg_yr} | Dept: {dept}")

        # Syllabuses
        c.execute("SELECT id, version FROM syllabuses WHERE course_id = ?", (cid,))
        sylls = c.fetchall()
        print(f"  Syllabuses in DB: {sylls}")

        # Units
        c.execute("SELECT u.id, u.number, u.name FROM units u JOIN syllabuses s ON u.syllabus_id = s.id WHERE s.course_id = ? ORDER BY u.number", (cid,))
        units = c.fetchall()
        print(f"  Units ({len(units)}):")
        unit_ids = [u[0] for u in units]
        for u in units:
            # count topics in unit
            c.execute("SELECT count(*) FROM topics WHERE unit_id = ?", (u[0],))
            t_cnt = c.fetchone()[0]
            print(f"    Unit {u[1]}: '{u[2]}' (ID: {u[0]}, Topics: {t_cnt})")

        # Questions in course
        c.execute("""
            SELECT count(q.id)
            FROM exams e
            JOIN sections s ON s.exam_id = e.id
            JOIN questions q ON q.section_id = s.id
            WHERE e.course_id = ?
        """, (cid,))
        tot_course_q = c.fetchone()[0]

        # Questions mapped to topics
        c.execute("""
            SELECT count(DISTINCT q.id)
            FROM exams e
            JOIN sections s ON s.exam_id = e.id
            JOIN questions q ON q.section_id = s.id
            JOIN question_topic qt ON qt.question_id = q.id
            WHERE e.course_id = ?
        """, (cid,))
        mapped_course_q = c.fetchone()[0]
        unmapped_course_q = tot_course_q - mapped_course_q

        print(f"  Total Questions: {tot_course_q} | Mapped to Topics: {mapped_course_q} ({mapped_course_q/tot_course_q*100:.1f}%) | Unmapped: {unmapped_course_q} ({unmapped_course_q/tot_course_q*100:.1f}%)")

        # Exams by year
        c.execute("SELECT e.id, e.year, e.assessment_type FROM exams e WHERE e.course_id = ? ORDER BY e.year, e.id", (cid,))
        exams = c.fetchall()
        year_exams = defaultdict(list)
        for eid, ey, eat in exams:
            year_exams[ey].append((eid, eat))

        print(f"  Exams by Year ({len(exams)} total):")
        for yr in sorted(year_exams.keys(), key=lambda x: (x is None, x)):
            ex_list = year_exams[yr]
            print(f"    Year {yr}: {len(ex_list)} exams -> {ex_list}")

        # Year-by-year Unit and Topic representation
        print(f"  Year-by-Year Unit Representation:")
        c.execute("""
            SELECT e.year, u.number, u.name, count(DISTINCT q.id), sum(q.marks)
            FROM exams e
            JOIN sections s ON s.exam_id = e.id
            JOIN questions q ON q.section_id = s.id
            JOIN question_topic qt ON qt.question_id = q.id
            JOIN topics t ON qt.topic_id = t.id
            JOIN units u ON t.unit_id = u.id
            WHERE e.course_id = ? AND e.year IS NOT NULL
            GROUP BY e.year, u.id
            ORDER BY e.year, u.number
        """, (cid,))
        unit_year_rows = c.fetchall()
        
        # Organize by year
        yr_units = defaultdict(dict)
        for yr, unum, uname, qcnt, qmarks in unit_year_rows:
            yr_units[yr][unum] = (uname, qcnt, qmarks or 0.0)

        for yr in sorted(yr_units.keys()):
            u_dict = yr_units[yr]
            present_units = sorted(u_dict.keys())
            missing_units = [u[1] for u in units if u[1] not in present_units]
            print(f"    Year {yr}: Units present: {present_units} | Missing from exams: {missing_units}")
            for unum in present_units:
                uname, qcnt, qmarks = u_dict[unum]
                print(f"      Unit {unum} ({uname[:30]}): {qcnt} qs, {qmarks:.1f} marks")

        # Topic representation across years
        c.execute("""
            SELECT t.id, t.name, u.number, count(DISTINCT q.id), min(e.year), max(e.year), count(DISTINCT e.year)
            FROM topics t
            JOIN units u ON t.unit_id = u.id
            JOIN syllabuses s ON u.syllabus_id = s.id
            LEFT JOIN question_topic qt ON qt.topic_id = t.id
            LEFT JOIN questions q ON qt.question_id = q.id
            LEFT JOIN sections sec ON q.section_id = sec.id
            LEFT JOIN exams e ON sec.exam_id = e.id AND e.year IS NOT NULL
            WHERE s.course_id = ?
            GROUP BY t.id
            ORDER BY u.number, count(DISTINCT q.id) DESC
        """, (cid,))
        topic_stats = c.fetchall()

        print(f"  Topic Representation Across Years ({len(topic_stats)} topics):")
        topics_zero_q = [ts for ts in topic_stats if ts[3] == 0]
        topics_single_yr = [ts for ts in topic_stats if ts[6] == 1]
        topics_multi_yr = [ts for ts in topic_stats if ts[6] > 1]
        print(f"    Topics with 0 questions in historical exams: {len(topics_zero_q)} / {len(topic_stats)}")
        print(f"    Topics appearing in only 1 year:            {len(topics_single_yr)} / {len(topic_stats)}")
        print(f"    Topics appearing across multiple years:     {len(topics_multi_yr)} / {len(topic_stats)}")
        for tid, tname, unum, qcnt, min_y, max_y, dist_y in topic_stats[:8]:
            print(f"      [Unit {unum}] '{tname[:35]}': {qcnt} qs, Years {min_y}..{max_y} (distinct: {dist_y})")

    conn.close()

if __name__ == '__main__':
    audit()
