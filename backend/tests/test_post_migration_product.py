import pytest
from backend.models.core import Course, Exam, Section, Question, QuestionFamily, QuestionFamilyMembership
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import PredictionResult


def test_dna_analyzer_distinct_paper_count_and_no_fake_zeros():
    """Verify distinct_paper_count tracks distinct exams, not just years, and does not fake marks."""
    analyzer = DNAAnalyzerService()
    # 3 questions in 3 exams across 2 years (two in 2023, one in 2024)
    exams = [
        {
            "id": 10,
            "year": 2023,
            "exam_type": "CLA-1",
            "questions": [
                {
                    "id": 1,
                    "text": "Explain Newton's second law.",
                    "family_id": 101,
                    "family_name": "Explain Newton's second law.",
                    "marks": 5.0,
                    "is_alternative": False,
                }
            ],
        },
        {
            "id": 11,
            "year": 2023,
            "exam_type": "CLA-2",
            "questions": [
                {
                    "id": 2,
                    "text": "State and prove Newton's second law with equations.",
                    "family_id": 101,
                    "family_name": "Explain Newton's second law.",
                    "marks": 5.0,
                    "is_alternative": False,
                }
            ],
        },
        {
            "id": 12,
            "year": 2024,
            "exam_type": "EndSem",
            "questions": [
                {
                    "id": 3,
                    "text": "Newton's second law derivation (OR choice)",
                    "family_id": 101,
                    "family_name": "Explain Newton's second law.",
                    "marks": 10.0,
                    "is_alternative": True,  # Alternative choice must be excluded from total marks
                }
            ],
        },
    ]

    dna = analyzer.analyze(exams)
    assert hasattr(dna, "families")
    fam = next((f for f in dna.families if f.family_id == 101), None)
    assert fam is not None
    # 3 distinct exam papers (10, 11, 12), not 2 years (2023, 2024)
    assert fam.distinct_paper_count == 3
    # Non-alternative marks: only questions 1 (5.0) and 2 (5.0) -> total 10.0, avg 5.0
    assert fam.total_marks == 10.0
    assert fam.average_marks == 5.0
    assert fam.occurrences == 3


def test_dna_analyzer_null_marks_when_unspecified():
    """Verify when questions lack marks, average_marks and total_marks are None, not 0.0."""
    analyzer = DNAAnalyzerService()
    exams = [
        {
            "id": 20,
            "year": 2022,
            "exam_type": "EndSem",
            "questions": [
                {
                    "id": 1,
                    "text": "Define polymorphism in Java.",
                    "family_id": 202,
                    "family_name": "Define polymorphism in Java.",
                    "marks": None,
                    "is_alternative": False,
                }
            ],
        },
        {
            "id": 21,
            "year": 2023,
            "exam_type": "EndSem",
            "questions": [
                {
                    "id": 2,
                    "text": "Explain polymorphism with example.",
                    "family_id": 202,
                    "family_name": "Define polymorphism in Java.",
                    "marks": None,
                    "is_alternative": False,
                }
            ],
        },
    ]

    dna = analyzer.analyze(exams)
    fam = next((f for f in dna.families if f.family_id == 202), None)
    assert fam is not None
    assert fam.total_marks is None
    assert fam.average_marks is None


def test_prediction_result_to_dict_contract():
    """Verify PredictionResult includes family_id, distinct_paper_count, and factual fields."""
    res = PredictionResult(
        target="family",
        name="What is OOP?",
        rank=1,
        score=0.85,
        confidence="HIGH",
        evidence={},
        probability=0.85,
        family_id=55,
        distinct_paper_count=4,
        total_marks_observed=20.0,
        average_marks=5.0,
        repetition_type="EXACT_REPEAT",
        observed_years=[2021, 2022, 2023],
        supporting_question_ids=[10, 20, 30],
    )
    d = res.to_dict()
    assert d["family_id"] == 55
    assert d["distinct_paper_count"] == 4
    assert d["total_marks_observed"] == 20.0
    assert d["average_marks"] == 5.0
    assert d["repetition_type"] == "EXACT_REPEAT"
    assert d["observed_years"] == [2021, 2022, 2023]
    assert d["supporting_question_ids"] == [10, 20, 30]


