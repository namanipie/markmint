"""
Comprehensive Intelligence Revalidation Script for Exam DNA after Chronology Backfill.

Compares BEFORE (production_corpus.db.pre_exam_metadata_backfill_backup) vs
AFTER (production_corpus.db) across:
1. Calculus And Linear Algebra (Course ID 1)
2. Chemistry (Course ID 2)
3. Programming For Problem Solving (Course ID 5)
4. Database Management Systems (Course ID 4)

Validates:
- Exam counts (total, with year, without year)
- Distinct historical years
- Temporal unit-year observations
- Sparse observations
- Questions & marks represented temporally
- Mathematical consistency (question % sum to 100%, marks % sum to 100%)
- Cutoffs: 2020, 2023, 2024
- Assessment filters: CT1, CT2, ENDSEM
- Course isolation
"""

import os
import sqlite3
import sys
from collections import defaultdict
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath("."))
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.analysis import _get_exams_as_dicts
from backend.core.database import SessionLocal
from backend.models.core import Course


def get_course_stats(db_path: str, course_id: int) -> Dict[str, Any]:
    conn = sqlite3.connect(f"file:{os.path.abspath(db_path)}?mode=ro", uri=True)
    c = conn.cursor()

    # Total exams, with year, without year
    c.execute("SELECT count(*), count(year), count(*) - count(year) FROM exams WHERE course_id = ?", (course_id,))
    tot_exams, with_year, without_year = c.fetchone()

    # Distinct years
    c.execute("SELECT DISTINCT year FROM exams WHERE course_id = ? AND year IS NOT NULL ORDER BY year", (course_id,))
    years = [r[0] for r in c.fetchall()]

    # Total questions and marks in course
    c.execute("""
        SELECT count(q.id), coalesce(sum(q.marks), 0.0)
        FROM exams e
        JOIN sections s ON s.exam_id = e.id
        JOIN questions q ON q.section_id = s.id
        WHERE e.course_id = ?
    """, (course_id,))
    total_q, total_marks = c.fetchone()

    # Questions and marks with exam year NOT NULL
    c.execute("""
        SELECT count(q.id), coalesce(sum(q.marks), 0.0)
        FROM exams e
        JOIN sections s ON s.exam_id = e.id
        JOIN questions q ON q.section_id = s.id
        WHERE e.course_id = ? AND e.year IS NOT NULL
    """, (course_id,))
    yeared_q, yeared_marks = c.fetchone()

    conn.close()

    return {
        "course_id": course_id,
        "total_exams": tot_exams,
        "exams_with_year": with_year,
        "exams_without_year": without_year,
        "years": years,
        "total_questions": total_q,
        "total_marks": total_marks,
        "yeared_questions": yeared_q,
        "yeared_marks": yeared_marks,
    }


def analyze_course_dna(db_session, course_id: int, cutoff_year: int = None, assessment_cycle: str = None) -> Any:
    exams_dict = _get_exams_as_dicts(
        course_id=course_id,
        db=db_session,
        assessment_cycle=assessment_cycle,
        cutoff_year=cutoff_year,
    )
    return DNAAnalyzerService.analyze(exams_dict, target_course_id=course_id)


