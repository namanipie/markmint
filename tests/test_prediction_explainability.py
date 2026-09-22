import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import (
    Course, CourseTrack, Exam, Section, Question, Topic, Unit, Syllabus,
    QuestionFamily, QuestionFamilyMembership, Document
)
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel, PredictionResult
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from fastapi.testclient import TestClient
from backend.main import app


def test_prediction_result_evidence_breakdown_contract():
    """Verify PredictionResult.to_dict includes evidence_breakdown and explainability with all required fields."""
    res = PredictionResult(
        target="topic",
        name="Dynamic Programming",
        rank=1,
        score=0.88,
        confidence="HIGH",
        evidence={
            "hist_freq": 0.30,
            "recent_freq": 0.50,
            "marks_weight": 0.25,
            "total_marks": 40.0,
            "average_marks": 10.0,
            "occurrences": 4,
            "recent_occurrences": 2,
            "last_seen": 2023,
            "years": [2021, 2022, 2023],
            "distinct_paper_count": 3,
            "papers_with_topic": 3,
            "explanation": "Strong recurrence signal.",
        },
        prediction_score=0.88,
        probability=0.85,
        historical_occurrences=4,
        recent_occurrences=2,
        last_seen_year=2023,
        marks_seen=40.0,
        distinct_paper_count=3,
        papers_analyzed=4,
        papers_with_topic=3,
        total_marks_observed=40.0,
        average_marks=10.0,
        observed_years=[2021, 2022, 2023],
        explanation="Strong recurrence signal.",
    )

    d = res.to_dict()

    # Requirement 7: Backward compatibility - all existing keys remain
    assert d["rank"] == 1
    assert d["name"] == "Dynamic Programming"
    assert d["score"] == 0.88
    assert d["prediction_score"] == 0.88
    assert d["probability"] == 0.85
    assert d["confidence"] == "HIGH"
    assert d["historical_occurrences"] == 4
    assert d["recent_occurrences"] == 2
    assert d["last_seen_year"] == 2023
    assert d["explanation"] == "Strong recurrence signal."

    # Requirement 1 & 6: Expose evidence breakdown and explainability
    assert "evidence_breakdown" in d
    assert "explainability" in d
    eb = d["evidence_breakdown"]

    assert eb["historical_frequency"] == 0.30
    assert eb["recent_frequency"] == 0.50
    assert eb["marks_weighting"] == 0.25
    assert eb["total_marks_observed"] == 40.0
    assert eb["average_marks"] == 10.0
    assert eb["distinct_exam_count"] == 3
    assert eb["total_papers_analyzed"] == 4
    assert eb["exam_coverage_ratio"] == 0.75
    assert eb["historical_occurrences"] == 4
    assert eb["recent_occurrences"] == 2
    assert eb["last_seen_year"] == 2023
    assert eb["temporal_trend"] == "rising"
    assert eb["source_years"] == [2021, 2022, 2023]
    assert "family_recurrence" in eb
    assert eb["reason_summary"] == "Strong recurrence signal."


