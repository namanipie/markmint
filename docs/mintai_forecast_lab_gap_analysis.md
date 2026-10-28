# MintAI Forecast Lab: Gap Analysis & Reconnaissance Report

## 1. Executive Summary

This report establishes the baseline architecture, empirical performance, and gaps of the existing MintAI forecasting pipeline prior to Phase 1 upgrades.

MarkMint's prediction system is designed to provide SRMIST engineering students with probabilistic, evidence-based forecasts of upcoming examination topics and recurring question families. This audit validates that temporal isolation is architecturally present, but identifies critical gaps in metric coverage (missing NDCG, abstention rates), missing baselines (blueprint weighting), empirical underperformance of the combined model relative to simple baselines, and absent frontend exposure of rigorous held-out validation evidence.

---

## 2. Reconnaissance & Current Architecture

### 2.1 Codebase & Data Model Discovery
- **Prediction Engine**: `backend/services/prediction/engine.py` implements:
  - `BaseModel`: Abstract class providing `_rank_and_format()` with Laplace probability calibration `(papers_with_topic + 1) / (sample_papers + 2)`.
  - `AllTimeFrequencyBaseline`: Topics ranked by historical frequency $f_{hist}$.
  - `RecentFrequencyBaseline`: Topics ranked by recent 2-year frequency $f_{recent}$.
  - `RecencyWeightedBaseline`: Topics ranked by $0.7 \cdot f_{recent} + 0.3 \cdot f_{hist}$.
  - `MarksWeightedBaseline`: Topics ranked by mark share $\sum \text{marks}_{topic} / \text{total marks}$.
  - `FamilyRecurrenceBaseline`: Question families ranked by $0.5 \cdot \text{occurrences} + 0.5 \cdot \text{recent}$.
  - `ExamScopeCombinedModel`: Production model combining $0.4 \cdot f_{recent} + 0.3 \cdot \text{marks\_weight} + 0.3 \cdot f_{hist}$.
- **Temporal Repository**: `backend/services/prediction/repository.py`
  - Restricts candidate historical exams strictly to $\text{Exam.year} < \text{cutoff\_year}$.
- **DNA Analyzer**: `backend/services/dna/analyzer.py`
  - Extracts empirical topic distributions, unit focus, question types, and repetition patterns.
- **Backtesting Engine**: `backend/services/prediction/backtester.py`
  - `BacktestHarness` evaluates historical exams year-by-year across courses.
- **FastAPI Endpoints**:
  - `GET /predictions/{subject}` in `backend/api/endpoints/predictions.py`.
  - `GET /model-performance` in `backend/api/endpoints/intelligence.py`.
- **Frontend Presentation**:
  - `src/app/dashboard/page.tsx` (MintAI Forecast Dashboard) renders top-ranked forecast items, probability percentages, and citations.

---

## 3. Baseline Empirical Evaluation & Gap Analysis

From the historical run across 31 courses and 214 mapped target exams (`data/reports/backtest_results.json`):

| Model | Precision@3 | Precision@5 | Precision@10 | Recall@5 | Marks Coverage@5 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **AllTimeFrequencyBaseline** | 66.82% | 61.87% | 54.91% | 33.34% | 33.12% |
| **RecentFrequencyBaseline** | 68.54% | 63.93% | 55.14% | 33.91% | 33.57% |
| **RecencyWeightedBaseline** | **68.69%** | **63.36%** | **55.23%** | 33.42% | 33.15% |
| **MarksWeightedBaseline** | 63.86% | 61.31% | 53.74% | 33.04% | 37.35% |
| **ExamScopeCombinedModel (Current)** | 67.29% | 62.43% | 55.28% | 33.17% | 37.40% |

### Key Diagnostic Findings:
1. **Current Production Model Underperforms Simple Recency**:
   `RecencyWeightedBaseline` (68.69% P@3) and `RecentFrequencyBaseline` (63.93% P@5) outperform `ExamScopeCombinedModel` (67.29% P@3, 62.43% P@5). The arbitrary inclusion of $0.3 \times \text{marks\_weight}$ introduces noise into topic rank ordering because high-mark topics are not always the most frequently recurring.
2. **Missing NDCG@K Metric**:
   The current harness only evaluates set-based Precision and Recall; it does not measure whether the most important topics appear at ranks 1–3 versus 4–5.
3. **Missing Blueprint-Weighted Baseline**:
   Although `backend/services/dna/blueprint.py` extracts exam blueprints, blueprint unit/section weighting has not been benchmarked as an explicit prediction baseline.
4. **Missing Formal Abstention / Coverage Statistics**:
   When historical evidence is sparse, the system should compute coverage and abstention rates rather than forcing arbitrary low-confidence rankings.
5. **Frontend Disconnect**:
   The MintAI dashboard displays probability cards but provides no trustworthy held-out accuracy metrics or empirical evidence badges (e.g. "Validated 71% Precision@5 across past 4 exam cycles").

---

## 4. Phase-by-Phase Implementation Plan

1. **Phase 1: Leakage-Safe Historical Evaluation Harness**:
   - Enhance `backend/services/prediction/backtester.py` with rolling-origin temporal isolation.
   - Guard against indirect leaks (target questions in family memberships, cross-track leaks).
   - Add CLI interface (`scripts/run_forecast_lab.py`).
2. **Phase 2: Metrics and Baselines**:
   - Implement `NDCG@K`, Abstention Rate, and Mark-weighted NDCG in `BacktestEvaluator`.
   - Implement `BlueprintWeightedBaseline` and component ablations.
   - Generate detailed JSON and Markdown evaluation artifacts with per-course disaggregation.
3. **Phase 3: Algorithm Improvement**:
   - Formulate candidate model: Evidence-aware and blueprint-calibrated combination that outperforms `RecencyWeightedBaseline` on held-out validation.
   - Preserve original `ExamScopeCombinedModel` as an exact baseline.
4. **Phase 4: API & Frontend Integration**:
   - Extend `/predictions/{subject}` and `/model-performance` schemas.
   - Add a clean, responsive "Model Performance & Validation Evidence" section in `src/app/dashboard/page.tsx`.
5. **Phase 5 & 6: Automated Testing & Verification**:
   - Comprehensive test suite covering leakage, determinism, NDCG math, edge cases.
   - Production Next.js build verification.
