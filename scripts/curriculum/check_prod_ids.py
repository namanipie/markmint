import os
import re
from sqlalchemy import create_engine, text

with open('scripts/verify_production_smoke.py', 'r') as f:
    match = re.search(r'postgresql://[^\"]+', f.read())
    url = match.group(0).replace("postgresql://", "postgresql+psycopg2://")

engine = create_engine(url)
with engine.connect() as conn:
    print('Max Unit ID in Prod:', conn.execute(text('SELECT max(id) FROM units')).scalar())
    print('Max Topic ID in Prod:', conn.execute(text('SELECT max(id) FROM topics')).scalar())
    print('Max Concept ID in Prod:', conn.execute(text('SELECT max(id) FROM concepts')).scalar())
    print('Unit count in Prod:', conn.execute(text('SELECT count(*) FROM units')).scalar())
    print('Topic count in Prod:', conn.execute(text('SELECT count(*) FROM topics')).scalar())
    units = conn.execute(text('SELECT id, syllabus_id, number, name FROM units ORDER BY id')).fetchall()
    print('Existing units in Prod:')
    for u in units:
        print(f'  Unit {u[0]}: syllabus={u[1]}, num={u[2]}, name={u[3]}')
