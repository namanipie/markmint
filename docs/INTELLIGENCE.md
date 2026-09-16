# MarkMint Academic Intelligence Architecture & Intelligence Layer

## 1. Overview & Core Mission

MarkMint is a deterministic, evidence-backed academic intelligence engine. Its intelligence core (**MintAI** / **ExamDNA**) synthesizes university examination history, canonical curriculum mappings, question taxonomy, and personalized student mastery into auditable study forecasts and adaptive revision schedules.

The platform enforces zero synthetic fabrication:
- **No speculative predictions** without verified historical examination papers.
- **Strict canonical curriculum lineage**: branches, semesters, and course codes originate from verified institutional mappings.
- **Statistical decoupling**: probability, statistical confidence, and study priority are mathematically distinct and never conflated.
- **Strict temporal isolation**: backtesting and predictions only operate on historical evidence chronologically preceding target examination dates.

---

## 2. Canonical Academic Curriculum Hierarchy

All academic queries in MarkMint follow a strictly unidirectional resolution chain:

```
Academic Branch (e.g., Aerospace Engineering)
  └── Semester (e.g., Semester 1)
        └── Curriculum Mapping Entry (frontend curriculum_id)
              └── Canonical Course (backend course_id & canonical_code)
```

### Data Availability States

The platform categorizes academic registry entries into 5 mutually exclusive, explicit states:

1. **`READY`**: The curriculum subject is mapped to a backend `Course` with verified examination papers and indexed question taxonomy. Full intelligence snapshot is generated.
2. **`CATALOG_ONLY`**: The course is mapped in the registry (`status == "MATCHED"`), but 0 historical exam papers have been uploaded (`exam_count == 0`). The UI displays catalog confirmation without generating synthetic forecasts.
3. **`INSUFFICIENT_EVIDENCE`**: Historical papers exist ($N = 1$ cycle), but the sample size is statistically inadequate for high-confidence predictions. The UI offers historical question browsing while gating low-evidence forecasts.
4. **`AMBIGUOUS`**: The curriculum subject matches multiple distinct institutional courses (e.g., Biology mapping to both Cell Biology and Bioengineering). Forecasts are halted and explicit candidate notes are presented.
5. **`UNMATCHED`**: The curriculum subject has no verified backend course mapping in the corpus. Clear awaiting-papers state is rendered.

---

## 3. ExamDNA: Statistical Foundations & Feature Extraction

ExamDNA transforms raw parsed examination papers into structured statistical distributions across three dimensions:

### A. Topic Distributions
- **`historical_frequency`**: Proportion of questions mapped to the topic across the full historical corpus.
- **`recent_frequency`**: Proportion of questions mapped to the topic within the most recent exam cycle.
- **`paper_coverage`**: Fraction of papers containing at least one question on the topic:
  $$\text{paper\_coverage} = \frac{k}{N}$$
  where $k$ is papers with topic and $N$ is total papers analyzed.
- **`total_marks`** and **`average_marks`**: Historical mark accumulation and weight per appearance.

### B. Unit & Module Weighting
- Aggregates mark distribution across syllabus units to ensure predictions respect institutional assessment balance.

### C. Question Families & Semantic Similarity
- Questions sharing mathematical structures, core equations, or near-duplicate phrasing are clustered into deterministic question families.
- Question family recurrence intervals track cycle-to-cycle repetition.

---

## 4. Probabilistic Calibration & Decoupled Metrics

MintAI explicitly decouples **Probability**, **Statistical Confidence**, and **Actionable Priority**:

| Dimension | Metric / Semantics | Value Range | Rationale |
| :--- | :--- | :--- | :--- |
| **Probability** | `LAPLACE_SMOOTHED_PAPER_RECURRENCE` | $0.0 \dots 1.0$ | Statistically defensible likelihood of topic appearance in the next exam paper. |
| **Confidence** | Reliability based on sample volume | `INSUFFICIENT`, `LOW`, `MEDIUM`, `HIGH` | Gated by paper count ($N$) and question density. $N \le 1 \implies$ `INSUFFICIENT`; $N \le 2 \implies$ capped at `MEDIUM`. |
| **Study Priority** | Personalized urgency band | `VERY_HIGH`, `HIGH`, `MEDIUM`, `LOW` | Combines ranking score with student mastery status (`STUDENT_UNSTUDIED`, `STUDENT_MASTERED`). |

### Laplace Smoothing Formulation

For a topic that appeared in $k$ papers out of $N$ analyzed historical papers:

$$P(\text{topic} \in \text{upcoming exam}) = \frac{k + 1}{N + 2}$$

