import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import Base, get_db
from backend.models.core import (
    Course, CourseTrack, Exam, Section, Question, Topic, Unit, Syllabus,
    Document, QuestionFamily, QuestionFamilyMembership
)
from backend.services.corpus_health import CorpusHealthService


@pytest.fixture(scope="module")
def health_test_db():
    """Create an isolated in-memory SQLite database populated with multi-course, multi-track, unknown-year data."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # --- 1. Course 1: Mathematics (Single track, with gap year and unknown year) ---
    course_math = Course(id=1, name="Mathematics", code="MATH101", canonical_code="21MAB101T")
    db.add(course_math)
    db.flush()

    syl_math = Syllabus(id=1, course_id=course_math.id, version="2021")
    db.add(syl_math)
    db.flush()

    unit1 = Unit(id=1, syllabus_id=syl_math.id, name="Linear Algebra", number=1)
    unit2 = Unit(id=2, syllabus_id=syl_math.id, name="Calculus", number=2)
    db.add_all([unit1, unit2])
    db.flush()

    top_matrices = Topic(id=1, unit_id=unit1.id, name="Matrices")
    top_eigen = Topic(id=2, unit_id=unit1.id, name="Eigenvalues")  # Will remain unobserved
    top_limits = Topic(id=3, unit_id=unit2.id, name="Limits")
    top_derivs = Topic(id=4, unit_id=unit2.id, name="Derivatives")
    db.add_all([top_matrices, top_eigen, top_limits, top_derivs])
    db.flush()

    fam_matrix = QuestionFamily(
        id=1,
        subject="Mathematics",
        canonical_name="Matrix Inversion",
        repetition_type="exact_repeat",
    )
    fam_deriv = QuestionFamily(
        id=2,
        subject="Mathematics",
        canonical_name="Chain Rule",
        repetition_type="singleton",
    )
    db.add_all([fam_matrix, fam_deriv])
    db.flush()

    doc_ok = Document(id=1, title="Math 2021 CT1", document_hash="hash_m1", extraction_status="extracted")
    doc_failed = Document(id=2, title="Math 2022 CT1 Scanned Corrupted", document_hash="hash_m2", extraction_status="failed")
    db.add_all([doc_ok, doc_failed])
    db.flush()

    # Math Exam 1: 2021, CT1
    e1 = Exam(id=1, course_id=course_math.id, document_id=doc_ok.id, year=2021, assessment_type="CT1")
    db.add(e1)
    db.flush()
    s1 = Section(id=1, exam_id=e1.id, name="Part A")
    db.add(s1)
    db.flush()
    q1 = Question(id=1, section_id=s1.id, question_number="1", original_text="Find inverse of A", marks=10.0, family_id=fam_matrix.id, question_type="LONG")
    q1.topics.append(top_matrices)
    q2 = Question(id=2, section_id=s1.id, question_number="2", original_text="Compute lim x->0", marks=5.0, question_type="SHORT")
    q2.topics.append(top_limits)
    db.add_all([q1, q2])

    # Math Exam 2: 2022, CT1
    e2 = Exam(id=2, course_id=course_math.id, document_id=doc_failed.id, year=2022, assessment_type="CT1")
    db.add(e2)
    db.flush()
    s2 = Section(id=2, exam_id=e2.id, name="Part A")
    db.add(s2)
    db.flush()
    q3 = Question(id=3, section_id=s2.id, question_number="1", original_text="Find inverse of B", marks=10.0, family_id=fam_matrix.id, question_type="LONG")
    q3.topics.append(top_matrices)
    q4 = Question(id=4, section_id=s2.id, question_number="2", original_text="Differentiate sin(x^2)", marks=5.0, family_id=fam_deriv.id, question_type="SHORT")
    q4.topics.append(top_derivs)
    db.add_all([q3, q4])

    # Math Exam 3: 2024, FINAL (Note 2023 is missing!)
    e3 = Exam(id=3, course_id=course_math.id, year=2024, assessment_type="FINAL")
    db.add(e3)
    db.flush()
    s3 = Section(id=3, exam_id=e3.id, name="Part A")
    db.add(s3)
    db.flush()
    q5 = Question(id=5, section_id=s3.id, question_number="1", original_text="Properties of determinants", marks=10.0, question_type="LONG")
    q5.topics.append(top_matrices)
    # q6 is unresolved: no topics assigned!
    q6 = Question(id=6, section_id=s3.id, question_number="2", original_text="Unresolved question without topic", marks=5.0, needs_review=True)
    db.add_all([q5, q6])

    # Math Exam 4: Unknown year (year=None)
    e4 = Exam(id=4, course_id=course_math.id, year=None, assessment_type="CT2")
    db.add(e4)
    db.flush()
    s4 = Section(id=4, exam_id=e4.id, name="Part A")
    db.add(s4)
    db.flush()
    q7 = Question(id=7, section_id=s4.id, question_number="1", original_text="Unknown year matrix question", marks=10.0)
    q7.topics.append(top_matrices)
    db.add(q7)

    # --- 2. Course 2: Physics (Isolated course) ---
    course_phys = Course(id=2, name="Physics", code="PHYS101", canonical_code="21PYB101T")
    db.add(course_phys)
    db.flush()

    syl_phys = Syllabus(id=2, course_id=course_phys.id, version="2021")
    db.add(syl_phys)
    db.flush()
    unit_phys = Unit(id=3, syllabus_id=syl_phys.id, name="Optics", number=1)
    db.add(unit_phys)
    db.flush()
    top_optics = Topic(id=5, unit_id=unit_phys.id, name="Optics & Lasers")
    db.add(top_optics)
    db.flush()

    e5 = Exam(id=5, course_id=course_phys.id, year=2022, assessment_type="FINAL")
    db.add(e5)
    db.flush()
    s5 = Section(id=5, exam_id=e5.id, name="Section 1")
    db.add(s5)
    db.flush()
    q8 = Question(id=8, section_id=s5.id, question_number="1", original_text="Explain Laser stimulation", marks=15.0)
    q8.topics.append(top_optics)
    db.add(q8)

    # --- 3. Course 3: Foreign Languages (Multi-track course) ---
    course_lang = Course(id=3, name="Foreign Languages", code="LANG101", canonical_code="21FLB101T")
    db.add(course_lang)
    db.flush()

    track_ger = CourseTrack(id=1, course_id=course_lang.id, track_key="german", track_name="German", track_code="GER101")
    track_fre = CourseTrack(id=2, course_id=course_lang.id, track_key="french", track_name="French", track_code="FRE101")
    db.add_all([track_ger, track_fre])
    db.flush()

    syl_ger = Syllabus(id=3, course_id=course_lang.id, track_id=track_ger.id, version="2021")
    syl_fre = Syllabus(id=4, course_id=course_lang.id, track_id=track_fre.id, version="2021")
    db.add_all([syl_ger, syl_fre])
    db.flush()

    unit_ger = Unit(id=4, syllabus_id=syl_ger.id, name="German Grammar", number=1)
    unit_fre = Unit(id=5, syllabus_id=syl_fre.id, name="French Grammar", number=1)
    db.add_all([unit_ger, unit_fre])
    db.flush()

    top_ger = Topic(id=6, unit_id=unit_ger.id, name="German Verbs")
    top_fre = Topic(id=7, unit_id=unit_fre.id, name="French Verbs")
    db.add_all([top_ger, top_fre])
    db.flush()

    # German exams: 2 exams, 2 questions
    e_ger1 = Exam(id=6, course_id=course_lang.id, track_id=track_ger.id, year=2021, assessment_type="FINAL")
    e_ger2 = Exam(id=7, course_id=course_lang.id, track_id=track_ger.id, year=2022, assessment_type="FINAL")
    db.add_all([e_ger1, e_ger2])
    db.flush()
    s_ger1 = Section(id=6, exam_id=e_ger1.id, name="A")
    s_ger2 = Section(id=7, exam_id=e_ger2.id, name="A")
    db.add_all([s_ger1, s_ger2])
    db.flush()
    q_ger1 = Question(id=9, section_id=s_ger1.id, question_number="1", original_text="Konjugieren Sie sein", marks=5.0)
    q_ger1.topics.append(top_ger)
    q_ger2 = Question(id=10, section_id=s_ger2.id, question_number="1", original_text="Konjugieren Sie haben", marks=5.0)
    q_ger2.topics.append(top_ger)
    db.add_all([q_ger1, q_ger2])

    # French exams: 1 exam, 1 question
    e_fre1 = Exam(id=8, course_id=course_lang.id, track_id=track_fre.id, year=2023, assessment_type="FINAL")
    db.add(e_fre1)
    db.flush()
    s_fre1 = Section(id=8, exam_id=e_fre1.id, name="A")
    db.add(s_fre1)
    db.flush()
    q_fre1 = Question(id=11, section_id=s_fre1.id, question_number="1", original_text="Conjuguez etre", marks=5.0)
    q_fre1.topics.append(top_fre)
    db.add(q_fre1)

    db.commit()
    yield db
    db.close()


def test_health_course_isolation(health_test_db):
    """Verify Course A data does not bleed into Course B."""
    db = health_test_db
    math_course = db.query(Course).filter(Course.id == 1).first()
    phys_course = db.query(Course).filter(Course.id == 2).first()

    math_health = CorpusHealthService.get_course_health(db, math_course)
    phys_health = CorpusHealthService.get_course_health(db, phys_course)

    # Math has 4 exams, Physics has 1 exam
    assert math_health["exams"]["total_exams"] == 4
    assert phys_health["exams"]["total_exams"] == 1

    # Math has 7 questions, Physics has 1 question
    assert math_health["questions"]["total_extracted"] == 7
    assert phys_health["questions"]["total_extracted"] == 1

    # Physics question has Optics topic; Math never sees Optics
    assert "Optics & Lasers" not in math_health["topics"]["unobserved_topic_names"]
    assert phys_health["topics"]["observed_topics"] == 1
    assert phys_health["topics"]["syllabus_topics_total"] == 1

    # Math has 2 families; Physics has 0 families
    assert math_health["question_families"]["total_families"] == 2
    assert phys_health["question_families"]["total_families"] == 0


def test_health_correct_aggregation(health_test_db):
    """Verify exact count of exams, questions, topics, families, and failures match database rows."""
    db = health_test_db
    math_course = db.query(Course).filter(Course.id == 1).first()
    h = CorpusHealthService.get_course_health(db, math_course)

    # Exams breakdown
    assert h["exams"]["total_exams"] == 4
    assert h["exams"]["valid_year_exams"] == 3
    assert h["exams"]["unknown_year_exams"] == 1
    assert h["exams"]["years_observed"] == [2021, 2022, 2024]
    assert h["exams"]["year_range"] == [2021, 2024]
    assert h["exams"]["missing_years"] == [2023]
    assert h["exams"]["by_year"] == {"2021": 1, "2022": 1, "2024": 1, "unknown": 1}
    assert h["exams"]["by_assessment_cycle"] == {"CT1": 2, "CT2": 1, "FINAL": 1}

    # Questions breakdown
    assert h["questions"]["total_extracted"] == 7
    assert h["questions"]["classified_with_topic"] == 6  # q1, q2, q3, q4, q5, q7 have topics
    assert h["questions"]["unresolved_questions"] == 1   # q6 has no topics
    assert h["questions"]["unresolved_question_sample_ids"] == [6]
    assert h["questions"]["needs_review_count"] == 1      # q6 has needs_review=True
    assert h["questions"]["unknown_year_questions"] == 1  # q7 is in e4 (null year)
    assert h["questions"]["classified_with_family"] == 3  # q1, q3, q4 have family_id

    # Question Families breakdown
    assert h["question_families"]["total_families"] == 2
    assert h["question_families"]["recurring_families"] == 1  # Matrix Inversion (exact_repeat)
    assert h["question_families"]["singleton_families"] == 1  # Chain Rule (singleton)
    assert h["question_families"]["repetition_type_breakdown"] == {"exact_repeat": 1, "singleton": 1}
    assert h["question_families"]["questions_in_families"] == 3
    assert h["question_families"]["unassigned_questions"] == 4

    # Topics breakdown
    # 4 syllabus topics: Matrices, Eigenvalues, Limits, Derivatives
    assert h["topics"]["syllabus_topics_total"] == 4
    assert h["topics"]["observed_topics"] == 3           # Matrices, Limits, Derivatives observed
    assert h["topics"]["unobserved_topics"] == 1         # Eigenvalues unobserved
    assert h["topics"]["unobserved_topic_names"] == ["Eigenvalues"]
    assert h["topics"]["topic_coverage_ratio"] == 0.75

    # Extraction failures
    assert h["ingestion_and_extraction"]["documents_total"] == 2
    assert h["ingestion_and_extraction"]["documents_failed"] == 1
    assert h["ingestion_and_extraction"]["failed_documents"][0]["document_id"] == 2


def test_health_unknown_year_handling(health_test_db):
    """Verify unknown-year exams are separated from temporal sequence and cannot corrupt missing years."""
    db = health_test_db
    math_course = db.query(Course).filter(Course.id == 1).first()
    h = CorpusHealthService.get_course_health(db, math_course)

    # Unknown year exam is explicitly identified
    assert h["exams"]["unknown_year_exams"] == 1
    assert h["exams"]["unknown_year_exam_ids"] == [4]
    assert h["trust_assessment"]["has_unknown_years"] is True

    # Unknown year exam does NOT appear in years_observed
    assert None not in h["exams"]["years_observed"]
    assert 0 not in h["exams"]["years_observed"]

    # Gap detection applies only between minimum and maximum valid years (2021 - 2024)
    assert h["exams"]["missing_years"] == [2023]


def test_health_track_isolation(health_test_db):
    """Verify multi-track course properly isolates stats when track is specified."""
    db = health_test_db
    lang_course = db.query(Course).filter(Course.id == 3).first()
    track_ger = db.query(CourseTrack).filter(CourseTrack.track_key == "german").first()
    track_fre = db.query(CourseTrack).filter(CourseTrack.track_key == "french").first()

    # 1. Unfiltered call on multi-track course
    overall = CorpusHealthService.get_course_health(db, lang_course)
    assert overall["tracks"]["has_tracks"] is True
    assert len(overall["tracks"]["available_tracks"]) == 2
    assert overall["exams"]["total_exams"] == 3
    assert overall["questions"]["total_extracted"] == 3

    # 2. German track isolated call
    ger_health = CorpusHealthService.get_course_health(db, lang_course, active_track=track_ger)
    assert ger_health["scope"]["track"]["track_key"] == "german"
    assert ger_health["exams"]["total_exams"] == 2
    assert ger_health["exams"]["years_observed"] == [2021, 2022]
    assert ger_health["questions"]["total_extracted"] == 2
    assert ger_health["topics"]["syllabus_topics_total"] == 1
    assert ger_health["topics"]["observed_topics"] == 1
    assert ger_health["topics"]["unobserved_topics"] == 0

    # 3. French track isolated call
    fre_health = CorpusHealthService.get_course_health(db, lang_course, active_track=track_fre)
    assert fre_health["scope"]["track"]["track_key"] == "french"
    assert fre_health["exams"]["total_exams"] == 1
    assert fre_health["exams"]["years_observed"] == [2023]
    assert fre_health["questions"]["total_extracted"] == 1
    assert fre_health["topics"]["syllabus_topics_total"] == 1
    assert fre_health["topics"]["observed_topics"] == 1

    # Cross-track zero bleeding
    assert ger_health["exams"]["years_observed"] != fre_health["exams"]["years_observed"]


def test_health_deterministic_output(health_test_db):
    """Verify repeated calls on identical database state produce deterministic, identical output."""
    db = health_test_db
    math_course = db.query(Course).filter(Course.id == 1).first()

    report1 = CorpusHealthService.get_course_health(db, math_course)
    report2 = CorpusHealthService.get_course_health(db, math_course)

    assert report1 == report2
    assert report1["exams"] == report2["exams"]
    assert report1["questions"] == report2["questions"]
    assert report1["trust_assessment"] == report2["trust_assessment"]


def test_health_api_endpoints(health_test_db):
    """Verify FastAPI routes /api/analytics/corpus-health and /api/analytics/{course_id}/corpus-health."""
    db = health_test_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Global corpus health
    resp_global = client.get("/api/analytics/corpus-health")
    assert resp_global.status_code == 200, resp_global.text
    data_global = resp_global.json()
    assert "totals" in data_global
    assert data_global["totals"]["total_courses"] == 3
    assert data_global["totals"]["total_exams"] == 8
    assert data_global["totals"]["total_questions_extracted"] == 11
    assert len(data_global["courses"]) == 3

    # 2. Course-specific corpus health
    resp_course = client.get("/api/analytics/1/corpus-health")
    assert resp_course.status_code == 200, resp_course.text
    data_course = resp_course.json()
    assert data_course["scope"]["course_id"] == 1
    assert data_course["exams"]["total_exams"] == 4
    assert data_course["trust_assessment"]["has_unknown_years"] is True
    assert data_course["trust_assessment"]["has_missing_years"] is True

    # 3. Course health alias
    resp_alias = client.get("/api/analytics/1/health")
    assert resp_alias.status_code == 200, resp_alias.text
    assert resp_alias.json() == data_course

    # 4. Multi-track course with language query
    resp_lang = client.get("/api/analytics/3/corpus-health?language=german")
    assert resp_lang.status_code == 200, resp_lang.text
    data_lang = resp_lang.json()
    assert data_lang["scope"]["track"]["track_key"] == "german"
    assert data_lang["exams"]["total_exams"] == 2

    # 5. Invalid course 404
    resp_404 = client.get("/api/analytics/99999/corpus-health")
    assert resp_404.status_code == 404

    app.dependency_overrides.clear()
