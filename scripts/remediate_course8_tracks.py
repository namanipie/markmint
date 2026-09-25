"""
Remediates Course 8 track isolation in production_corpus.db:
1. Corrects Exam 62 track_id from 5 (Korean) to 1 (German).
2. Populates QuestionFamily.track_id for all Course 8 families from their member questions' exam track.
3. Ensures all single-track/trackless courses retain track_id = NULL.
4. Verifies all integrity invariants.
"""

import sqlite3
import sys

con = sqlite3.connect('production_corpus.db')
cur = con.cursor()

try:
    print("=== COMMENCING TRACK REMEDIATION ===")
    
    # 1. Update Exam 62 track_id to 1 (German)
    cur.execute("SELECT track_id FROM exams WHERE id = 62")
    prev_track = cur.fetchone()[0]
    print(f"Exam 62 track_id before: {prev_track}")
    
    cur.execute("UPDATE exams SET track_id = 1 WHERE id = 62")
    print("Updated Exam 62 track_id to 1 (German)")
    
    # 2. Check for any remaining cross-track questions in any family
    cur.execute('''
        SELECT m.family_id, COUNT(DISTINCT e.track_id) as t_cnt, GROUP_CONCAT(DISTINCT e.track_id) as tracks
        FROM question_family_memberships m
        JOIN questions q ON m.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        GROUP BY m.family_id
        HAVING t_cnt > 1
    ''')
    remaining_cross = cur.fetchall()
    if remaining_cross:
        raise ValueError(f"Aborting: found remaining cross-track families: {remaining_cross}")
    print("Verified: 0 families contain questions from multiple tracks.")
    
    # 3. Populate track_id on question_families for Course 8
    cur.execute('''
        SELECT DISTINCT qf.id, e.track_id
        FROM question_families qf
        JOIN questions q ON qf.id = q.family_id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.course_id = 8 AND e.track_id IS NOT NULL
    ''')
    fam_tracks = cur.fetchall()
    print(f"Populating track_id for {len(fam_tracks)} Course 8 families...")
    
    for fid, tid in fam_tracks:
        cur.execute("UPDATE question_families SET track_id = ? WHERE id = ?", (tid, fid))
        
    # Verify no non-Course-8 families have track_id set
    cur.execute('''
        SELECT COUNT(*)
        FROM question_families qf
        WHERE qf.track_id IS NOT NULL AND qf.subject != 'Foreign Languages'
    ''')
    invalid_non_c8 = cur.fetchone()[0]
    if invalid_non_c8 > 0:
        raise ValueError(f"Aborting: non-Course-8 families have track_id set: {invalid_non_c8}")
        
    con.commit()
    print("Remediation committed successfully.")
    
    # 4. Invariant checks
    print("\n=== POST-REMEDIATION VERIFICATION ===")
    
    cur.execute("SELECT COUNT(*) FROM question_families")
    total_fams = cur.fetchone()[0]
    print(f"Total QuestionFamilies: {total_fams} (expected: 7450)")
    assert total_fams == 7450, f"Expected 7450 families, got {total_fams}"
    
    cur.execute("SELECT COUNT(*) FROM question_family_memberships")
    total_mems = cur.fetchone()[0]
    print(f"Total Memberships: {total_mems} (expected: 9013)")
    assert total_mems == 9013, f"Expected 9013 memberships, got {total_mems}"
    
    cur.execute("SELECT COUNT(*) FROM questions WHERE family_id IS NULL")
    unassigned = cur.fetchone()[0]
    print(f"Questions without family: {unassigned} (expected: 0)")
    assert unassigned == 0
    
    cur.execute('''
        SELECT COUNT(*) FROM questions q
        LEFT JOIN question_family_memberships m ON q.id = m.question_id
        WHERE m.id IS NULL
    ''')
    no_mem = cur.fetchone()[0]
    print(f"Questions without membership: {no_mem} (expected: 0)")
    assert no_mem == 0
    
    cur.execute('''
        SELECT question_id, COUNT(*) FROM question_family_memberships
        GROUP BY question_id HAVING COUNT(*) > 1
    ''')
    multi_mem = len(cur.fetchall())
    print(f"Questions with multiple memberships: {multi_mem} (expected: 0)")
    assert multi_mem == 0
    
    # Cross-course check
    cur.execute('''
        SELECT m.family_id, COUNT(DISTINCT e.course_id) as c_cnt
        FROM question_family_memberships m
        JOIN questions q ON m.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        GROUP BY m.family_id
        HAVING c_cnt > 1
    ''')
    cross_course = len(cur.fetchall())
    print(f"Cross-course families: {cross_course} (expected: 0)")
    assert cross_course == 0
    
    # Cross-track check
    cur.execute('''
        SELECT m.family_id, COUNT(DISTINCT e.track_id) as t_cnt
        FROM question_family_memberships m
        JOIN questions q ON m.question_id = q.id
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        WHERE e.track_id IS NOT NULL
        GROUP BY m.family_id
        HAVING t_cnt > 1
    ''')
    cross_track = len(cur.fetchall())
    print(f"Cross-track families: {cross_track} (expected: 0)")
    assert cross_track == 0
    
    # Every Course 8 question's exam track equals its family's track
    cur.execute('''
        SELECT COUNT(*)
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN question_families qf ON q.family_id = qf.id
        WHERE e.course_id = 8 AND (e.track_id != qf.track_id OR qf.track_id IS NULL)
    ''')
    mismatched_c8 = cur.fetchone()[0]
    print(f"Course 8 questions with exam.track_id != family.track_id: {mismatched_c8} (expected: 0)")
    assert mismatched_c8 == 0
    
    # Course 8 breakdown by track
    cur.execute('''
        SELECT qf.track_id, ct.track_name, COUNT(DISTINCT qf.id)
        FROM question_families qf
        JOIN course_tracks ct ON qf.track_id = ct.id
        WHERE qf.subject = 'Foreign Languages'
        GROUP BY qf.track_id, ct.track_name
        ORDER BY qf.track_id
    ''')
    print("\nCourse 8 families by track_id:")
    track_counts = {}
    for tid, tname, cnt in cur.fetchall():
        track_counts[tname] = cnt
        print(f"  Track {tid} ({tname}): {cnt} families")
        
    assert track_counts.get("German") == 180, f"Expected 180 German families, got {track_counts.get('German')}"
    assert track_counts.get("French") == 172, f"Expected 172 French families, got {track_counts.get('French')}"
    assert track_counts.get("Spanish") == 54, f"Expected 54 Spanish families, got {track_counts.get('Spanish')}"
    assert track_counts.get("Japanese") == 129, f"Expected 129 Japanese families, got {track_counts.get('Japanese')}"
    assert track_counts.get("Korean") == 171, f"Expected 171 Korean families, got {track_counts.get('Korean')}"
    assert track_counts.get("Chinese") == 91, f"Expected 91 Chinese families, got {track_counts.get('Chinese')}"
    
    c8_total = sum(track_counts.values())
    print(f"Total Course 8 families: {c8_total} (expected: 797)")
    assert c8_total == 797
    
    # Verify the 20 previously leaking families
    known_20 = [2227, 2228, 2234, 2235, 2236, 2240, 2242, 2245, 2246, 2247, 2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257]
    cur.execute(f"SELECT id, track_id FROM question_families WHERE id IN ({','.join(map(str, known_20))})")
    rows = cur.fetchall()
    print(f"\nStatus of the 20 previously leaking families: {len(rows)} checked")
    for fid, tid in rows:
        assert tid == 1, f"Family {fid} has track_id {tid}, expected 1 (German)"
    print("All 20 families are now strictly Track 1 (German) with ZERO cross-track questions.")

    print("\nALL INVARIANTS SATISFIED.")

finally:
    con.close()
