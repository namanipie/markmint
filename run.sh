#!/bin/bash
set -e

export PYTHONPATH=".:$PYTHONPATH"

echo "Running Alembic schema migrations..."
alembic upgrade head

echo "Starting MarkMint FastAPI server in production mode..."
exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers
