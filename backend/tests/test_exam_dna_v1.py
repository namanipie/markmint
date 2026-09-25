import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.schemas import DataSufficiency
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus

client = TestClient(app)


def test_unit_aggregation():
    """Unit distribution aggregates historical marks and questions by unit and tracks unmapped questions."""
    synthetic_exams = [
        {
            "id": 101,
            "year": 2022,
            "exam_type": "ENDSEM",
            "questions": [
                {"id": 1, "marks": 10.0, "is_alternative": False, "unit": "Unit 1", "question_type": "proof"},
                {"id": 2, "marks": 10.0, "is_alternative": False, "unit": "Unit 2", "question_type": "calculation"},
                {"id": 3, "marks": 10.0, "is_alternative": True, "unit": "Unit 2", "question_type": "calculation"},  # Alt: excluded from denominator
                {"id": 4, "marks": 10.0, "is_alternative": False, "unit": None, "question_type": "explanation"},  # Unmapped
            ]
        },
        {
            "id": 102,
            "year": 2023,
            "exam_type": "ENDSEM",
            "questions": [
                {"id": 5, "marks": 10.0, "is_alternative": False, "unit": "Unit 1", "question_type": "proof"},
                {"id": 6, "marks": 10.0, "is_alternative": False, "unit": "Unit 3", "question_type": "calculation"},
            ]
        }
    ]

    # Total non-alt marks = 10 (id1) + 10 (id2) + 10 (id4) + 10 (id5) + 10 (id6) = 50.0
    # Total questions = 6
    # Unit 1 non-alt marks = 20.0 (id1 + id5) -> weighting = 20 / 50 = 0.40 (40%)
    # Unit 2 non-alt marks = 10.0 (id2) -> weighting = 10 / 50 = 0.20 (20%)
    # Unit 3 non-alt marks = 10.0 (id6) -> weighting = 10 / 50 = 0.20 (20%)
    # Unmapped non-alt marks = 10.0 (id4) -> 10 / 50 = 0.20 (20%)

    dna = DNAAnalyzerService.analyze(synthetic_exams)

    u1 = next(u for u in dna.units if u.unit == "Unit 1")
    u2 = next(u for u in dna.units if u.unit == "Unit 2")
    u3 = next(u for u in dna.units if u.unit == "Unit 3")

    assert u1.marks == 20.0
    assert u1.question_count == 2
    assert u1.historical_weighting == 0.40
    assert u1.paper_coverage == 1.0  # appears in both papers 101 and 102

    assert u2.marks == 10.0
    assert u2.question_count == 2  # includes alt question in question count
    assert u2.historical_weighting == 0.20
    assert u2.paper_coverage == 0.5  # only paper 101

    assert u3.marks == 10.0
    assert u3.question_count == 1
    assert u3.historical_weighting == 0.20

    # Check UnitDistributionDNA summary object
    assert dna.unit_distribution is not None
    assert dna.unit_distribution.unmapped_question_count == 1
    assert dna.unit_distribution.unmapped_marks == 10.0
    assert dna.unit_distribution.is_marks_weighted is True
    assert dna.unit_distribution.total_marks_evaluated == 50.0
    assert dna.unit_distribution.total_questions_evaluated == 6


