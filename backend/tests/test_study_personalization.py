import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import Course, Topic, Unit, Syllabus, StudentTopicProgress
from backend.services.prediction.engine import PredictionResult
from backend.services.study_intelligence import StudyIntelligenceService, StudyPriority, PriorityResult


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_exam_schedule_duration_conservation(test_db):
    service = StudyIntelligenceService(test_db)
    priorities = [
        PriorityResult(topic="Calculus", priority=StudyPriority.VERY_HIGH, prediction_score=0.9, reasons=[], resources=[], topic_id=1),
        PriorityResult(topic="Linear Algebra", priority=StudyPriority.HIGH, prediction_score=0.8, reasons=[], resources=[], topic_id=2),
        PriorityResult(topic="Physics", priority=StudyPriority.MEDIUM, prediction_score=0.6, reasons=[], resources=[], topic_id=3),
    ]

    for days in [1, 2, 3, 5, 7, 14, 21, 30, 45, 60]:
        target_date = date.today() + timedelta(days=days)
        target_date_str = target_date.strftime("%Y-%m-%d")
        schedule = service.generate_exam_schedule(priorities, target_date_str)

        assert schedule is not None
        assert schedule["days_remaining"] == days
        assert len(schedule["phases"]) > 0

        # Strict duration conservation invariant
        total_phase_days = sum(phase["duration_days"] for phase in schedule["phases"])
        assert total_phase_days == days, f"Failed conservation for {days} days: got {total_phase_days}"


def test_coverage_gap_decomposition(test_db):
    course = Course(name="Data Structures", code="CS201")
    test_db.add(course)
    test_db.commit()

    syllabus = Syllabus(course_id=course.id, version="v1")
    test_db.add(syllabus)
    test_db.commit()

    unit = Unit(syllabus_id=syllabus.id, name="Trees & Graphs", number=1)
    test_db.add(unit)
    test_db.commit()

    t1 = Topic(unit_id=unit.id, name="Binary Trees")
    t2 = Topic(unit_id=unit.id, name="Graphs")
    t3 = Topic(unit_id=unit.id, name="Heaps")
    test_db.add_all([t1, t2, t3])
    test_db.commit()

    # Add progress: t1 mastered, t2 in progress, t3 unstudied
    p1 = StudentTopicProgress(student_id="student_1", topic_id=t1.id, status="COMPLETED", practice_attempted=5, practice_correct=5)
    p2 = StudentTopicProgress(student_id="student_1", topic_id=t2.id, status="IN_PROGRESS", practice_attempted=3, practice_correct=1)
    test_db.add_all([p1, p2])
    test_db.commit()

    service = StudyIntelligenceService(test_db)
    predictions = [
        PredictionResult(target="topic", name="Binary Trees", rank=1, score=0.9, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Graphs", rank=2, score=0.8, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Heaps", rank=3, score=0.7, confidence="MEDIUM", evidence={}),
    ]

    gap = service.calculate_coverage_gap(predictions, course.id, student_id="student_1")

    assert gap["total_predicted_topics"] == 3
    assert gap["mastered_topics"] == 1
    assert gap["in_progress_topics"] == 1
    assert gap["unstudied_topics"] == 1
    # Coverage should be (1.0 * 1 + 0.5 * 1) / 3 * 100 = 50.0%
    assert gap["student_preparation_coverage"] == 50.0


def test_recommended_action_transitions(test_db):
    course = Course(name="Algorithms", code="CS301")
    test_db.add(course)
    test_db.commit()

    syllabus = Syllabus(course_id=course.id, version="v1")
    test_db.add(syllabus)
    test_db.commit()

    unit = Unit(syllabus_id=syllabus.id, name="Sorting", number=1)
    test_db.add(unit)
    test_db.commit()

    t1 = Topic(unit_id=unit.id, name="QuickSort")
    test_db.add(t1)
    test_db.commit()

    service = StudyIntelligenceService(test_db)

    # 1. Very high priority unstudied topic -> DEEP_STUDY_URGENT
    pred_high = PredictionResult(target="topic", name="QuickSort", rank=1, score=0.9, confidence="HIGH", evidence={})
    p_urgent = service.calculate_study_priority(pred_high, course.id, student_id="student_a")
    assert p_urgent.recommended_action == "DEEP_STUDY_URGENT"
    assert p_urgent.topic_id == t1.id

    # 2. Mastered topic -> MAINTAIN_AND_REVIEW
    prog = StudentTopicProgress(student_id="student_b", topic_id=t1.id, status="COMPLETED", practice_attempted=10, practice_correct=10)
    test_db.add(prog)
    test_db.commit()

    p_mastered = service.calculate_study_priority(pred_high, course.id, student_id="student_b")
    assert p_mastered.recommended_action == "MAINTAIN_AND_REVIEW"
