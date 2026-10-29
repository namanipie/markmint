import sqlite3

conn = sqlite3.connect("production_corpus.db")
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    for fk in c.execute(f"PRAGMA foreign_key_list('{t}')").fetchall():
        if fk[2] == 'topics':
            print(f"Table {t} references topics.{fk[3]}")

# Also check which tables have rows with topic_id in rogue_topic_ids
rogue_topic_ids = [7, 8, 9, 10, 18, 19, 20, 21, 36, 37, 38, 39]
for t in tables:
    cols = [col[1] for col in c.execute(f"PRAGMA table_info('{t}')").fetchall()]
    if 'topic_id' in cols:
        count = c.execute(f"SELECT COUNT(*) FROM {t} WHERE topic_id IN ({','.join(str(i) for i in rogue_topic_ids)})").fetchone()[0]
        if count > 0:
            print(f"Table {t} has {count} rows with rogue topic_id!")
conn.close()
