import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal, engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")).fetchall()
        print('Postgres tables count:', len(tables))
        for t in tables:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{t[0]}"')).scalar()
            print(f'  {t[0]}: {count}')
except Exception as e:
    print('Error connecting to DB:', e)
