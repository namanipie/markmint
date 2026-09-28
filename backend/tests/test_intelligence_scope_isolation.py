"""
Regression test suite for Phase 4 Slice 1: Intelligence Correctness - Scope & Historical Isolation.

Verifies:
A. Course 8 study intelligence track isolation (German/French/Korean)
B. Trackless study intelligence regression (untracked courses remain unchanged)
C. QuestionFamily fallback scoping (cross-course, cross-track, valid preservation, ambiguity)
D. Historical resource counts (cutoff_year filtering, null-year exclusion, track exclusion)
E. Zero-history deterministic study priority behavior
"""
import pytest
from sqlalchemy.orm import Session

from backend.models.core import (
    Course,
    CourseTrack,
    Syllabus,
    Unit,
    Topic,
    Concept,
    Exam,
    Section,
    Question,
    Document,
    StudyEvidence,
    MappingConfidence,
    QuestionFamily,
    QuestionFamilyMembership,
)
from backend.services.prediction.engine import PredictionResult
from backend.services.study_intelligence import StudyIntelligenceService, StudyPriority
from backend.services.intelligence_cache import IntelligenceCacheService
from backend.api.endpoints.intelligence import get_intelligence_snapshot


@pytest.fixture(autouse=True)
def clean_cache():
    IntelligenceCacheService.clear_memory_cache()
    yield
    IntelligenceCacheService.clear_memory_cache()


# ==============================================================================
# A. COURSE 8 MULTI-TRACK STUDY INTELLIGENCE ISOLATION
# ==============================================================================

