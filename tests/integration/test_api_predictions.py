import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import Base
from backend.models.core import Course, Exam, Section, Question, QuestionFamily, QuestionFamilyMembership
import json

@pytest.fixture(scope="module")
def mock_db_api():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.core.database import get_db

    from sqlalchemy.pool import StaticPool
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Populate the DB
    db = TestingSessionLocal()
    course = Course(name="TestSubject", code="TS101")
    db.add(course)
    db.commit()
    
    fam = QuestionFamily(subject=course.name, canonical_name="TestFamily")
    db.add(fam)
    db.commit()
    
    exam1 = Exam(course_id=course.id, year=2022, term="Fall")
    exam2 = Exam(course_id=course.id, year=2023, term="Fall")
    db.add_all([exam1, exam2])
    db.commit()
    
    sec1 = Section(exam_id=exam1.id, name="A")
    sec2 = Section(exam_id=exam2.id, name="A")
    db.add_all([sec1, sec2])
    db.commit()
    
    # 2022 Q
    q1 = Question(section_id=sec1.id, question_number="1", original_text="Q1", marks=None, family_id=fam.id) # missing marks
    # 2023 Q
    q2 = Question(section_id=sec2.id, question_number="1", original_text="Q2", marks=None, family_id=fam.id) # missing marks
    db.add_all([q1, q2])
    db.commit()
    
    m1 = QuestionFamilyMembership(question_id=q1.id, family_id=fam.id, match_type="exact", similarity_score=1.0, decision_method="test", algorithm_version="1.0")
    m2 = QuestionFamilyMembership(question_id=q2.id, family_id=fam.id, match_type="exact", similarity_score=1.0, decision_method="test", algorithm_version="1.0")
    db.add_all([m1, m2])
    db.commit()
    
    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()

    # Override the dependency injected DB session
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()
    engine.dispose()


def test_api_predictions_dynamic_cutoff(mock_db_api):
    # Subject exists, latest year is 2023. Dynamic target_year should be 2024.
    res = mock_db_api.get("/api/predictions/TestSubject")
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    
    # 1. Prediction cutoff dynamically set
    assert data["target_year"] == 2024
    
    # 5. Empty topic data handled honestly
    # We inserted questions with NO topics. The API should not fabricate any topics.
    topics = [p for p in data["predictions"] if p["category"] == "topic"]
    assert len(topics) == 0
    
    # 6. Real family predictions remain functional
    families = [p for p in data["predictions"] if p["category"] == "family"]
    assert len(families) == 1
    assert families[0]["name"] == "TestFamily"
    
    # 8. Missing marks remain unavailable 
    # (API doesn't invent marks, it uses frequency, confidence should be INSUFFICIENT due to small sample size)
    assert families[0]["confidence"] in ["LOW", "INSUFFICIENT"]

def test_api_predictions_unknown_subject(mock_db_api):
    # 7. Unknown subject handled correctly
    res = mock_db_api.get("/api/predictions/DoesNotExist")
    assert res.status_code == 404
    assert res.json()["detail"] == "Subject not found"
