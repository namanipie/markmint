import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.core.database import Base
from backend.models.core import Course, Exam, Section, Question, QuestionFamily, QuestionFamilyMembership


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_question_family_membership_uniqueness(test_db):
    course = Course(name="Test Subject", code="TEST101")
    test_db.add(course)
    test_db.flush()

    exam = Exam(course_id=course.id, year=2023, assessment_type="Cycle Test 1")
    test_db.add(exam)
    test_db.flush()

    section = Section(exam_id=exam.id, name="Section A")
    test_db.add(section)
    test_db.flush()

    question = Question(section_id=section.id, question_number="1", original_text="What is a hash table?")
    test_db.add(question)
    test_db.flush()

    family1 = QuestionFamily(canonical_name="Hash Table Definition", subject=course.name)
    family2 = QuestionFamily(canonical_name="Hash Map Concepts", subject=course.name)
    test_db.add_all([family1, family2])
    test_db.flush()

    # 1. First membership assignment succeeds
    mem1 = QuestionFamilyMembership(
        question_id=question.id,
        family_id=family1.id,
        match_type="EXACT",
        similarity_score=1.0,
        decision_method="rule_based",
        algorithm_version="v1.0",
    )
    test_db.add(mem1)
    test_db.commit()

    assert test_db.query(QuestionFamilyMembership).count() == 1

    # 2. Second membership assignment for SAME question_id MUST fail with IntegrityError
    mem2 = QuestionFamilyMembership(
        question_id=question.id,
        family_id=family2.id,
        match_type="APPROXIMATE",
        similarity_score=0.9,
        decision_method="rule_based",
        algorithm_version="v1.0",
    )
    test_db.add(mem2)
    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()
    assert test_db.query(QuestionFamilyMembership).count() == 1