def test_course_8_study_intelligence_track_isolation(db_session: Session):
    """
    Course 8 German, French, and Korean must not cross-contaminate topics,
    concepts, study evidence, or question counts.
    """
    course = Course(name="Foreign Languages", code="21LEH-ELECTIVE")
    db_session.add(course)
    db_session.commit()

    german = CourseTrack(course_id=course.id, track_key="german", track_name="German", track_code="GER")
    french = CourseTrack(course_id=course.id, track_key="french", track_name="French", track_code="FRE")
    korean = CourseTrack(course_id=course.id, track_key="korean", track_name="Korean", track_code="KOR")
    db_session.add_all([german, french, korean])
    db_session.commit()

    # Syllabuses for each track
    syl_ger = Syllabus(course_id=course.id, track_id=german.id, version="v1")
    syl_fre = Syllabus(course_id=course.id, track_id=french.id, version="v1")
    syl_kor = Syllabus(course_id=course.id, track_id=korean.id, version="v1")
    db_session.add_all([syl_ger, syl_fre, syl_kor])
    db_session.commit()

    u_ger = Unit(syllabus_id=syl_ger.id, name="Unit 1 GER", number=1, expected_units=5)
    u_fre = Unit(syllabus_id=syl_fre.id, name="Unit 1 FRE", number=1, expected_units=5)
    u_kor = Unit(syllabus_id=syl_kor.id, name="Unit 1 KOR", number=1, expected_units=5)
    db_session.add_all([u_ger, u_fre, u_kor])
    db_session.commit()

    top_ger = Topic(unit_id=u_ger.id, name="German Grammar")
    top_fre = Topic(unit_id=u_fre.id, name="French Grammar")
    top_kor = Topic(unit_id=u_kor.id, name="Korean Grammar")
    db_session.add_all([top_ger, top_fre, top_kor])
    db_session.commit()

    # Concepts & Evidence
    c_ger = Concept(canonical_name="German Grammar", unit_id=u_ger.id)
    c_fre = Concept(canonical_name="French Grammar", unit_id=u_fre.id)
    c_kor = Concept(canonical_name="Korean Grammar", unit_id=u_kor.id)
    db_session.add_all([c_ger, c_fre, c_kor])
    db_session.commit()

    doc_ger = Document(title="German Notes", subject=course.name, document_hash="hash_ger_1")
    doc_fre = Document(title="French Notes", subject=course.name, document_hash="hash_fre_1")
    db_session.add_all([doc_ger, doc_fre])
    db_session.commit()

    ev_ger = StudyEvidence(document_id=doc_ger.id, concept_id=c_ger.id, knowledge_type="definition", content="Ger def", original_text="Ger", confidence=MappingConfidence.HIGH)
    ev_fre = StudyEvidence(document_id=doc_fre.id, concept_id=c_fre.id, knowledge_type="definition", content="Fre def", original_text="Fre", confidence=MappingConfidence.HIGH)
    db_session.add_all([ev_ger, ev_fre])
    db_session.commit()

    # Exams & Questions
    exam_ger = Exam(course_id=course.id, track_id=german.id, year=2023)
    exam_fre = Exam(course_id=course.id, track_id=french.id, year=2023)
    db_session.add_all([exam_ger, exam_fre])
    db_session.commit()

    sec_ger = Section(exam_id=exam_ger.id, name="Sec A")
    sec_fre = Section(exam_id=exam_fre.id, name="Sec A")
    db_session.add_all([sec_ger, sec_fre])
    db_session.commit()

    q_ger = Question(section_id=sec_ger.id, question_number="1", original_text="Was ist das?")
    q_ger.topics.append(top_ger)
    q_fre = Question(section_id=sec_fre.id, question_number="1", original_text="Qu'est-ce que c'est?")
    q_fre.topics.append(top_fre)
    db_session.add_all([q_ger, q_fre])
    db_session.commit()

    svc = StudyIntelligenceService(db_session)

    # 1. Preload scoped to German
    svc.preload_course_resources(course.id, track_id=german.id, cutoff_year=2024)

    # German topic resources should include German document + 1 question
    res_ger = svc.get_topic_resources("German Grammar", course.id, track_id=german.id)
    doc_titles_ger = [r["title"] for r in res_ger if r.get("id")]
    assert "German Notes" in doc_titles_ger
    assert "French Notes" not in doc_titles_ger
    q_res_ger = [r for r in res_ger if r.get("resource_type") == "previous_exam_questions"]
    assert len(q_res_ger) == 1
    assert q_res_ger[0]["question_count"] == 1

    # German track must NOT find French Grammar topic
    assert svc.get_topic_by_name("French Grammar", course.id, track_id=german.id) is None
    res_fre_under_ger = svc.get_topic_resources("French Grammar", course.id, track_id=german.id)
    assert len(res_fre_under_ger) == 0

    # 2. Preload scoped to French
    svc_french = StudyIntelligenceService(db_session)
    svc_french.preload_course_resources(course.id, track_id=french.id, cutoff_year=2024)
    res_fre = svc_french.get_topic_resources("French Grammar", course.id, track_id=french.id)
    doc_titles_fre = [r["title"] for r in res_fre if r.get("id")]
    assert "French Notes" in doc_titles_fre
    assert "German Notes" not in doc_titles_fre
    assert svc_french.get_topic_by_name("German Grammar", course.id, track_id=french.id) is None

    # 3. Preload scoped to Korean (zero evidence, zero questions)
    svc_kor = StudyIntelligenceService(db_session)
    svc_kor.preload_course_resources(course.id, track_id=korean.id, cutoff_year=2024)
    res_kor = svc_kor.get_topic_resources("Korean Grammar", course.id, track_id=korean.id)
    assert len(res_kor) == 0
    assert svc_kor.get_topic_by_name("German Grammar", course.id, track_id=korean.id) is None


# ==============================================================================
# B. TRACKLESS STUDY INTELLIGENCE REGRESSION
# ==============================================================================