This Bayesian Laplace prior (Rule of Succession) ensures:
- With $k = 0, N = 3$, probability is $1/5 = 0.20$ (not artificially 0%).
- With $k = 3, N = 3$, probability is $4/5 = 0.80$ (not artificially 100%).
- Sparse samples gracefully regress toward the uninformed prior ($0.5$).

### Explainable Machine-Readable Reason Codes

Every prediction item outputs structured reason codes and transparent human explanations:
- `SUFFICIENT_HISTORY`: Analyzed $\ge 3$ verified examination papers.
- `INSUFFICIENT_EVIDENCE`: Historical paper count $\le 1$.
- `HIGH_FREQUENCY`: Topic appears in $\ge 20\%$ of historical questions or $\ge 3$ occurrences.
- `RECENTLY_REPEATED`: Appeared in the most recent examination cycle.
- `HIGH_MARK_WEIGHT`: Carries high credit weight ($\ge 15\%$ total marks or $\ge 8$ marks/question).
- `QUESTION_FAMILY_RECURRING`: Structural question repetition detected across cycles.
- `CONFLICTING_SIGNALS`: High historical mark weight but absent in recent cycles.
- `LONG_ABSENCE`: Frequent historically, but unrepresented in latest papers.

---

## 5. Walk-Forward Chronological Backtesting Evaluation

Model performance is evaluated via chronological backtesting without future data leakage:

1. **Folds**: For each historical examination year $T \in \{T_{\min}+1 \dots T_{\max}\}$:
   - Training context: strictly all exams where $\text{year} < T$.
   - Target ground truth: exams where $\text{year} = T$.
2. **Metrics Evaluated**:
   - $\text{Precision}@K = \frac{|\text{Top } K \cap \text{Target Topics}|}{K}$
   - $\text{Recall}@K = \frac{|\text{Top } K \cap \text{Target Topics}|}{|\text{Target Topics}|}$
   - $\text{Marks\_Coverage}@K = \frac{\sum_{t \in \text{Top } K \cap \text{Target}} \text{marks}(t)}{\sum_{t \in \text{Target}} \text{marks}(t)}$
   - $\text{Question\_Coverage}@K = \frac{\sum_{t \in \text{Top } K \cap \text{Target}} \text{questions}(t)}{\sum_{t \in \text{Target}} \text{questions}(t)}$
3. Evaluated across cutoff thresholds $K \in [3, 5, 10]$.
4. Evaluates all baseline models (`AllTimeFrequency`, `RecentFrequency`, `RecencyWeighted`, `MarksWeighted`, `ExamScopeCombined`).

---

## 6. Personalization, Mastery, and Adaptive Schedule

### Preparation Gap Decomposition
The student preparation meter computes exact topic state:
- $\text{Coverage \%} = \frac{\text{Mastered} + 0.5 \times \text{In Progress}}{\text{Total Predicted Topics}} \times 100$

### Recommended Study Actions
Transitions are evaluated per topic:
- `DEEP_STUDY_URGENT`: High prediction yield + student unstudied.
- `PRACTICE_QUESTIONS`: High yield + student in progress.
- `MAINTAIN_AND_REVIEW`: High yield + student mastered ($\ge 60\%$ practice accuracy).
- `CONCEPT_REINFORCEMENT`: Medium yield + student in progress.
- `FOUNDATIONAL_EXPLORATION`: Unstudied lower yield topic.

### Adaptive Revision Schedule (Strict Time Conservation)

For target exam dates with $D$ days remaining:
$$\sum_{i=1}^{M} \text{duration\_days}(\text{Phase } i) = D \quad (\forall D \ge 1)$$

- **$D \ge 14$ days**: 3-Phase breakdown:
  - Phase 1: High-Yield Topic Mastery ($\approx 50\%$ duration)
  - Phase 2: Moderate-Yield Topic Reinforcement ($\approx 30\%$ duration)
  - Phase 3: High-Frequency Question Solving & Mock Drills ($\approx 20\%$ duration)
- **$3 \le D < 14$ days**: Compressed 3-phase with minimum 1 day per phase, strictly summing to $D$.
- **$D \le 2$ days**: Emergency triage revision phase with duration equal to $D$.

---

## 7. Versioning & Lineage Metadata

Centralized in `backend.core.version`:
- `MODEL_VERSION = "2.2.0"`
- `TAXONOMY_VERSION = "1.0.0"`
- `ENGINE_VERSION = "mintai-v2"`
- `CORPUS_VERSION = "2026.1"`
- `CALIBRATION_METHOD = "LAPLACE_SMOOTHED_PAPER_RECURRENCE"`
- `SCORE_SEMANTICS = "EMPIRICAL_PAPER_RECURRENCE_PROBABILITY"`

All endpoints embed this metadata in JSON responses for auditable client-side traceability.
