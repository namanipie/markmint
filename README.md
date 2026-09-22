<div align="center">
  <img src="https://img.shields.io/badge/Next.js-Black?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</div>

<br />

<div align="center">
  <h2>🍃 MarkMint</h2>
  <p><strong>A deterministic exam-intelligence platform built for SRMIST students.</strong></p>
<p><strong>MarkMint v1.0 – First-Year Release</strong></p>
<p>Stable production release. See <a href="CHANGELOG.md">CHANGELOG.md</a> for details.</p>
  <p>
    <a href="https://markmint.vercel.app">View Live Demo</a>
    ·
    <a href="https://github.com/namanipie/markmint/issues">Report Bug</a>
  </p>
</div>

---

MarkMint is a deterministic exam-intelligence platform designed to ingest raw university examination papers and study materials, extract structured metadata, and generate high-confidence predictions using historical ExamDNA and MintAI prediction models.

## Architecture

MarkMint operates on a strictly decoupled, highly precise intelligence pipeline:

* **Frontend**: Next.js (App Router), Tailwind CSS
* **Backend**: FastAPI (Python 3.14+)
* **Database**: PostgreSQL (Production) / SQLite (Local/Testing) via SQLAlchemy
* **ML Layer**: Local `sentence-transformers` for precise classification.
* **Extraction**: PyMuPDF, `easyocr` (with structural math gating)

## Repository Structure

Please see [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for a comprehensive breakdown of the repository layout.

## Local Development

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Unix: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend
cd backend
uvicorn main:app --reload
```

### Frontend

```bash
# Install dependencies
npm install

# Run Next.js frontend
npm run dev
```

Navigate to http://localhost:3000 to view the application.

## Database

MarkMint uses SQLAlchemy and Alembic for migrations.
```bash
# Run migrations
alembic upgrade head
```

## Crawling / Ingestion

The data pipeline is decoupled from the web server. Run these scripts from the root directory manually or via cron:

```bash
# 1. Scrape raw PDFs
python scripts/crawler/scrape.py

# 2. Extract and classify data
python scripts/ingestion/ingest.py

# 3. Synchronize canonical topics safely
python scripts/utilities/sync_topics.py
```

## Testing

Backend tests are written in Pytest.
```bash
# Run backend service tests
pytest backend/tests/ -v

# Run integration and crawler tests
pytest tests/ -v
```

## Deployment

* **Frontend**: Deployed to Vercel automatically upon pushing to the `main` branch.
* **Backend**: Deployed to Render. Configured via `render_build.sh` and `run.sh`.
