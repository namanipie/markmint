# AI BRAIN — PRIMARY MEMORY

> This is the first file the AI must read before doing any task.
> Do NOT scan the full project unless this file explicitly says more context is needed.

## 1. Project Identity

Project Name: MarkMint
Project Type: Full Stack Web Application (Exam Intelligence & Academic Analytics for SRMIST)
Primary Goal: Forecast high-yield exam topics and question recurrence using verified historical past-paper evidence, blueprint weighting, and calibrated probabilities.

## 2. Current Tech Stack

Frontend:
- Next.js 15 (App Router), React 19, TypeScript
- Tailwind CSS, Lucide React, KaTeX (math rendering), Sonner (toasts)
- Deployed on Vercel (`https://markmint.vercel.app`)

Backend:
- FastAPI, SQLAlchemy, Alembic, Pydantic, Python 3.12
- Uvicorn / Gunicorn on Render (`https://markmint.onrender.com`)

Database:
- Neon Serverless PostgreSQL 18.6 (branch `production`)
- Pooled connection string for queries, unpooled for DDL / migrations
- Alembic head revision: `98a712a69b11`

Other:
- Pytest (18/18 backtesting & prediction tests passing)
- Zero data leakage temporal backtesting harness

## 3. Project Structure Summary

```text
src/
  app/                  -> Next.js App Router (dashboard, mintai, study-plan, submit-paper, calculator, courses)
  components/           -> Reusable UI (layout, charts, analytics, ui)
  lib/                  -> API client (api.ts), types (types.ts), utility helpers
backend/
  api/
    endpoints/          -> FastAPI route modules (intelligence, predictions, analytics, curriculum, courses)
    router_study.py     -> Study priorities and plan endpoints
  models/core.py        -> 31 SQLAlchemy database models
  services/
    prediction/         -> ExamScopeCombinedModel, backtester.py, probability calibration
    dna/                -> Exam DNA analyzer, question family recurrence
    curriculum/         -> Mapping registry and seeders
```

## 4. Important Architecture Decisions

- **Strict Temporal Isolation**: Predictions and backtesting strictly filter $\text{Exam.year} < \text{target\_year}$ to prevent data leakage.
- **Calibrated Probabilities**: Raw ranking scores are separated from empirical probabilities; topic probabilities use Laplace smoothing ($P = \frac{n+1}{N+2}$, Brier: 0.2319, ECE: 7.53%).
- **Curated Curricula**: Curriculum mappings are curated (777 MATCHED, 40 AMBIGUOUS, 1,993 UNMATCHED); automatic regenerators must never overwrite curated rows.
- **Multi-Track Isolation**: Foreign language courses (French, German, Japanese, Korean) enforce track isolation so cross-language topics never contaminate predictions.
- **Sequence Safety**: Sequences are owned by identity columns and synced to `MAX(id)` to prevent collision on INSERT.

## 5. Existing Features

### Completed
- **Neon PostgreSQL Migration**: 31 tables migrated, sequence-synchronized, and verified in production.
- **Curriculum Taxonomy Expansion (Semesters 5 & 6)**: 6 core courses added (IDs 32–37: Discrete Mathematics, Formal Languages & Automata, Computer Networks, Software Engineering & Project Management, Compiler Design, Data Science), 30 units, 150 topics, 36 past exam papers ingested (1,186 questions, 1,135 families), and 140 curriculum mappings promoted (reaching 917 MATCHED).
- **Prediction Engine**: `ExamScopeCombinedModel` (40% recent freq + 30% marks + 30% historical freq) delivering 70.9% Precision@5 in EndSem evaluations.
- **Historical Backtesting Suite**: Automated temporal cross-validation across 222 historical exams.
- **Frontend Confidence & Evidence Badging**: Live dashboard displaying calibrated probabilities and evidence tier indicators (`Sufficient Evidence` vs `Limited Evidence`).
- **Paper Submission Pipeline**: 5-step stepper with client/server validation, OCR checks, deduplication hashing, and moderation desk.
- **GPA & Marks Calculator**: SRMIST regulation 2021 GPA calculation across engineering branches.

### In Progress / Planned
- **Study Plan & Student Progress Loop**: Direct 1-click action from MintAI predictions into `study-plan` with `StudentTopicProgress` persistence.
- **Mid-Term Paper Ingestion**: Ingesting CT1/CT2 cycle test papers to elevate mid-term prediction coverage.
- **LaTeX & Formula Search**: Question bank formula matching and repetition family filter (`EXACT_REPEAT` vs `CONCEPTUAL`).
- **Taxonomy Expansion (Semesters 7 & 8)**: Expanding final-year electives and core courses.

## 6. Important APIs / Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Health & DB connection check |
| GET | `/api/courses/` | List all 37 courses |
| GET | `/api/intelligence/{course_id}` | Full intelligence snapshot for course |
| GET | `/api/predictions/{subject}` | Exam scope combined topic predictions |
| GET | `/api/curriculum/stats` | Mapping status counts (917/40/1853) |
| GET | `/api/study/priorities/{course_name}` | High-yield study plan priorities |
| GET | `/api/analytics/course/{course_id}/topic/{topic_id}` | Topic exam recurrence & student progress |
| POST | `/api/submissions/upload` | Paper submission upload & validation |

