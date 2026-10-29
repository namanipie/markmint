import sqlite3

conn = sqlite3.connect("production_corpus.db")
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
for t in tables:
    for fk in c.execute(f"PRAGMA foreign_key_list('{t}')").fetchall():
        if fk[2] == 'concepts':
            print(f"Table {t} references concepts.{fk[3]}")

conn.close()