def test_marks_aggregation():
    """Discrete marks distribution captures historical paper structure without assumptions."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 1, "marks": 1.0, "is_alternative": False},
                {"id": 2, "marks": 1.0, "is_alternative": False},
                {"id": 3, "marks": 5.0, "is_alternative": False},
                {"id": 4, "marks": 8.0, "is_alternative": False},
                {"id": 5, "marks": 8.0, "is_alternative": True},  # Alt question
                {"id": 6, "marks": 15.0, "is_alternative": False},
                {"id": 7, "marks": None, "is_alternative": False},  # Unscored question
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(synthetic_exams)

    assert dna.marks_distribution is not None
    md = dna.marks_distribution

    # Non-alt total marks = 1 + 1 + 5 + 8 + 15 = 30.0
    assert md.total_marks == 30.0
    assert md.unscored_question_count == 1
    assert md.unscored_percentage == round(1 / 7, 4)
    assert md.total_scored_questions == 5  # non-alt scored
    assert md.min_marks == 1.0
    assert md.max_marks == 15.0
    assert md.avg_marks == 6.0  # (1 + 1 + 5 + 8 + 15) / 5 = 30 / 5 = 6.0

    bucket_1 = next(b for b in md.buckets if b.marks == 1.0)
    assert bucket_1.question_count == 2
    assert bucket_1.cumulative_marks == 2.0
    assert bucket_1.percentage_of_questions == round(2 / 7, 4)
    assert bucket_1.percentage_of_marks == round(2.0 / 30.0, 4)

    bucket_8 = next(b for b in md.buckets if b.marks == 8.0)
    assert bucket_8.question_count == 2  # 1 non-alt + 1 alt
    assert bucket_8.cumulative_marks == 8.0  # alt excluded from marks


def test_question_type_aggregation():
    """Question type distribution aggregates persisted types and explicitly tracks unclassified."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 1, "marks": 10.0, "question_type": "comparison"},
                {"id": 2, "marks": 10.0, "question_type": "proof"},
                {"id": 3, "marks": 10.0, "question_type": "proof"},
                {"id": 4, "marks": 5.0, "question_type": None},  # Missing classification
                {"id": 5, "marks": 5.0, "question_type": ""},    # Empty classification
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(synthetic_exams)

    qtypes = {qt.question_type: qt for qt in dna.question_types}

    assert "proof" in qtypes
    assert qtypes["proof"].count == 2
    assert qtypes["proof"].percentage == 0.4  # 2 / 5

    assert "comparison" in qtypes
    assert qtypes["comparison"].count == 1
    assert qtypes["comparison"].percentage == 0.2  # 1 / 5

    # Unclassified must be explicitly accounted for, never fabricated
    assert "unclassified" in qtypes
    assert qtypes["unclassified"].count == 2
    assert qtypes["unclassified"].percentage == 0.4  # 2 / 5
    assert qtypes["unclassified"].marks_weighting == round(10.0 / 40.0, 4)


