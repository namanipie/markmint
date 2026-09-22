# Changelog

All notable changes to MarkMint are documented in this file.

## [1.0.0] - 2026-09-22

### MarkMint v1.0 — SRMIST First-Year Release

This milestone marks the finalization of the completed first-year platform for SRM Institute of Science and Technology students.

#### Core Platform & Intelligence
- **First-Year Curriculum**: Complete authoritative syllabus mappings for all first-year engineering courses (including Semester 1 and Semester 2 courses such as Calculus, Chemistry, Semiconductor Physics, EEE, OODP, and 6 Foreign Language tracks).
- **Canonical 5-Unit Taxonomy**: Strict enforcement of the canonical 5-unit syllabus taxonomy across all courses, preventing phantom units or legacy schema leakage.
- **Observed Assessment Scope**: Reconciled intended syllabus scope against archived examination papers (Cycle Test 1, Cycle Test 2, and End Semester).
- **MintAI Prediction Engine**: Multi-year recurring question family detection, frequency tracking, and calibrated confidence forecasting based strictly on historical exam evidence.
- **Repetition Analytics**: Empirical repetition metrics across verbatim repeats and recurring question families.

#### Unified Student Experience
- **Home**: Student-oriented entry point with automatic "Continue Studying" restoration of active course, cycle, and last-studied targets, plus discovery orientation for first-time visitors.
- **MintAI**: Direct deep-linking from forecast prediction cards into actionable study targets via "Study this →".
- **Study Plan**: Pragmatic, action-oriented study roadmap consuming MintAI intelligence directly, featuring 3-state task tracking (`[Not Started]`, `[In Progress]`, `[Done]`), working resources only, and subtle collapsible lecture note uploads.
- **Course Pages**: Comprehensive course exploration, verified past examination question lineages, and isolated track explorers.
- **Track Isolation**: Strict isolation of multi-track courses (Course 8 Foreign Languages: German, French, Spanish, Japanese, Korean, Chinese) across syllabuses, exams, predictions, and study plans.
- **Context Persistence**: Seamless local storage persistence across navigation flows for anonymous student sessions.

#### Branding & Production Finalization
- Removed visible Beta branding across primary navigation, footer, and legal disclaimers.
- Finalized version constants at `1.0.0` in `package.json`, FastAPI application configuration, and frontend metadata.
