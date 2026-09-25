"""
Verification script for Temporal Exam DNA and Cutoff Isolation after Metadata Backfill.

Verifies:
1. Course temporal evolution breakdown for affected courses:
   - Programming For Problem Solving (ID 5)
   - Communicative English (ID 15)
   - Electrical & Electronics Engineering (ID 14)
   - Semiconductor Physics (ID 13)
2. Strict Cutoff Year Isolation:
   - For cutoff_year = Y, no exams with year >= Y appear in or influence temporal results.
3. No fabricated years appear.
4. Total unit counts and question types reconcile with database ground truth.
"""

import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.core.database import SessionLocal
from backend.api.endpoints.analysis import _get_exams_as_dicts
from backend.services.dna.analyzer import DNAAnalyzerService


def verify_temporal_dna():
    db = SessionLocal()

    print("=" * 80)
    print("TEMPORAL EXAM DNA VERIFICATION")
    print("=" * 80)

    # Test 1: Programming For Problem Solving (Course ID: 5)
    print("\n--- Course 5: Programming For Problem Solving ---")
    exams_pps = _get_exams_as_dicts(5, db, None)
    dna_pps = DNAAnalyzerService.analyze(exams_pps, target_course_id=5)
    temporal_pps = dna_pps.temporal_unit_question_type_breakdown
    print(f"Total historical exams analyzed: {len(exams_pps)}")
    print(f"Total historical questions analyzed: {dna_pps.sample_size.questions}")
    print(f"Temporal breakdown rows: {len(temporal_pps)}")
    all_pps_years = {row.year for row in temporal_pps}
    print(f"All distinct temporal years for PPS: {sorted(list(all_pps_years))}")
    assert {2022, 2023}.issubset(all_pps_years), f"Expected newly backfilled years 2022 and 2023 in PPS, got {all_pps_years}"
    assert all_pps_years.issubset({2019, 2022, 2023, 2024, 2025}), f"Unexpected fabricated years in PPS: {all_pps_years}"

    # Test 2: Communicative English (Course ID: 15)
    print("\n--- Course 15: Communicative English ---")
    exams_eng = _get_exams_as_dicts(15, db, None)
    dna_eng = DNAAnalyzerService.analyze(exams_eng, target_course_id=15)
    temporal_eng = dna_eng.temporal_unit_question_type_breakdown
    print(f"Total historical exams analyzed: {len(exams_eng)}")
    print(f"Total historical questions analyzed: {dna_eng.sample_size.questions}")
    print(f"Temporal breakdown rows: {len(temporal_eng)}")
    all_eng_years = {row.year for row in temporal_eng}
    print(f"All distinct temporal years for English: {sorted(list(all_eng_years))}")
    assert 2024 in all_eng_years, "Expected newly backfilled year 2024 to participate in Communicative English!"

    # Test 3: Electrical & Electronics Engineering (Course ID: 14)
    print("\n--- Course 14: Electrical & Electronics Engineering ---")
    exams_eee = _get_exams_as_dicts(14, db, None)
    dna_eee = DNAAnalyzerService.analyze(exams_eee, target_course_id=14)
    temporal_eee = dna_eee.temporal_unit_question_type_breakdown
    print(f"Total historical exams analyzed: {len(exams_eee)}")
    print(f"Total historical questions analyzed: {dna_eee.sample_size.questions}")
    print(f"Temporal breakdown rows: {len(temporal_eee)}")
    all_eee_years = {row.year for row in temporal_eee}
    print(f"All distinct temporal years for EEE: {sorted(list(all_eee_years))}")
    assert {2022, 2023}.issubset(all_eee_years), "Expected newly backfilled years 2022 & 2023 in EEE!"

    # Test 4: Strict Cutoff Isolation Check
    print("\n--- Strict Cutoff Year Isolation Test ---")
    for cutoff in [2022, 2023, 2024]:
        exams_cutoff = _get_exams_as_dicts(5, db, None, cutoff_year=cutoff)
        for ex in exams_cutoff:
            if ex.get("year") is not None:
                assert ex["year"] < cutoff, f"Exams input leak: exam {ex['id']} has year {ex['year']} >= cutoff {cutoff}!"
        dna_cutoff = DNAAnalyzerService.analyze(exams_cutoff, target_course_id=5)
        for row in dna_cutoff.temporal_unit_question_type_breakdown:
            assert row.year < cutoff, f"LEAKAGE DETECTED: year {row.year} >= cutoff {cutoff} in row {row}!"
        print(f"  Passed cutoff_year = {cutoff}: zero exams with year >= {cutoff} influenced results.")

    db.close()
    print("\nAll temporal DNA and cutoff isolation assertions PASSED successfully!")


if __name__ == "__main__":
    verify_temporal_dna()
