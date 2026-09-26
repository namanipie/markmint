import pytest
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.schemas import ExamDNA, TemporalUnitFocusBreakdown, TopicHistoricalFootprint
from backend.core.database import SessionLocal
from backend.api.endpoints.analysis import _resolve_course, _get_exams_as_dicts, Unit, Syllabus
from backend.models.core import Course

def test_unit_focus_question_percentages_reconcile():
    """Verify that question percentages sum to 100.0% for every dated year."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2022,
            "questions": [
                {"id": 1, "marks": 10.0, "unit": "Unit 1", "unit_number": 1},
                {"id": 2, "marks": 10.0, "unit": "Unit 2", "unit_number": 2},
                {"id": 3, "marks": 10.0, "unit": "Unit 3", "unit_number": 3},
                {"id": 4, "marks": 10.0, "unit": None}, # unmapped
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    rows = [r for r in dna.temporal_unit_focus if r.year == 2022]
    total_pct = sum(r.question_percentage for r in rows)
    assert round(total_pct, 2) == 100.0
    # Each question is 1 of 4 -> 25.0%
    assert all(r.question_percentage == 25.0 for r in rows if r.question_count > 0)

def test_marks_percentages_reconcile():
    """Verify that marks percentages sum to 100.0% for every year with scored marks."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 1, "marks": 20.0, "is_alternative": False, "unit": "Unit 1", "unit_number": 1},
                {"id": 2, "marks": 30.0, "is_alternative": False, "unit": "Unit 2", "unit_number": 2},
                {"id": 3, "marks": 50.0, "is_alternative": False, "unit": None}, # unmapped marks
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    rows = [r for r in dna.temporal_unit_focus if r.year == 2023]
    total_marks_pct = sum(r.marks_weight_percentage for r in rows)
    assert round(total_marks_pct, 2) == 100.0
    u1 = next(r for r in rows if r.unit == "Unit 1")
    u2 = next(r for r in rows if r.unit == "Unit 2")
    unmapped = next(r for r in rows if r.unit == "Unmapped / Unknown")
    assert u1.marks_weight_percentage == 20.0
    assert u2.marks_weight_percentage == 30.0
    assert unmapped.marks_weight_percentage == 50.0

