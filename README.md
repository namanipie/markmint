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
  <p>
    <a href="https://markmint.vercel.app">View Live Demo</a>
    ·
    <a href="https://github.com/namanipie/markmint/issues">Report Bug</a>
  </p>
</div>

---

### ✨ Features
* **MintAI Engine:** Generates high-confidence exam predictions using exponential decay recency-weighting algorithms.
* **ExamDNA Dashboard:** Visualizes topic weights, mark distributions, and cognitive level mappings over historical data.
* **Premium UI/UX:** Fully responsive, dark-mode optimized interface featuring interactive 3D elements and cinematic Easter eggs.
* **Strictly Decoupled Architecture:** Clean separation between the Next.js frontend and the robust Python FastAPI extraction engine.

---

MarkMint is a deterministic exam-intelligence platform designed to ingest raw university examination papers and study materials, extract structured metadata, and generate high-confidence predictions using historical ExamDNA and MintAI prediction models.

## Intelligence Stack

MarkMint operates on a strictly decoupled, highly precise intelligence pipeline:

1. **Document Ingestion (`scripts/scrape.py` & `scripts/ingest.py`)**: Raw historical exams and study materials (PDFs) are scraped and ingested.
2. **Document Understanding (`backend/services/extraction`)**: Deterministic OCR (with rigorous math/scan fallbacks) and semantic extraction identify strict boundaries for Questions and Concepts.
3. **Subject-Isolated Classification (`backend/services/question_classifier.py`)**: Uses SentenceTransformers to map questions to canonical course topics. Enforces a strict minimum confidence threshold (`0.45` cosine similarity) and course-isolation to prevent cross-contamination (e.g., Biology concepts mapped to Calculus questions).
4. **Question Families**: Aggregates semantically identical or structurally similar questions over time.
5. **ExamDNA (`backend/api/endpoints/analysis.py`)**: Computes topic weights, mark distributions, and cognitive level mappings over historical data.
6. **MintAI Predictions**: Employs exponential decay recency-weighting algorithms to predict upcoming exam structures without hallucination.
7. **Frontend (`src/app`)**: A responsive Next.js web application for students and educators to explore predictions, study DNA, and track trends.

## Architecture

* **Frontend**: Next.js (App Router), Tailwind CSS
* **Backend**: FastAPI (Python 3.14+)
* **Database**: PostgreSQL (Production) / SQLite (Local/Testing) via SQLAlchemy
* **ML Layer**: Local `sentence-transformers` for precise classification.
* **Extraction**: PyMuPDF (`fitz`), `easyocr` (with structural math gating)

## Local Development

### 1. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # Unix

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend
cd backend
uvicorn main:app --reload
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Run Next.js frontend
npm run dev
```

Navigate to [http://localhost:3000](http://localhost:3000) to view the application.

### 3. Data Pipeline Execution

The data pipeline is decoupled from the web server. Run these scripts manually or via cron to populate the database:

```bash
# 1. Scrape raw PDFs
python scripts/scrape.py

# 2. Extract and classify data (idempotent)
python scripts/ingest.py

# 3. Synchronize canonical topics safely
python scripts/sync_topics.py

# 4. Final subject-aware question classification
python scripts/classify_questions.py
```

## Core Philosophy

* **High Precision > High Coverage**: MarkMint refuses to force classifications. If a question doesn't map to a syllabus topic with high confidence, it remains unresolved. It is better to have 150 accurately classified questions than 350 polluted ones.
* **Deterministic Output**: MintAI predictions rely solely on mathematical extrapolation of historical ExamDNA. Generative AI is NEVER used to hallucinate topics, questions, or predictions. 
* **Data Isolation**: The pipeline guarantees subject boundaries. Chemistry topics will never bleed into Philosophy exams.

## License

Private Repository. All rights reserved.
