#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running Alembic schema migrations..."
alembic upgrade head

if [ -f "production_corpus.db" ]; then
    echo "Populating production database from SQLite backup..."
    # The script is idempotent; it skips if data already exists
    python scripts/migrate_sqlite_to_pg.py sqlite:///./production_corpus.db "$DATABASE_URL"
else
    echo "production_corpus.db not present; skipping SQLite backup migration."
fi

echo "Seeding canonical curriculum mappings..."
python scripts/seed_curriculum.py

echo "Build and migration step completed successfully."