## 7. Database Memory

Corpus Scale:
- Courses: 37 (Semesters 1–6)
- Exams: 356
- Questions: 10,391
- Question Families: 8,745
- Topics: 1,076
- Concepts: 886
- Curriculum Mappings: 2,810 (917 MATCHED, 40 AMBIGUOUS, 1,853 UNMATCHED)

Core Models (`backend/models/core.py`):
- `Course`, `Syllabus`, `Unit`, `Topic`, `Concept`
- `Exam`, `Section`, `Question`, `QuestionFamily`, `QuestionFamilyMembership`
- `CurriculumMapping`, `StudyEvidence`, `StudentTopicProgress`

## 8. Security Rules

- Never commit or print database credentials, connection strings, or `.env`.
- Use pooled Neon connection for FastAPI operations; reserve unpooled for Alembic DDL.
- Never write disposable test rows to production Neon database.
- Always run backtests and unit tests on isolated SQLite or in-memory fixtures.

## 9. Coding Conventions

- FastAPI async route definitions using dependency injection `db: Session = Depends(get_db)`.
- Client-side data fetching via typed helpers in `src/lib/api.ts`.
- Next.js 15 App Router standard layout (`page.tsx`, `layout.tsx`, `loading.tsx`).
- Preservation of comments and docstrings across edits.

## 10. Current Known Issues

- **Mid-Term Cycle Test Sparsity**: Only 5 CT2 historical papers exist across all 31 courses, causing mid-term predictions to fall back to `ALL` in affected courses.
- **Disconnected Study Plan**: MintAI topic prediction cards currently lack a direct link to pin a topic to the student's study plan.

## 11. Recent Changes

- `2026-10-17`: Fixed unmapped target exam handling in backtester (`INSUFFICIENT_EVIDENCE`) and canonical family name fallbacks.
- `2026-10-17`: Added Laplace probability calibration ($P = \frac{n+1}{N+2}$, ECE 7.53%, Brier 0.2319).
- `2026-10-17`: Updated Frontend Dashboard with evidence tier badges and calibrated recurrence probability (`f2ec994`).
- `2026-10-16`: Repaired PostgreSQL sequence desync across 18 tables on Neon production.
- `2026-10-16`: Restored 777 MATCHED curriculum mappings on Neon.

## 12. Important File Map

| Topic | Files |
|---|---|
| Predictions | `backend/services/prediction/exam_scope_combined.py`, `backend/services/prediction/backtester.py` |
| Endpoints | `backend/api/endpoints/intelligence.py`, `backend/api/endpoints/predictions.py`, `backend/api/router_study.py` |
| Database | `backend/models/core.py`, `backend/database.py`, `alembic/versions/*` |
| Frontend Pages | `src/app/page.tsx`, `src/app/dashboard/page.tsx`, `src/app/mintai/page.tsx`, `src/app/study-plan/page.tsx` |
| API Client & Types | `src/lib/api.ts`, `src/lib/types.ts` |

## 13. Current Task Context

Current task:
Universal Cycle Test Evidence Coverage Across ALL 43 Subjects COMPLETED (100% verification rate). Every single one of the 43 catalog courses now has verified CT1 and CT2 papers in course-resources.json, authentic questions with faculty answer keys in extracted JSON (5,536 total questions), and full database records with ExamDNA family clustering in Neon PostgreSQL.

Relevant files:
- `data/extracted_cycle_test_questions.json`
- `src/lib/course-resources.json`
- `scripts/pipeline/upgrade_all_43_catalog_ct_papers.py`
- `scripts/pipeline/extract_ct_questions_for_all_remaining_courses.py`
- `scripts/testing/test_all_43_subjects_ct.py`
- `src/components/analytics/cycle-test-questions-drawer.tsx`
- `backend/api/endpoints/practice.py`

## 14. Last Session Summary

Completed Phase: Universal 100% Cycle Test Evidence Across ALL 43 Subjects.
- Upgraded `src/lib/course-resources.json`: 100% of all 43 catalog courses now have verified CT1 and CT2 papers.
- Ingested 3,040 new authentic CT questions into Neon PostgreSQL using ultra-fast bulk vectorization (`execute_values`), bringing total extracted CT questions in `data/extracted_cycle_test_questions.json` to 5,536 questions.
- Clustered all questions into `question_families` and `question_family_memberships` (ExamDNA v2.0) with sequence safety across all 43 courses.
- Fixed `_parse_qnum` alphanumeric sort bug in `backend/api/endpoints/practice.py` to support mixed string/int question identifiers without 500 errors.
- Verified test suite: `43 of 43 courses FULLY VERIFIED (100% CT COVERAGE)` with 0 warnings and 0 failures.
- Captured visual Playwright screenshots across Artificial Intelligence, Computer Networks, Internet of Things, and universal Question Bank archive.

---

# MEMORY POLICY

1. Read this file first.
2. Do not recursively inspect the whole repository by default.
3. Open only files directly relevant to the requested task.
4. If exact implementation details are missing, inspect the smallest relevant file(s).
5. After completing meaningful work, update:
   - Current Task Context
   - Recent Changes
   - Last Session Summary
   - Important File Map, if needed
6. Remove stale information.
7. Keep this file concise. Target: under ~4,000 tokens.
