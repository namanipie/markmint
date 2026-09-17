#!/bin/bash
set -e

# Ensure repository root is on PYTHONPATH for all Python invocations
export PYTHONPATH=".:$PYTHONPATH"

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running Alembic schema migrations..."
alembic upgrade head


echo "Seeding canonical curriculum mappings..."
python -m scripts.curriculum.seed_curriculum

echo "Build and migration step completed successfully."