def test_unmapped_questions_explicitly_represented():
    """Verify unmapped questions are bucketed into 'Unmapped / Unknown' with unit_number=None."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2024,
            "questions": [
                {"id": 1, "marks": 10.0, "unit": "Unit 1", "unit_number": 1},
                {"id": 2, "marks": 10.0, "unit": None, "topic": None},
                {"id": 3, "marks": 10.0, "units": [], "topics": []},
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    rows = [r for r in dna.temporal_unit_focus if r.year == 2024]
    unmapped = next((r for r in rows if r.unit == "Unmapped / Unknown"), None)
    assert unmapped is not None
    assert unmapped.unit_number is None
    assert unmapped.question_count == 2
    assert unmapped.question_percentage == round((2 / 3) * 100.0, 2)

def test_unmapped_marks_explicitly_represented():
    """Verify unmapped questions with scored marks contribute to unmapped scored_marks and marks_weight_percentage."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2024,
            "questions": [
                {"id": 1, "marks": 40.0, "is_alternative": False, "unit": "Unit 1", "unit_number": 1},
                {"id": 2, "marks": 60.0, "is_alternative": False, "unit": None},
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    rows = [r for r in dna.temporal_unit_focus if r.year == 2024]
    unmapped = next(r for r in rows if r.unit == "Unmapped / Unknown")
    assert unmapped.scored_marks == 60.0
    assert unmapped.marks_weight_percentage == 60.0

def test_alternative_questions_excluded_from_marks_weighting():
    """Verify is_alternative=True questions count towards question count but are excluded from marks weighting."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2024,
            "questions": [
                {"id": 1, "marks": 50.0, "is_alternative": False, "unit": "Unit 1", "unit_number": 1},
                {"id": 2, "marks": 50.0, "is_alternative": True, "unit": "Unit 1", "unit_number": 1},
                {"id": 3, "marks": 50.0, "is_alternative": False, "unit": "Unit 2", "unit_number": 2},
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    rows = [r for r in dna.temporal_unit_focus if r.year == 2024]
    u1 = next(r for r in rows if r.unit == "Unit 1")
    u2 = next(r for r in rows if r.unit == "Unit 2")

    # Question count includes alternative question (1 non-alt + 1 alt = 2)
    assert u1.question_count == 2
    assert u1.question_percentage == round((2 / 3) * 100.0, 2)

    # Scored marks excludes alternative (only 50.0 of 100.0 total scored marks)
    assert u1.scored_marks == 50.0
    assert u1.marks_weight_percentage == 50.0
    assert u2.marks_weight_percentage == 50.0

def test_sparse_year_detection():
    """Verify is_sparse=True when exam_count <= 1 OR mapped_questions < 10."""
    synthetic_exams = [
        # Year 2020: 1 exam paper, 12 mapped questions -> sparse because papers <= 1
        {
            "id": 1,
            "year": 2020,
            "questions": [{"id": i, "marks": 5.0, "unit": "Unit 1", "unit_number": 1} for i in range(1, 13)]
        },
        # Year 2021: 2 exam papers, but only 4 mapped questions -> sparse because mapped_q < 10
        {
            "id": 2,
            "year": 2021,
            "questions": [{"id": 20, "marks": 5.0, "unit": "Unit 1", "unit_number": 1}, {"id": 21, "marks": 5.0, "unit": "Unit 2", "unit_number": 2}]
        },
        {
            "id": 3,
            "year": 2021,
            "questions": [{"id": 22, "marks": 5.0, "unit": "Unit 1", "unit_number": 1}, {"id": 23, "marks": 5.0, "unit": "Unit 2", "unit_number": 2}]
        },
        # Year 2022: 2 exam papers, 10 mapped questions -> NOT sparse
        {
            "id": 4,
            "year": 2022,
            "questions": [{"id": 30 + i, "marks": 5.0, "unit": "Unit 1", "unit_number": 1} for i in range(5)]
        },
        {
            "id": 5,
            "year": 2022,
            "questions": [{"id": 40 + i, "marks": 5.0, "unit": "Unit 2", "unit_number": 2} for i in range(5)]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    r2020 = [r for r in dna.temporal_unit_focus if r.year == 2020]
    r2021 = [r for r in dna.temporal_unit_focus if r.year == 2021]
    r2022 = [r for r in dna.temporal_unit_focus if r.year == 2022]

    assert all(r.is_sparse for r in r2020)
    assert all(r.is_sparse for r in r2021)
    assert all(not r.is_sparse for r in r2022)

def test_missing_years_not_interpolated():
    """Verify that missing chronological years are NEVER interpolated in focus or footprints."""
    synthetic_exams = [
        {"id": 1, "year": 2018, "questions": [{"id": 1, "marks": 10.0, "topic": "Matrices", "topic_id": 1, "unit": "Unit 1", "unit_number": 1}]},
        {"id": 2, "year": 2023, "questions": [{"id": 2, "marks": 10.0, "topic": "Matrices", "topic_id": 1, "unit": "Unit 1", "unit_number": 1}]},
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    years_in_focus = sorted(list({r.year for r in dna.temporal_unit_focus}))
    assert years_in_focus == [2018, 2023]
    assert 2019 not in years_in_focus
    assert 2020 not in years_in_focus
    assert 2021 not in years_in_focus
    assert 2022 not in years_in_focus

    fp = next(f for f in dna.topic_historical_footprints if f.topic_name == "Matrices")
    assert fp.years_observed == [2018, 2023]
    assert fp.first_seen_year == 2018
    assert fp.latest_seen_year == 2023

def test_cutoff_year_excludes_future_exams():
    """Verify cutoff_year strictly excludes exams on or after the cutoff."""
    db = SessionLocal()
    try:
        course = _resolve_course(db, '1') # Calculus
        cutoff = 2024
        exams_cutoff = _get_exams_as_dicts(course.id, db, cutoff_year=cutoff)
        dna_cutoff = DNAAnalyzerService.analyze(exams_cutoff, target_course_id=course.id)

        years = sorted(list({r.year for r in dna_cutoff.temporal_unit_focus}))
        assert all(y < cutoff for y in years), f"Found year >= {cutoff}: {years}"
        assert 2024 not in years
        assert 2025 not in years

        for fp in dna_cutoff.topic_historical_footprints:
            assert all(y < cutoff for y in fp.years_observed)
            if fp.latest_seen_year is not None:
                assert fp.latest_seen_year < cutoff
    finally:
        db.close()

def test_assessment_cycle_filtering():
    """Verify assessment cycle filtering isolates ENDSEM from continuous assessments."""
    db = SessionLocal()
    try:
        course = _resolve_course(db, '5') # PPS
        endsem_exams = _get_exams_as_dicts(course.id, db, assessment_cycle="ENDSEM")
        ct1_exams = _get_exams_as_dicts(course.id, db, assessment_cycle="CT1")

        dna_endsem = DNAAnalyzerService.analyze(endsem_exams, target_course_id=course.id)
        dna_ct1 = DNAAnalyzerService.analyze(ct1_exams, target_course_id=course.id)

        # Both must produce valid non-overlapping or appropriately scoped datasets
        assert dna_endsem.sample_size.papers > 0
        assert dna_ct1.sample_size.papers > 0
        # In PPS, CT1 questions test early units (Unit 1/2), ENDSEM tests all units
        endsem_units = {r.unit for r in dna_endsem.temporal_unit_focus if r.question_count > 0}
        ct1_units = {r.unit for r in dna_ct1.temporal_unit_focus if r.question_count > 0}
        assert len(endsem_units) >= len(ct1_units)
    finally:
        db.close()

def test_course_isolation():
    """Verify exams from other courses are excluded when target_course_id is provided."""
    synthetic_exams = [
        {"id": 1, "course_id": 1, "year": 2023, "questions": [{"id": 1, "marks": 10.0, "unit": "Unit 1", "unit_number": 1, "topic": "Calc"}]},
        {"id": 2, "course_id": 2, "year": 2023, "questions": [{"id": 2, "marks": 10.0, "unit": "Unit 5", "unit_number": 5, "topic": "Chem"}]},
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams, target_course_id=1)
    # Only Course 1 exam should be evaluated
    assert dna.sample_size.papers == 1
    assert dna.sample_size.questions == 1
    assert all(r.unit != "Unit 5" for r in dna.temporal_unit_focus if r.question_count > 0)
    assert len(dna.topic_historical_footprints) == 1
    assert dna.topic_historical_footprints[0].topic_name == "Calc"

def test_track_language_isolation():
    """Verify track isolation on multi-track course (Foreign Languages)."""
    db = SessionLocal()
    try:
        course_fl = _resolve_course(db, '8')
        tracks = {t.track_name: t.id for t in course_fl.tracks}
        if "German" in tracks and "French" in tracks:
            g_exams = _get_exams_as_dicts(course_fl.id, db, track_id=tracks["German"])
            f_exams = _get_exams_as_dicts(course_fl.id, db, track_id=tracks["French"])
            g_dna = DNAAnalyzerService.analyze(g_exams, target_course_id=course_fl.id)
            f_dna = DNAAnalyzerService.analyze(f_exams, target_course_id=course_fl.id)

            g_topics = {fp.topic_name for fp in g_dna.topic_historical_footprints}
            f_topics = {fp.topic_name for fp in f_dna.topic_historical_footprints}
            assert len(g_topics.intersection(f_topics)) == 0, "Track leakage detected between German and French"
    finally:
        db.close()

def test_empty_historical_dataset():
    """Verify that an empty list of exams returns a valid _empty_dna without exceptions."""
    dna = DNAAnalyzerService.analyze([])
    assert isinstance(dna, ExamDNA)
    assert dna.sample_size.papers == 0
    assert dna.sample_size.questions == 0
    assert dna.temporal_unit_focus == []
    assert dna.topic_historical_footprints == []
    assert dna.temporal_topic_focus == []

def test_duplicate_exam_inputs_do_not_change_results():
    """Verify that duplicate exams with identical IDs are deduplicated identically."""
    exam1 = {
        "id": 1,
        "year": 2023,
        "questions": [{"id": 10, "marks": 10.0, "unit": "Unit 1", "unit_number": 1, "topic": "T1", "topic_id": 1}]
    }
    dna_single = DNAAnalyzerService.analyze([exam1])
    dna_duplicate = DNAAnalyzerService.analyze([exam1, exam1])

    assert dna_single.sample_size.papers == dna_duplicate.sample_size.papers
    assert dna_single.sample_size.questions == dna_duplicate.sample_size.questions
    assert len(dna_single.temporal_unit_focus) == len(dna_duplicate.temporal_unit_focus)
    assert dna_single.temporal_unit_focus[0].question_count == dna_duplicate.temporal_unit_focus[0].question_count

def test_unscored_questions():
    """Verify questions with marks=None do not crash analysis and set marks_weight_percentage=0.0."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2021,
            "questions": [
                {"id": 1, "marks": None, "unit": "Unit 1", "unit_number": 1, "topic": "Calculus"},
                {"id": 2, "marks": None, "unit": "Unit 2", "unit_number": 2, "topic": "Algebra"},
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    assert dna.sample_size.total_marks == 0.0
    assert dna.sample_size.unscored_question_count == 2
    rows = dna.temporal_unit_focus
    assert all(r.scored_marks == 0.0 for r in rows)
    assert all(r.marks_weight_percentage == 0.0 for r in rows)
    # Question percentages still reconcile to 100.0%
    q_pct_sum = sum(r.question_percentage for r in rows)
    assert round(q_pct_sum, 1) == 100.0

def test_temporal_topic_focus_reconciliation_and_question_types():
    """Verify temporal topic focus reconciles question percentage and marks, and computes question-types."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 1, "marks": 20.0, "unit": "Unit 1", "unit_number": 1, "topic": "Eigenvalues", "topic_id": 10, "question_type": "Calculation / Numerical"},
                {"id": 2, "marks": 30.0, "unit": "Unit 1", "unit_number": 1, "topic": "Eigenvalues", "topic_id": 10, "question_type": "Derivation / Proof"},
                {"id": 3, "marks": 50.0, "unit": "Unit 2", "unit_number": 2, "topic": "Optimization", "topic_id": 20, "question_type": "Calculation / Numerical"},
                {"id": 4, "marks": 50.0, "unit": None, "topic": None, "question_type": "Other / Unclassified"}, # unmapped
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    assert dna.temporal_topic_focus is not None
    rows = dna.temporal_topic_focus

    # Check question percentage reconciliation across topics
    q_sum = sum(r.question_percentage for r in rows)
    assert round(q_sum, 1) == 100.0

    # Check marks weight percentage reconciliation across topics
    m_sum = sum(r.marks_weight_percentage for r in rows)
    assert round(m_sum, 1) == 100.0

    # Check Eigenvalues topic composition
    eigen = next(r for r in rows if r.topic == "Eigenvalues")
    assert eigen.question_count == 2
    assert eigen.scored_marks == 50.0
    assert eigen.question_types == {"Calculation / Numerical": 1, "Derivation / Proof": 1}
    assert eigen.persistence_years == [2023]
    assert eigen.first_seen_year == 2023
    assert eigen.latest_seen_year == 2023

    # Check unmapped bucket
    unmapped = next(r for r in rows if r.topic == "Unmapped / Unknown")
    assert unmapped.question_count == 1
    assert unmapped.scored_marks == 50.0
    assert unmapped.question_percentage == 25.0

def test_existing_exam_dna_fields_backward_compatible():
    """Verify all pre-existing ExamDNA fields remain populated and backward compatible."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 1, "marks": 10.0, "is_alternative": False, "topic": "Calculus", "unit": "Unit 1", "question_type": "analytical", "difficulty": 0.5},
            ]
        }
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    assert dna.sample_size is not None
    assert dna.topics is not None and len(dna.topics) == 1
    assert dna.units is not None and len(dna.units) == 1
    assert dna.question_types is not None and len(dna.question_types) == 1
    assert dna.repetition is not None
    assert dna.families is not None
    assert dna.temporal_trends is not None
    assert dna.unit_distribution is not None
    assert dna.marks_distribution is not None
    assert dna.pattern_summary is not None
    assert dna.temporal_unit_question_type_breakdown is not None
    assert dna.temporal_unit_focus is not None
    assert dna.topic_historical_footprints is not None
    assert dna.temporal_topic_focus is not None

def test_topic_footprints_only_actually_observed_years():
    """Verify topic footprints contain strictly the discrete observed years, ignoring undated papers and unobserved years."""
    synthetic_exams = [
        {"id": 1, "year": 2020, "questions": [{"id": 1, "marks": 10.0, "topic": "Algebra", "topic_id": 100, "unit": "Unit 1", "unit_number": 1}]},
        {"id": 2, "year": 2024, "questions": [{"id": 2, "marks": 10.0, "topic": "Algebra", "topic_id": 100, "unit": "Unit 1", "unit_number": 1}]},
        {"id": 3, "year": None, "questions": [{"id": 3, "marks": 10.0, "topic": "Algebra", "topic_id": 100, "unit": "Unit 1", "unit_number": 1}]},
    ]
    dna = DNAAnalyzerService.analyze(synthetic_exams)
    fp = dna.topic_historical_footprints[0]
    assert fp.years_observed == [2020, 2024]
    assert fp.first_seen_year == 2020
    assert fp.latest_seen_year == 2024
    # Dated papers = 2 (id 1 and id 2). Algebra is in both dated papers -> 100.0%
    assert fp.paper_coverage_percentage == 100.0
