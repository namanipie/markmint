import pytest
from backend.services.prediction.engine import ExamScopeCombinedModel, PredictionResult
from backend.services.prediction.context import PredictionTarget
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.study_intelligence import StudyIntelligenceService, StudyPriority


def test_explainable_predictions_structure_and_reasons():
    # 3 exams dataset with recurring Trees and high marks
    exams = [
        {
            "id": "e1", "year": 2021, "exam_type": "FINAL",
            "questions": [
                {"id": "q1", "topic": "Trees", "marks": 20.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5}
            ]
        },
        {
            "id": "e2", "year": 2022, "exam_type": "FINAL",
            "questions": [
                {"id": "q2", "topic": "Trees", "marks": 25.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.6}
            ]
        },
        {
            "id": "e3", "year": 2023, "exam_type": "FINAL",
            "questions": [
                {"id": "q3", "topic": "Trees", "marks": 25.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.7},
                {"id": "q4", "topic": "Graphs", "marks": 5.0, "is_alternative": False, "question_type": "SHORT", "repetition_type": "singleton", "family_name": None, "difficulty": 0.3}
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)

    assert len(preds) >= 1
    top = preds[0]
    assert top.name == "Trees"

    # Verify structured explainability fields
    assert hasattr(top, "prediction_score")
    assert hasattr(top, "probability")
    assert hasattr(top, "confidence")
    assert hasattr(top, "historical_occurrences")
    assert hasattr(top, "recent_occurrences")
    assert hasattr(top, "marks_seen")
    assert hasattr(top, "reason_codes")
    assert hasattr(top, "explanation")

    # Trees appeared in 3 questions with 70 marks total
    assert top.historical_occurrences == 3
    assert top.marks_seen == 70.0
    assert top.confidence == "HIGH"

    # Verify machine-readable reason codes
    assert "HIGH_FREQUENCY" in top.reason_codes
    assert "RECENTLY_REPEATED" in top.reason_codes
    assert "HIGH_MARK_WEIGHT" in top.reason_codes
    assert "SUFFICIENT_HISTORY" in top.reason_codes

    # Verify dictionary export contains all required frontend fields
    d = top.to_dict()
    assert d["name"] == "Trees"
    assert d["probability"] > 0.5
    assert d["confidence"] == "HIGH"
    assert d["historical_occurrences"] == 3
    assert "Strong recurrence signal" in d["explanation"]


def test_probability_vs_confidence_vs_priority_distinction():
    # Low evidence case: only 1 exam, 1 question
    exams_sparse = [
        {
            "id": "e1", "year": 2023, "exam_type": "CT1",
            "questions": [
                {"id": "q1", "topic": "Matrices", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.4}
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams_sparse)
    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    assert len(preds) == 1
    p = preds[0]

    # Model score may be high because it was the only question (100% of that exam)
    # BUT confidence MUST be INSUFFICIENT due to sparse sample
    assert p.confidence == "INSUFFICIENT"
    assert "LOW_EVIDENCE" in p.reason_codes


def test_student_mastery_affects_study_priority():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.core.database import Base
    from backend.models.core import Course, Topic, Unit, Syllabus, StudentTopicProgress

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    c = Course(name="Calculus", code="CALC101")
    db.add(c)
    db.commit()
    syl = Syllabus(course_id=c.id, version="v1")
    db.add(syl)
    db.commit()
    u = Unit(syllabus_id=syl.id, name="Unit 1", number=1)
    db.add(u)
    db.commit()
    t = Topic(unit_id=u.id, name="Integration")
    db.add(t)
    db.commit()

    service = StudyIntelligenceService(db)

    pred = PredictionResult(
        target="topic",
        name="Integration",
        rank=1,
        score=0.85,
        confidence="HIGH",
        evidence={"occurrences": 5, "recent_freq": 0.4},
        reason_codes=["HIGH_FREQUENCY", "RECENTLY_REPEATED"]
    )

    # 1. Unstudied student: Priority should be VERY_HIGH
    unstudied_priority = service.calculate_study_priority(pred, c.id, student_id="student_new")
    assert unstudied_priority.priority == StudyPriority.VERY_HIGH
    assert "STUDENT_UNSTUDIED" in unstudied_priority.reason_codes

    # 2. Mastered student: Completed with 100% accuracy
    progress = StudentTopicProgress(
        student_id="student_master",
        topic_id=t.id,
        status="COMPLETED",
        practice_attempted=5,
        practice_correct=5
    )
    db.add(progress)
    db.commit()

    mastered_priority = service.calculate_study_priority(pred, c.id, student_id="student_master")
    # Priority should be lowered from VERY_HIGH to HIGH due to mastery
    assert mastered_priority.priority == StudyPriority.HIGH
    assert "STUDENT_MASTERED" in mastered_priority.reason_codes
    assert "deprioritized" in " ".join(mastered_priority.reasons).lower()