def run_revalidation():
    db_after = SessionLocal()

    canonical_courses = [
        (1, "Calculus And Linear Algebra"),
        (2, "Chemistry"),
        (5, "Programming For Problem Solving"),
        (4, "Database Management Systems"),
    ]

    print("=" * 80)
    print("MINTAI EXAM DNA INTELLIGENCE REVALIDATION")
    print("=" * 80)

    # 1. Compare Before vs After
    print("\n" + "=" * 80)
    print("PART 1: BEFORE VS AFTER COMPARISON (CANONICAL COURSES)")
    print("=" * 80)

    before_db = "production_corpus.db.pre_exam_metadata_backfill_backup"
    after_db = "production_corpus.db"

    for cid, cname in canonical_courses:
        b_stats = get_course_stats(before_db, cid)
        a_stats = get_course_stats(after_db, cid)

        # Analyze with current DB
        dna_report = analyze_course_dna(db_after, cid)
        temporal_rows = dna_report.temporal_unit_question_type_breakdown
        
        # Unit-year observations: unique (unit, year) pairs
        unit_years = set((r.unit, r.year) for r in temporal_rows)
        sparse_obs = set((r.unit, r.year) for r in temporal_rows if r.is_sparse)

        print(f"\n[{cid}] {cname}:")
        print(f"  Total Exams: {a_stats['total_exams']}")
        print(f"  Exams with Year:        BEFORE = {b_stats['exams_with_year']:>2}  -->  AFTER = {a_stats['exams_with_year']:>2}  (Delta: +{a_stats['exams_with_year'] - b_stats['exams_with_year']})")
        print(f"  Exams without Year:     BEFORE = {b_stats['exams_without_year']:>2}  -->  AFTER = {a_stats['exams_without_year']:>2}  (Delta: -{b_stats['exams_without_year'] - a_stats['exams_without_year']})")
        print(f"  Distinct Historical Years: BEFORE = {b_stats['years']}  -->  AFTER = {a_stats['years']}")
        print(f"  Temporal Questions:     BEFORE = {b_stats['yeared_questions']:>3}  -->  AFTER = {a_stats['yeared_questions']:>3}  (Delta: +{a_stats['yeared_questions'] - b_stats['yeared_questions']})")
        print(f"  Temporal Marks:         BEFORE = {b_stats['yeared_marks']:>6.1f}  -->  AFTER = {a_stats['yeared_marks']:>6.1f}  (Delta: +{a_stats['yeared_marks'] - b_stats['yeared_marks']:.1f})")
        print(f"  Temporal Unit-Year Pairs: {len(unit_years)} (Sparse: {len(sparse_obs)}, Non-Sparse: {len(unit_years) - len(sparse_obs)})")
        print(f"  Total Temporal Breakdown Rows: {len(temporal_rows)}")

    # 2. Mathematical Consistency in Unit-Years
    print("\n" + "=" * 80)
    print("PART 2: TEMPORAL DISTRIBUTION MATHEMATICAL CONSISTENCY")
    print("=" * 80)
    for cid, cname in canonical_courses:
        dna = analyze_course_dna(db_after, cid)
        t_rows = dna.temporal_unit_question_type_breakdown
        grouped = defaultdict(list)
        for r in t_rows:
            grouped[(r.unit, r.year)].append(r)

        print(f"\nCourse {cid} ({cname}): {len(grouped)} unit-year groups")
        errors = 0
        for (u, y), rows in grouped.items():
            sum_q_pct = sum(r.question_percentage for r in rows)
            # Question count reconciliation
            unit_q_total = rows[0].total_unit_questions
            sum_q_cnt = sum(r.question_count for r in rows)
            assert sum_q_cnt == unit_q_total, f"Question count mismatch in ({u}, {y}): {sum_q_cnt} != {unit_q_total}"

            # Percentage sum close to 1.0 (allowing float rounding)
            if not (0.99 <= sum_q_pct <= 1.01):
                print(f"  * Warning: Question percentage sum in ({u}, {y}) = {sum_q_pct}")
                errors += 1

            # Marks percentage sum close to 1.0 if scored marks exist
            scored_marks_total = sum(r.scored_marks for r in rows)
            if scored_marks_total > 0:
                sum_m_pct = sum(r.marks_weight_percentage for r in rows)
                if not (0.99 <= sum_m_pct <= 1.01):
                    print(f"  * Warning: Marks percentage sum in ({u}, {y}) = {sum_m_pct}")
                    errors += 1

        if errors == 0:
            print(f"  -> All {len(grouped)} unit-year groups mathematically reconcile (100% sum and exact question counts).")

    # 3. Cutoff Isolation Across 2020, 2023, 2024
    print("\n" + "=" * 80)
    print("PART 3: STRICT CUTOFF ISOLATION VALIDATION")
    print("=" * 80)
    for cid, cname in [(1, "Calculus"), (5, "PPS")]:
        for cutoff in [2020, 2023, 2024]:
            dna_cutoff = analyze_course_dna(db_after, cid, cutoff_year=cutoff)
            max_year = None
            for r in dna_cutoff.temporal_unit_question_type_breakdown:
                assert r.year < cutoff, f"CRITICAL: Year {r.year} >= cutoff {cutoff} leaked into {cname}!"
                if max_year is None or r.year > max_year:
                    max_year = r.year
            print(f"Course {cid} ({cname}) with cutoff {cutoff}: Passed! (Max year observed: {max_year})")

    # 4. Assessment Cycle Filtering
    print("\n" + "=" * 80)
    print("PART 4: ASSESSMENT CYCLE FILTERING VALIDATION")
    print("=" * 80)
    for cycle in ["CT1", "CT2", "ENDSEM"]:
        dna_filtered = analyze_course_dna(db_after, 5, assessment_cycle=cycle)
        types_present = set(dna_filtered.sample_size.exam_types)
        print(f"PPS with assessment_cycle='{cycle}': {dna_filtered.sample_size.papers} papers, types={types_present}")

    # 5. Course Isolation
    print("\n" + "=" * 80)
    print("PART 5: COURSE ISOLATION VALIDATION")
    print("=" * 80)
    pps_dna = analyze_course_dna(db_after, 5)
    calculus_dna = analyze_course_dna(db_after, 1)
    
    pps_exam_ids = set(pps_dna.sample_size.contributing_exam_ids)
    calc_exam_ids = set(calculus_dna.sample_size.contributing_exam_ids)
    overlap = pps_exam_ids.intersection(calc_exam_ids)
    assert len(overlap) == 0, f"Course isolation failure: exam overlap {overlap}"
    print(f"Course isolation verified: zero exam overlap between Course 5 ({len(pps_exam_ids)} exams) and Course 1 ({len(calc_exam_ids)} exams).")

    db_after.close()


if __name__ == "__main__":
    run_revalidation()