def test_trackless_study_intelligence_regression(db_session: Session):
    """
    Standard trackless courses must continue working identically without requiring a track_id.
    """
    course = Course(name="Calculus", code="CALC101")
    db_session.add(course)
    db_session.commit()

    syl = Syllabus(course_id=course.id, version="v1")
    db_session.add(syl)
    db_session.commit()

    u = Unit(syllabus_id=syl.id, name="Unit 1", number=1, expected_units=5)
    db_session.add(u)
    db_session.commit()

    top = Topic(unit_id=u.id, name="Limits and Continuity")
    db_session.add(top)
    db_session.commit()

    c = Concept(canonical_name="Limits and Continuity", unit_id=u.id)
    db_session.add(c)
    db_session.commit()

    doc = Document(title="Limits Notes", subject=course.name, document_hash="hash_calc_1")
    db_session.add(doc)
    db_session.commit()

    ev = StudyEvidence(document_id=doc.id, concept_id=c.id, knowledge_type="definition", content="Def", original_text="Def", confidence=MappingConfidence.HIGH)
    db_session.add(ev)
    db_session.commit()

    exam = Exam(course_id=course.id, year=2023)
    db_session.add(exam)
    db_session.commit()

    sec = Section(exam_id=exam.id, name="Sec A")
    db_session.add(sec)
    db_session.commit()

    q = Question(section_id=sec.id, question_number="1", original_text="Evaluate limit as x approaches 0.")
    q.topics.append(top)
    db_session.add(q)
    db_session.commit()

    svc = StudyIntelligenceService(db_session)
    svc.preload_course_resources(course.id)

    res = svc.get_topic_resources("Limits and Continuity", course.id)
    assert len(res) == 2
    titles = [r["title"] for r in res]
    assert "Limits Notes" in titles
    assert f"Previous exam questions for {top.name}" in titles

    pred = PredictionResult(
        target="topic",
        name="Limits and Continuity",
        rank=1,
        score=0.85,
        confidence="HIGH",
        evidence={"occurrences": 2, "freq": 0.4, "recent_freq": 0.3},
    )
    p_res = svc.calculate_study_priority(pred, course.id)
    assert p_res.priority == StudyPriority.VERY_HIGH
    assert "Study material or related past questions are available." in p_res.reasons


# ==============================================================================
# C. QUESTIONFAMILY FALLBACK SCOPING
# ==============================================================================

def test_question_family_fallback_cross_course_collision(db_session: Session):
    """
    When two different courses have families with the same canonical_name,
    intelligence fallback resolution for Course A must not pick the family from Course B.
    """
    course_a = Course(name="Course A", code="CA101")
    course_b = Course(name="Course B", code="CB101")
    db_session.add_all([course_a, course_b])
    db_session.commit()

    # Course B has a QuestionFamily with canonical_name "Shared Canonical Name"
    fam_b = QuestionFamily(
        canonical_name="Shared Canonical Name",
        subject=course_b.name,
        track_id=None,
        first_seen_year=2022,
        latest_seen_year=2023,
    )
    db_session.add(fam_b)

    # Course A has an exam with questions
    exam_a = Exam(course_id=course_a.id, year=2023)
    db_session.add(exam_a)
    db_session.commit()

    sec_a = Section(exam_id=exam_a.id, name="Section A")
    db_session.add(sec_a)
    db_session.commit()

    q_a = Question(section_id=sec_a.id, question_number="1", original_text="Question in Course A without family link")
    db_session.add(q_a)
    db_session.commit()

    # Query intelligence snapshot for Course A
    snapshot_a = get_intelligence_snapshot(course_id=str(course_a.id), db=db_session)
    fam_preds = snapshot_a.get("family_predictions", [])

    # None of the family predictions in Course A should adopt Course B's family ID
    for fp in fam_preds:
        if fp.get("name") == "Shared Canonical Name":
            assert fp.get("family_id") != fam_b.id


