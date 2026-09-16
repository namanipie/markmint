import pytest
from backend.services.prediction.context import HistoricalContext
from backend.services.prediction.repository import HistoricalRepository
from backend.models.core import Course, Exam, Section, Question, QuestionFamily, QuestionFamilyMembership
from backend.core.database import SessionLocal, engine, Base

@pytest.fixture(scope="module")
def mock_db():
    # We will use an in-memory SQLite DB for this test
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    db = TestingSessionLocal()
    
    # Insert Mock Data
    c = Course(name="Test Course", code="TC101")
    db.add(c)
    db.commit()
    
    # Historical (2022)
    e_hist = Exam(course_id=c.id, year=2022, term="Spring")
    # Target (2023)
    e_targ = Exam(course_id=c.id, year=2023, term="Spring")
    # Future (2024)
    e_fut = Exam(course_id=c.id, year=2024, term="Spring")
    # Unanchored (None)
    e_un = Exam(course_id=c.id, year=None, term="Spring")
    
    db.add_all([e_hist, e_targ, e_fut, e_un])
    db.commit()
    
    # We add 1 question to each
    s_hist = Section(exam_id=e_hist.id, name="A")
    s_targ = Section(exam_id=e_targ.id, name="A")
    s_fut = Section(exam_id=e_fut.id, name="A")
    s_un = Section(exam_id=e_un.id, name="A")
    db.add_all([s_hist, s_targ, s_fut, s_un])
    db.commit()
    
    q_hist = Question(section_id=s_hist.id, original_text="Hist", question_number="1")
    q_targ = Question(section_id=s_targ.id, original_text="Targ", question_number="1")
    q_fut = Question(section_id=s_fut.id, original_text="Fut", question_number="1")
    q_un = Question(section_id=s_un.id, original_text="Un", question_number="1")
    db.add_all([q_hist, q_targ, q_fut, q_un])
    db.commit()
    
    yield db
    db.close()

def test_leakage_exams(mock_db):
    context = HistoricalContext(course_id=1, cutoff_year=2023)
    repo = HistoricalRepository(mock_db, context)
    
    exams = repo.get_historical_exams()
    assert len(exams) == 1
    assert exams[0].year == 2022
    
    # Verify we can fetch the target safely
    targ = repo.get_target_exams()
    assert len(targ) == 1
    assert targ[0].year == 2023

def test_leakage_questions(mock_db):
    context = HistoricalContext(course_id=1, cutoff_year=2023)
    repo = HistoricalRepository(mock_db, context)
    
    questions = repo.get_historical_questions()
    assert len(questions) == 1
    assert questions[0].original_text == "Hist"
    
def test_leakage_future_access(mock_db):
    # What if the cutoff is 2022?
    context = HistoricalContext(course_id=1, cutoff_year=2022)
    repo = HistoricalRepository(mock_db, context)
    
    # We shouldn't see 2022, 2023, 2024, or None
    exams = repo.get_historical_exams()
    assert len(exams) == 0