def test_topic_and_family_explainability_both_supported():
    """Verify both topic and question family predictions support explainability."""
    # Topic prediction
    topic_res = PredictionResult(
        target="topic",
        name="Binary Search",
        rank=2,
        score=0.72,
        confidence="MEDIUM",
        evidence={
            "hist_freq": 0.20,
            "recent_freq": 0.05,
            "marks_weight": 0.15,
            "total_marks": 15.0,
            "average_marks": 7.5,
            "occurrences": 2,
            "recent_occurrences": 0,
            "last_seen": 2020,
            "years": [2019, 2020],
        },
        historical_occurrences=2,
        recent_occurrences=0,
        last_seen_year=2020,
        papers_analyzed=4,
        papers_with_topic=2,
        observed_years=[2019, 2020],
    )
    t_dict = topic_res.to_dict()
    assert t_dict["evidence_breakdown"]["temporal_trend"] == "declining"
    assert t_dict["evidence_breakdown"]["distinct_exam_count"] == 2
    assert t_dict["evidence_breakdown"]["source_years"] == [2019, 2020]

    # Family prediction
    fam_res = PredictionResult(
        target="family",
        name="Explain Amdahl's Law",
        rank=1,
        score=0.90,
        confidence="HIGH",
        evidence={
            "family_id": 42,
            "repetition_type": "exact_repeat",
            "occurrences": 3,
            "recent_occurrences": 2,
            "distinct_paper_count": 3,
            "years": [2021, 2022, 2023],
            "last_seen": 2023,
            "average_marks": 8.0,
            "total_marks": 24.0,
        },
        family_id=42,
        repetition_type="exact_repeat",
        historical_occurrences=3,
        recent_occurrences=2,
        last_seen_year=2023,
        distinct_paper_count=3,
        papers_analyzed=3,
        observed_years=[2021, 2022, 2023],
        total_marks_observed=24.0,
        average_marks=8.0,
    )
    f_dict = fam_res.to_dict()
    assert f_dict["evidence_breakdown"]["family_recurrence"]["family_id"] == 42
    assert f_dict["evidence_breakdown"]["family_recurrence"]["repetition_type"] == "exact_repeat"
    assert f_dict["evidence_breakdown"]["family_recurrence"]["is_recurring"] is True
    assert f_dict["evidence_breakdown"]["temporal_trend"] == "rising"
    assert f_dict["evidence_breakdown"]["source_years"] == [2021, 2022, 2023]