def test_question_family_fallback_cross_track_collision(db_session: Session):
    """
    When two tracks in Course 8 have families with the same canonical_name,
    intelligence fallback resolution for German must not pick the French family ID.
    """
    course = Course(name="Foreign Languages", code="21LEH-ELECTIVE")
    db_session.add(course)
    db_session.commit()

    german = CourseTrack(course_id=course.id, track_key="german", track_name="German", track_code="GER")
    french = CourseTrack(course_id=course.id, track_key="french", track_name="French", track_code="FRE")
    db_session.add_all([german, french])
    db_session.commit()

    # French has a family
    fam_fre = QuestionFamily(
        canonical_name="Translate Sentence",
        subject=course.name,
        track_id=french.id,
        first_seen_year=2022,
        latest_seen_year=2023,
    )
    # German has its own family
    fam_ger = QuestionFamily(
        canonical_name="Translate Sentence",
        subject=course.name,
        track_id=german.id,
        first_seen_year=2021,
        latest_seen_year=2023,
    )
    db_session.add_all([fam_fre, fam_ger])
    db_session.commit()

    # German exam & question
    exam_ger = Exam(course_id=course.id, track_id=german.id, year=2023)
    db_session.add(exam_ger)
    db_session.commit()

    sec_ger = Section(exam_id=exam_ger.id, name="Sec A")
    db_session.add(sec_ger)
    db_session.commit()

    q_ger = Question(section_id=sec_ger.id, question_number="1", original_text="Translate Sentence to German", family=fam_ger)
    db_session.add(q_ger)
    db_session.commit()

    mem_ger = QuestionFamilyMembership(
        question_id=q_ger.id, family_id=fam_ger.id, match_type="exact", similarity_score=1.0, decision_method="manual", algorithm_version="v1"
    )
    db_session.add(mem_ger)
    db_session.commit()

    snapshot_ger = get_intelligence_snapshot(course_id=str(course.id), language="german", db=db_session)
    fam_preds_ger = snapshot_ger.get("family_predictions", [])
    assert len(fam_preds_ger) > 0
    for fp in fam_preds_ger:
        if fp.get("name") == "Translate Sentence":
            assert fp.get("family_id") == fam_ger.id
            assert fp.get("family_id") != fam_fre.id


def test_question_family_valid_id_authoritative(db_session: Session):
    """
    If a prediction already possesses a valid family_id, fallback lookup is skipped,
    and the valid family_id remains authoritative.
    """
    course = Course(name="Chemistry", code="CHEM101")
    db_session.add(course)
    db_session.commit()

    fam = QuestionFamily(canonical_name="Periodic Trends", subject=course.name, track_id=None)
    db_session.add(fam)
    db_session.commit()

    exam = Exam(course_id=course.id, year=2023)
    db_session.add(exam)
    db_session.commit()

    sec = Section(exam_id=exam.id, name="Sec A")
    db_session.add(sec)
    db_session.commit()

    q = Question(section_id=sec.id, question_number="1", original_text="Explain periodic trends in electronegativity.", family=fam)
    db_session.add(q)
    db_session.commit()

    mem = QuestionFamilyMembership(
        question_id=q.id, family_id=fam.id, match_type="exact", similarity_score=1.0, decision_method="manual", algorithm_version="v1"
    )
    db_session.add(mem)
    db_session.commit()

    snapshot = get_intelligence_snapshot(course_id=str(course.id), db=db_session)
    fam_preds = snapshot.get("family_predictions", [])
    assert len(fam_preds) > 0
    assert fam_preds[0]["family_id"] == fam.id


# ==============================================================================
# D. HISTORICAL RESOURCE COUNTS
# ==============================================================================

