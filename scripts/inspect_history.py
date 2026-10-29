import sqlite3
import os

db_path = os.path.expandvars(r"%TEMP%\history_copy.sqlite")
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT url, title, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') as dt FROM urls ORDER BY last_visit_time DESC LIMIT 30")
for row in cur.fetchall():
    print(f"{row[2]} | {row[1]} | {row[0]}")
conn.close()
