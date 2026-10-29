import sqlite3

c = sqlite3.connect('production_corpus.db')
c_bak = sqlite3.connect('production_corpus.db.pre_full_ingest_backup_20260917_140107')

# Restore original mappings for the 12 clobbered CSE rows
for row_id in [745, 794, 842, 891, 940, 988, 1036, 1085, 1135, 1184, 1282, 2659]:
    orig = c_bak.execute('SELECT course_id, status, notes FROM curriculum_mappings WHERE id = ?', (row_id,)).fetchone()
    c.execute('UPDATE curriculum_mappings SET course_id = ?, status = ?, notes = ? WHERE id = ?', (orig[0], orig[1], orig[2], row_id))

# Row 1233 is Fundamentals of Economics in Computer Science and Business Systems
c.execute("UPDATE curriculum_mappings SET course_id = 6, status = 'MATCHED', notes = 'Fundamentals of Economics matched to course 6 (18MSS101T)' WHERE id = 1233")
c.commit()

# Verify counts
calc_cnt = c.execute('SELECT count(*) FROM curriculum_mappings WHERE course_id = 1').fetchone()[0]
spcm_cnt = c.execute('SELECT count(*) FROM curriculum_mappings WHERE course_id = 13').fetchone()[0]
foe_cnt = c.execute('SELECT count(*) FROM curriculum_mappings WHERE course_id = 6').fetchone()[0]
print(f"Repaired local SQLite: calc={calc_cnt}, spcm={spcm_cnt}, foe={foe_cnt}")