def test_historical_resource_counts_temporal_and_track_scoping(db_session: Session):
    """
    Verify question_count in get_topic_resources:
    - Excludes future exams (year >= cutoff_year)
    - Excludes exams where year IS NULL
    - Excludes exams belonging to another track
    """
    course = Course(name="Mathematics", code="MATH101")
    db_session.add(course)
    db_session.commit()

    track_a = CourseTrack(course_id=course.id, track_key="track_a", track_name="Track A")
    track_b = CourseTrack(course_id=course.id, track_key="track_b", track_name="Track B")
    db_session.add_all([track_a, track_b])
    db_session.commit()

    syl = Syllabus(course_id=course.id, track_id=track_a.id, version="v1")
    db_session.add(syl)
    db_session.commit()

    u = Unit(syllabus_id=syl.id, name="Unit 1", number=1, expected_units=5)
    db_session.add(u)
    db_session.commit()

    topic = Topic(unit_id=u.id, name="Derivatives")
    db_session.add(topic)
    db_session.commit()

    # 1. Valid historical exam in track_a (year 2022)
    exam_2022 = Exam(course_id=course.id, track_id=track_a.id, year=2022)
    # 2. Valid historical exam in track_a (year 2023)
    exam_2023 = Exam(course_id=course.id, track_id=track_a.id, year=2023)
    # 3. Future exam in track_a (year 2024, equal to cutoff 2024)
    exam_2024 = Exam(course_id=course.id, track_id=track_a.id, year=2024)
    # 4. Unknown-year exam in track_a (year IS NULL)
    exam_null = Exam(course_id=course.id, track_id=track_a.id, year=None)
    # 5. Exam in track_b (year 2023)
    exam_track_b = Exam(course_id=course.id, track_id=track_b.id, year=2023)

    db_session.add_all([exam_2022, exam_2023, exam_2024, exam_null, exam_track_b])
    db_session.commit()

    # Add questions for each exam mapped to topic "Derivatives"
    for ex in [exam_2022, exam_2023, exam_2024, exam_null, exam_track_b]:
        sec = Section(exam_id=ex.id, name=f"Section {ex.id}")
        db_session.add(sec)
        db_session.commit()
        q = Question(section_id=sec.id, question_number="1", original_text=f"Find derivative in exam {ex.id}")
        q.topics.append(topic)
        db_session.add(q)

    db_session.commit()

    svc = StudyIntelligenceService(db_session)

    # Preloaded query with track_a and cutoff 2024
    svc.preload_course_resources(course.id, track_id=track_a.id, cutoff_year=2024)
    res_preloaded = svc.get_topic_resources("Derivatives", course.id, track_id=track_a.id, cutoff_year=2024)
    q_res_pre = [r for r in res_preloaded if r.get("resource_type") == "previous_exam_questions"]
    assert len(q_res_pre) == 1
    # Only 2022 and 2023 must be counted (2 questions).
    # 2024 (>= cutoff), None (null year), and track_b must be excluded!
    assert q_res_pre[0]["question_count"] == 2

    # Direct non-preloaded query
    svc_direct = StudyIntelligenceService(db_session)
    res_direct = svc_direct.get_topic_resources("Derivatives", course.id, track_id=track_a.id, cutoff_year=2024)
    q_res_dir = [r for r in res_direct if r.get("resource_type") == "previous_exam_questions"]
    assert len(q_res_dir) == 1
    assert q_res_dir[0]["question_count"] == 2


# ==============================================================================
# E. ZERO-HISTORY BEHAVIOR
# ==============================================================================

def test_zero_history_study_priority_deterministic(db_session: Session):
    """
    calculate_study_priority must execute without exceptions, produce deterministic
    priorities, and never fabricate evidence when historical corpus data is zero.
    """
    course = Course(name="New Course", code="NEW101")
    db_session.add(course)
    db_session.commit()

    pred = PredictionResult(
        target="topic",
        name="Completely Unobserved Topic",
        rank=1,
        score=0.2,
        confidence="LOW",
        evidence={},
    )

    svc = StudyIntelligenceService(db_session)
    res = svc.calculate_study_priority(pred, course.id)

    assert res.topic == "Completely Unobserved Topic"
    assert res.priority == StudyPriority.LOW
    assert res.resources == []
    assert "No trusted topic-mapped study material is available." in res.reasons
    assert res.student_status is None
    assert res.practice_accuracy is None
    assert res.recommended_action == "FOUNDATIONAL_EXPLORATION"
