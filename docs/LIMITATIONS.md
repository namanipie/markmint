# MarkMint Intelligence: System Limitations & Boundaries

MarkMint provides empirical, evidence-based academic intelligence derived from historical examination papers and curriculum catalogs. It is designed to assist student revision planning through chronological pattern detection, NOT to guarantee exam questions.

---

## 1. What MarkMint Cannot Currently Know

1. **Unseen Teacher / Setter Bias**:
   - Examination setters change between terms, departments, and academic cycles. A new instructor may emphasize entirely different chapters or introduce novel application problems absent from historical papers.
2. **Sudden Institutional Curriculum or Regulation Shifts**:
   - When an institution updates regulations (e.g., transitioning from Regulation 2018 to Regulation 2021), module weightings, credit allocations, and textbook editions shift discontinuously. MarkMint detects historical trends within cataloged courses but cannot infer unannounced syllabus modifications.
3. **Non-Indexed Elective Papers & Variant Syllabi**:
   - Department elective tracks, special topic courses, and honors modules often lack standardized archival repositories. If historical papers have not been indexed into MarkMint's registry, the system operates in `CATALOG_ONLY` or `UNMATCHED` modes and refuses speculative synthesis.
4. **Unannounced Pattern Changes & Format Swaps**:
   - Emergency or restructured evaluation formats (e.g., surprise MCQ-only tests, open-book transitions, shortened midterm papers) cannot be deduced from standard 100-mark historical terminal formats.

---

## 2. Conditions That Break or Invalidate Predictions

1. **0-Exam Cold Start (`CATALOG_ONLY`)**:
   - When a course is cataloged in the academic registry but zero past question papers exist in the database, the model cannot produce topic rankings. In this state, MarkMint strictly surfaces catalog metadata and sets `data_availability_status: CATALOG_ONLY`.
2. **1-Exam Limited Sample (`INSUFFICIENT_EVIDENCE`)**:
   - When only a single historical examination paper is present, recurrence cannot be observed (sample size $N=1$). Any mathematical frequency is an artifact of that specific exam's selection rather than a recurring curriculum priority. MarkMint explicitly gates confidence and flags `sufficiency: INSUFFICIENT`.
3. **New Syllabus Regulations & Course Re-codings**:
   - When course codes change (e.g., `18MAB101T` to `21MAB101T`), topic namespaces may diverge. MarkMint's canonical curriculum reconciliation bridges known equivalents, but novel units break historical continuity.
4. **Extreme Topic Drift & Discontinued Chapters**:
   - If a topic appeared heavily in 2019-2021 but was excised from current textbooks, frequency-only models will erroneously score it high. MarkMint mitigates this using recency weighting ($\lambda = 0.85$), but human syllabus inspection remains necessary.

---

## 3. Empirical Past Frequency vs. Future Certainty

- **Empirical Frequency is Descriptive, Not Prescriptive**:
  - A topic recurrence probability of $85\%$ means: *"In historical papers matching this course, questions mapping to this topic appeared in approximately $85\%$ of analyzed examination cycles."*
  - It does **not** mean: *"There is an $85\%$ chance this question appears tomorrow."*
- **The Gambler's Fallacy & Anti-Recurrence**:
  - Examiners frequently avoid repeating the exact problem from the immediately preceding semester. MarkMint's `gap_penalty` and `repetition_type` analysis capture whether a question family repeats cyclically or alternated across semesters.
- **Laplace Smoothing ($k=1$)**:
  - All topic probabilities incorporate Laplace pseudo-counts ($\alpha=1, \beta=2$) to ensure no topic is estimated at $0.00$ or $1.00$, preserving mathematical humility in all output distributions.

---

## 4. Why High Confidence on 1 Paper is Meaningless (Sample Size Gating)

- **The Single-Sample Illusion**:
  - On a single 5-question paper, a topic covering 2 questions might represent $40\%$ of the marks. Without sample gating, a naive model would assign maximum priority and $100\%$ confidence to that topic.
- **Sample Gating Architecture**:
  - MarkMint enforces strict sample size tiers in `backend/services/dna/analyzer.py`:
    - **$N < 2$ papers**: `INSUFFICIENT` data. Model outputs are suppressed or capped at baseline prior probabilities. Confidence is clamped to `0.20` or marked uncalibrated.
    - **$2 \le N < 4$ papers**: `LIMITED` data. Predictions are generated with explicit warnings and conservative confidence scores ($\le 0.60$).
    - **$N \ge 4$ papers**: `SUFFICIENT` data. Multi-year walk-forward validation and trend analysis are activated.
- **Confidence vs. Priority Separation**:
  - Confidence reflects *evidentiary stability* (sample depth, cross-year consistency, extraction quality).
  - Priority reflects *study urgency* (expected marks, gap analysis, student mastery).
  - High marks on a single paper produce elevated marks weight, but **low confidence**, correctly instructing the student that the pattern lacks empirical verification.

---

## 5. Architectural & Technical Known Limitations

1. **Choice ("OR") Block Processing**:
   - Examination structures featuring internal choice (`Q1(a) OR Q1(b)`) are currently extracted as individual questions. This causes the cumulative paper marks to exceed 100 in internal computations, though relative normalized weights remain stable.
2. **Text Search Scalability**:
   - The `/api/search` endpoint utilizes indexed SQLite / PostgreSQL string queries. As the question database grows beyond 50,000 questions, full-text vector embeddings (`tsvector` / HNSW) will be required to maintain $<50\text{ms}$ latency.
3. **Multi-Disciplinary Syllabus Overlaps**:
   - Courses shared across multiple departments (e.g., `Engineering Mathematics`) may experience syllabus divergences across engineering streams. These are tracked via `CurriculumMapping.status = 'AMBIGUOUS'`.