def test_course_isolation():
    """Exams and questions from other courses must not leak into the analysis."""
    mixed_exams = [
        {
            "id": 1,
            "course_id": 10,
            "year": 2023,
            "questions": [
                {"id": 1, "marks": 10.0, "unit": "Unit 1"}
            ]
        },
        {
            "id": 2,
            "course_id": 99,  # Unrelated course
            "year": 2023,
            "questions": [
                {"id": 2, "marks": 100.0, "unit": "Unit X"}
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(mixed_exams, target_course_id=10)

    assert dna.sample_size.papers == 1
    assert dna.sample_size.questions == 1
    assert dna.sample_size.contributing_exam_ids == [1]
    assert len(dna.units) == 1
    assert dna.units[0].unit == "Unit 1"
    assert dna.sample_size.total_marks == 10.0


def test_duplicate_handling():
    """Duplicate exams and questions must be deduplicated to avoid inflating statistics."""
    duplicate_exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 10, "marks": 10.0, "unit": "Unit 1"},
                {"id": 10, "marks": 10.0, "unit": "Unit 1"},  # Duplicate question ID
                {"id": 11, "marks": 5.0, "unit": "Unit 1"},
            ]
        },
        {
            "id": 1,  # Duplicate exam ID
            "year": 2023,
            "questions": [
                {"id": 10, "marks": 10.0, "unit": "Unit 1"},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(duplicate_exams)

    assert dna.sample_size.papers == 1
    assert dna.sample_size.questions == 2
    assert dna.sample_size.total_marks == 15.0


def test_missing_metadata():
    """Handles missing question metadata gracefully without crashing or fabricating precision."""
    incomplete_exams = [
        {
            "id": 1,
            "year": None,  # Missing year
            "exam_type": None,
            "questions": [
                {"id": 1, "marks": None, "topic": None, "unit": None, "question_type": None, "text": None},
                {"id": 2, "marks": 5.0, "topic": None, "unit": None, "question_type": None, "text": ""},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(incomplete_exams)

    assert dna.sample_size.papers == 1
    assert dna.sample_size.questions == 2
    assert dna.sample_size.time_range_years == (0, 0)
    assert dna.sample_size.unscored_question_count == 1
    assert dna.sample_size.unmapped_question_count == 2
    assert dna.unit_distribution.unmapped_question_count == 2
    assert len(dna.units) == 0  # No mapped units
    assert dna.marks_distribution.unscored_question_count == 1
    assert dna.marks_distribution.total_marks == 5.0


def test_empty_dataset():
    """Empty datasets return structured empty DNA with zero division safeguards."""
    empty_dna_1 = DNAAnalyzerService.analyze([])
    assert empty_dna_1.sample_size.papers == 0
    assert empty_dna_1.sample_size.questions == 0
    assert empty_dna_1.sample_size.sufficiency == DataSufficiency.INSUFFICIENT
    assert empty_dna_1.units == []
    assert empty_dna_1.marks_distribution.buckets == []
    assert empty_dna_1.pattern_summary.top_recurring_families == []

    empty_dna_2 = DNAAnalyzerService.analyze([{"id": 1, "questions": []}])
    assert empty_dna_2.sample_size.papers == 0
    assert empty_dna_2.sample_size.questions == 0


def test_question_patterns_summary():
    """Deterministic question patterns identify recurring families and question formulation stems."""
    synthetic_exams = [
        {
            "id": 1,
            "year": 2022,
            "questions": [
                {
                    "id": 1, "marks": 10.0,
                    "family_name": "Euler_Theorem",
                    "original_text": "State and prove Euler's theorem for homogeneous functions.",
                    "repetition_type": "exact_repeat"
                },
                {
                    "id": 2, "marks": 8.0,
                    "family_name": "Cayley_Hamilton",
                    "original_text": "Find the characteristic equation and verify Cayley-Hamilton theorem.",
                    "repetition_type": "family_repeat"
                },
            ]
        },
        {
            "id": 2,
            "year": 2023,
            "questions": [
                {
                    "id": 3, "marks": 10.0,
                    "family_name": "Euler_Theorem",
                    "original_text": "Prove Euler's theorem and evaluate the given expression.",
                    "repetition_type": "exact_repeat"
                },
                {
                    "id": 4, "marks": 5.0,
                    "family_name": None,
                    "original_text": "Explain the difference between scalar and vector fields.",
                    "repetition_type": "singleton"
                }
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(synthetic_exams)

    assert dna.pattern_summary is not None
    ps = dna.pattern_summary

    # Euler Theorem should be the top recurring family
    assert len(ps.top_recurring_families) >= 1
    top_fam = ps.top_recurring_families[0]
    assert top_fam.family_name == "Euler_Theorem"
    assert top_fam.occurrences == 2
    assert top_fam.distinct_paper_count == 2

    # Check stem patterns
    stem_dict = {p.pattern: p for p in ps.stem_patterns}
    assert "Proof & Derivation" in stem_dict  # matched "prove"
    assert stem_dict["Proof & Derivation"].question_count >= 2

    # Check repetition breakdown
    assert ps.repetition_breakdown.exact_repeat_count == 2
    assert ps.repetition_breakdown.family_repeat_count == 1
    assert ps.repetition_breakdown.singleton_count == 1


def test_historical_cutoff_and_api():
    """Historical cutoff parameter strictly enforces temporal isolation without future leakage."""
    db = SessionLocal()
    try:
        # Fetch an existing course with multiple exams
        course = db.query(Course).first()
        if not course:
            pytest.skip("No courses found in database.")

        exams = db.query(Exam).filter(Exam.course_id == course.id, Exam.year.isnot(None)).all()
        years = sorted(list({e.year for e in exams if e.year}))
        if len(years) < 2:
            pytest.skip("Course does not have exams across multiple years.")

        cutoff = years[-1]  # Cutoff at the most recent year

        # Request DNA with cutoff_year
        resp = client.get(f"/api/analysis/dna?course_id={course.id}&cutoff_year={cutoff}")
        assert resp.status_code == 200
        data = resp.json()

        # All contributing exams must be strictly prior to cutoff
        sample_size = data["sample_size"]
        assert sample_size["time_range_years"][1] < cutoff
        for yr in sample_size["years"]:
            assert yr < cutoff

        # Verify new DNA v1 top-level fields are present
        assert "unit_distribution" in data
        assert "marks_distribution" in data
        assert "pattern_summary" in data

    finally:
        db.close()