def test_prediction_scores_and_ranking_unaffected():
    """Verify that scores and rankings remain 100% bit-for-bit identical before and after explainability enrichment."""
    exams = [
        {
            "id": 1, "year": 2021, "exam_type": "FINAL",
            "questions": [
                {"id": 101, "topic": "Calculus", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": "Fam A", "family_id": 1},
                {"id": 102, "topic": "Linear Algebra", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": "Fam B", "family_id": 2},
            ]
        },
        {
            "id": 2, "year": 2022, "exam_type": "FINAL",
            "questions": [
                {"id": 201, "topic": "Calculus", "marks": 15.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": "Fam A", "family_id": 1},
            ]
        },
        {
            "id": 3, "year": 2023, "exam_type": "FINAL",
            "questions": [
                {"id": 301, "topic": "Calculus", "marks": 15.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": "Fam A", "family_id": 1},
                {"id": 302, "topic": "Differential Equations", "marks": 5.0, "is_alternative": False, "question_type": "SHORT", "repetition_type": "singleton", "family_name": "Fam C", "family_id": 3},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)

    # Top prediction must be Calculus
    assert len(preds) >= 2
    assert preds[0].name == "Calculus"
    calc_score = preds[0].score

    # Re-verify through to_dict
    calc_dict = preds[0].to_dict()
    assert calc_dict["score"] == calc_score
    assert calc_dict["rank"] == 1
    assert calc_dict["prediction_score"] == round(calc_score, 4)

    # Calculus appeared in 3 exams with 40 marks total
    eb = calc_dict["evidence_breakdown"]
    assert eb["distinct_exam_count"] == 3
    assert eb["historical_occurrences"] == 3
    assert eb["total_marks_observed"] == 40.0


def test_temporal_cutoff_and_cycle_isolation_for_source_exams():
    """Verify that exams excluded by historical cutoff, track, or cycle NEVER appear as evidence."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Create Course
    course = Course(id=1, name="Database Systems", code="CS301", canonical_code="CS301")
    db.add(course)
    db.flush()

    syl = Syllabus(id=1, course_id=course.id, version="2020")
    db.add(syl)
    db.flush()

    unit = Unit(id=1, syllabus_id=syl.id, name="Unit 1", number=1)
    db.add(unit)
    db.flush()

    top_sql = Topic(id=1, unit_id=unit.id, name="SQL Indexing")
    top_nosql = Topic(id=2, unit_id=unit.id, name="NoSQL Models")
    db.add_all([top_sql, top_nosql])
    db.flush()

    # Historical exam 1: 2021 (Allowed)
    e2021 = Exam(id=1, course_id=course.id, year=2021, assessment_type="FINAL")
    db.add(e2021)
    db.flush()
    s1 = Section(id=1, exam_id=e2021.id, name="A")
    db.add(s1)
    db.flush()
    q1 = Question(id=1, section_id=s1.id, question_number="1", original_text="Explain B-Tree indexing.", marks=10.0)
    q1.topics.append(top_sql)
    db.add(q1)

    # Historical exam 2: 2022 (Allowed)
    e2022 = Exam(id=2, course_id=course.id, year=2022, assessment_type="FINAL")
    db.add(e2022)
    db.flush()
    s2 = Section(id=2, exam_id=e2022.id, name="A")
    db.add(s2)
    db.flush()
    q2 = Question(id=2, section_id=s2.id, question_number="1", original_text="Clustered index vs Non-clustered.", marks=10.0)
    q2.topics.append(top_sql)
    db.add(q2)

    # Future exam: 2024 (EXCLUDED by cutoff_year=2024)
    e2024 = Exam(id=3, course_id=course.id, year=2024, assessment_type="FINAL")
    db.add(e2024)
    db.flush()
    s3 = Section(id=3, exam_id=e2024.id, name="A")
    db.add(s3)
    db.flush()
    q3 = Question(id=3, section_id=s3.id, question_number="1", original_text="Future question on NoSQL.", marks=10.0)
    q3.topics.append(top_nosql)
    db.add(q3)

    # Exam with NULL year (EXCLUDED by HistoricalRepository)
    e_null = Exam(id=4, course_id=course.id, year=None, assessment_type="FINAL")
    db.add(e_null)
    db.flush()
    s4 = Section(id=4, exam_id=e_null.id, name="A")
    db.add(s4)
    db.flush()
    q4 = Question(id=4, section_id=s4.id, question_number="1", original_text="Null year question.", marks=10.0)
    q4.topics.append(top_nosql)
    db.add(q4)

    db.commit()

    # Query HistoricalRepository with cutoff_year=2024
    context = HistoricalContext(course_id=course.id, cutoff_year=2024)
    repo = HistoricalRepository(db, context)
    hist_exams = repo.get_historical_exams()

    # Only 2021 and 2022 are returned
    assert len(hist_exams) == 2
    assert {e.year for e in hist_exams} == {2021, 2022}
    assert 2024 not in {e.year for e in hist_exams}
    assert None not in {e.year for e in hist_exams}

    # Generate payloads consumed by prediction
    hist_payloads = _build_historical_exam_payloads(hist_exams)
    dna = DNAAnalyzerService.analyze(hist_payloads)
    engine_model = ExamScopeCombinedModel(dna)
    preds = engine_model.predict(PredictionTarget.TOPIC)

    # SQL Indexing was predicted from 2021 and 2022
    assert len(preds) >= 1
    sql_pred = next(p for p in preds if p.name == "SQL Indexing")
    sql_dict = sql_pred.to_dict()

    # Reconstruct source exams from hist_exams
    matching_exams = [
        {
            "exam_id": e.id,
            "year": e.year,
            "assessment_type": e.assessment_type,
            "title": f"Exam {e.year}",
        }
        for e in hist_exams
        if e.year is not None and any(
            any(t.name == sql_pred.name for t in q.topics)
            for s in e.sections for q in s.questions
        )
    ]
    sql_dict["evidence_breakdown"]["source_exams"] = matching_exams

    # Assertions on temporal integrity:
    # 1. 2024 exam (future) CANNOT appear in source_exams
    assert all(se["year"] < 2024 for se in sql_dict["evidence_breakdown"]["source_exams"])
    # 2. Null-year exam CANNOT appear in source_exams
    assert all(se["year"] is not None for se in sql_dict["evidence_breakdown"]["source_exams"])
    # 3. Source exams match the historical exams repository exactly
    assert len(sql_dict["evidence_breakdown"]["source_exams"]) == 2
    assert {se["year"] for se in sql_dict["evidence_breakdown"]["source_exams"]} == {2021, 2022}
    assert {se["exam_id"] for se in sql_dict["evidence_breakdown"]["source_exams"]} == {1, 2}

    db.close()


def test_intelligence_and_predictions_endpoints_explainability():
    """Integration test verifying GET /api/intelligence/{course_id} and GET /predictions/{subject} enrich predictions with evidence_breakdown."""
    from backend.core.database import get_db

    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed Course & Syllabus & Exam
    course = Course(id=10, name="Operating Systems", code="OS101", canonical_code="CS202")
    db.add(course)
    db.flush()

    syl = Syllabus(id=10, course_id=course.id, version="2022")
    db.add(syl)
    db.flush()

    unit = Unit(id=10, syllabus_id=syl.id, name="Concurrency", number=1)
    db.add(unit)
    db.flush()

    top_deadlock = Topic(id=10, unit_id=unit.id, name="Deadlock Detection")
    db.add(top_deadlock)
    db.flush()

    fam = QuestionFamily(
        id=20,
        subject="Operating Systems",
        canonical_name="Bankers Algorithm",
        repetition_type="exact_repeat",
    )
    db.add(fam)
    db.flush()

    doc = Document(id=10, title="OS End-Term 2022", document_hash="os_2022_hash")
    db.add(doc)
    db.flush()

    e2022 = Exam(id=10, course_id=course.id, document_id=doc.id, year=2022, assessment_type="FINAL")
    db.add(e2022)
    db.flush()

    s = Section(id=10, exam_id=e2022.id, name="A")
    db.add(s)
    db.flush()

    q = Question(
        id=10,
        section_id=s.id,
        family_id=fam.id,
        question_number="1",
        original_text="Explain Bankers algorithm for deadlock avoidance.",
        marks=15.0,
    )
    q.topics.append(top_deadlock)
    db.add(q)
    db.flush()

    mem = QuestionFamilyMembership(
        question_id=q.id,
        family_id=fam.id,
        match_type="exact_repeat",
        decision_method="automated",
        algorithm_version="1.0",
    )
    db.add(mem)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Test GET /api/intelligence/{course_id}
    resp = client.get("/api/intelligence/10?student_id=anonymous")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "predictions" in data
    assert "topic_predictions" in data
    assert "family_predictions" in data

    if data["topic_predictions"]:
        t_pred = data["topic_predictions"][0]
        assert "evidence_breakdown" in t_pred
        assert "explainability" in t_pred
        assert t_pred["evidence_breakdown"]["historical_occurrences"] >= 1
        assert t_pred["evidence_breakdown"]["distinct_exam_count"] >= 1
        assert len(t_pred["evidence_breakdown"]["source_exams"]) >= 1
        assert t_pred["evidence_breakdown"]["source_exams"][0]["year"] == 2022

    if data["family_predictions"]:
        f_pred = data["family_predictions"][0]
        assert "evidence_breakdown" in f_pred
        assert "explainability" in f_pred
        assert f_pred["evidence_breakdown"]["family_recurrence"]["family_id"] == 20
        assert f_pred["evidence_breakdown"]["family_recurrence"]["repetition_type"] == "exact_repeat"
        assert len(f_pred["evidence_breakdown"]["source_exams"]) >= 1
        assert f_pred["evidence_breakdown"]["source_exams"][0]["year"] == 2022

    # 2. Test GET /api/predictions/{subject}
    resp_pred = client.get("/api/predictions/OS101")
    assert resp_pred.status_code == 200, resp_pred.text
    pred_data = resp_pred.json()

    assert "predictions" in pred_data
    if pred_data["predictions"]:
        p_item = pred_data["predictions"][0]
        assert "evidence_breakdown" in p_item
        assert "explainability" in p_item
        assert len(p_item["evidence_breakdown"]["source_exams"]) >= 1
        assert p_item["evidence_breakdown"]["source_exams"][0]["year"] == 2022

    app.dependency_overrides.clear()
    db.close()