def test_single_family_evidence_endpoint(client, db_session):
    """Test GET /api/analytics/{course_id}/families/{family_id}."""
    course = db_session.query(Course).first()
    assert course is not None

    # Create exam, section, family, and questions
    exam1 = Exam(course_id=course.id, year=2022, assessment_type="EndSem")
    exam2 = Exam(course_id=course.id, year=2023, assessment_type="CLA-1")
    db_session.add_all([exam1, exam2])
    db_session.commit()

    sec1 = Section(exam_id=exam1.id, name="Part A")
    sec2 = Section(exam_id=exam2.id, name="Part B")
    db_session.add_all([sec1, sec2])
    db_session.commit()

    fam = QuestionFamily(
        canonical_name="Explain Kirchhoff's Voltage Law.",
        subject=course.name,
        repetition_type="FAMILY_REPEAT",
        first_seen_year=2022,
        latest_seen_year=2023,
    )
    db_session.add(fam)
    db_session.commit()

    q1 = Question(
        section_id=sec1.id,
        question_number="1",
        original_text="State Kirchhoff's Voltage Law (KVL).",
        marks=2.0,
        is_alternative=False,
        family_id=fam.id,
    )
    q2 = Question(
        section_id=sec2.id,
        question_number="5",
        original_text="Explain Kirchhoff's Voltage Law with circuit diagram.",
        marks=5.0,
        is_alternative=False,
        family_id=fam.id,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    # Query the single family endpoint
    resp = client.get(f"/api/analytics/{course.id}/families/{fam.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["family_id"] == fam.id
    assert data["canonical_name"] == "Explain Kirchhoff's Voltage Law."
    assert data["occurrence_count"] == 2
    assert data["distinct_paper_count"] == 2
    assert data["first_seen_year"] == 2022
    assert data["last_seen_year"] == 2023
    assert data["observed_years"] == [2022, 2023]
    assert data["average_marks"] == 3.5
    assert data["total_marks_observed"] == 7.0
    assert len(data["appearances"]) == 2
    assert len(data["timeline"]) >= 2


def test_dynamic_study_plan_fallback(client, db_session):
    """Test study plan falls back to family_predictions when topic_predictions is empty."""
    course = db_session.query(Course).first()
    assert course is not None

    # Add 2 exams, section, family, and questions
    exam1 = Exam(course_id=course.id, year=2022, assessment_type="EndSem")
    exam2 = Exam(course_id=course.id, year=2023, assessment_type="EndSem")
    db_session.add_all([exam1, exam2])
    db_session.commit()

    sec1 = Section(exam_id=exam1.id, name="Part A")
    sec2 = Section(exam_id=exam2.id, name="Part A")
    db_session.add_all([sec1, sec2])
    db_session.commit()

    fam = QuestionFamily(
        canonical_name="Derive Carnot cycle efficiency.",
        subject=course.name,
        repetition_type="EXACT_REPEAT",
        first_seen_year=2022,
        latest_seen_year=2023,
    )
    db_session.add(fam)
    db_session.commit()

    q1 = Question(
        section_id=sec1.id,
        question_number="3",
        original_text="Derive the efficiency of Carnot cycle.",
        marks=10.0,
        is_alternative=False,
        family_id=fam.id,
    )
    q2 = Question(
        section_id=sec2.id,
        question_number="4",
        original_text="Derive the efficiency of Carnot cycle.",
        marks=10.0,
        is_alternative=False,
        family_id=fam.id,
    )
    db_session.add_all([q1, q2])
    db_session.commit()

    # Call study plan endpoint
    resp = client.get(f"/api/study/plan/{course.name}")
    assert resp.status_code == 200
    data = resp.json()

    # Since no topics exist in the database for this course, plan_mode must be "family"
    assert data.get("plan_mode") == "family"
    assert len(data.get("topics", [])) > 0
    top = data["topics"][0]
    assert "Carnot" in top["name"]
    assert "appeared across" in top["reason"].lower() or "observed across" in top["reason"].lower()
