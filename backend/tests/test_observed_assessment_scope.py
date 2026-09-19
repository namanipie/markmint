"""
Comprehensive Test Suite for Paper-Derived Assessment Scope Architecture.

Verifies:
1. Canonical syllabus taxonomy retrieval (Syllabus defines what exists)
2. Variable unit counts (N is not globally 5; e.g. Calculus=9, Chemistry=12, SPCM=5)
3. Paper assessment identification with provenance (metadata -> doc metadata -> title -> filename -> fallback)
4. Question -> Topic -> Unit mapping lineage (no inferring Q5 = Unit 5)
5. Paper-level observed coverage
6. Cycle-level observed aggregation
7. Separation of intended_scope and observed_scope
8. Evidence status (EVIDENCE_BACKED, INTENDED_ONLY_NO_PAPERS, OUT_OF_SCOPE_OBSERVED, UNPLANNED_OBSERVED_ONLY, ALL_SCOPE)
9. UNOBSERVED_IN_SCOPE handling (strictly 0 synthetic probability)
10. OUT_OF_SCOPE_OBSERVED handling (preserved as empirical anomaly)
11. Coverage provenance audit chain
12. No hardcoded global CT1/CT2 unit assumptions
13. Raw assessment provenance preservation
"""

import pytest
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Exam, Section, Question
from backend.services.assessment_plan_registry import (
    COURSE_ASSESSMENT_PLANS,
    get_course_assessment_plan,
    get_course_assessment_scope,
)
from backend.services.observed_assessment_coverage import (
    identify_exam_assessment,
    compute_paper_observed_coverage,
    compute_cycle_observed_coverage,
    build_coverage_audit_chain,
)
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.endpoints.predictions import get_prediction
from backend.api.endpoints.practice import get_practice_questions
from backend.api.router_study import get_study_priorities


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_canonical_syllabus_variable_unit_counts(db: Session):
    """Verify that canonical units are defined by Syllabus authority and N is variable."""
    # Calculus (21MAB101T) has 9 canonical units
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    assert calc is not None
    calc_units = (
        db.query(Unit)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == calc.id)
        .order_by(Unit.number)
        .all()
    )
    calc_unit_nums = [u.number for u in calc_units]
    assert calc_unit_nums == [1, 2, 3, 4, 5, 6, 7, 8, 9], f"Calculus must have units 1..9, got {calc_unit_nums}"
    assert len(calc_units) == 9

    # Chemistry (21CYB101J) has 12 canonical units
    chem = db.query(Course).filter(Course.canonical_code == "21CYB101J").first()
    assert chem is not None
    chem_units = (
        db.query(Unit)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == chem.id)
        .order_by(Unit.number)
        .all()
    )
    chem_unit_nums = [u.number for u in chem_units]
    assert chem_unit_nums == list(range(1, 13)), f"Chemistry must have units 1..12, got {chem_unit_nums}"
    assert len(chem_units) == 12

    # SPCM (21PYB102J) has 5 canonical units
    spcm = db.query(Course).filter(Course.canonical_code == "21PYB102J").first()
    assert spcm is not None
    spcm_units = (
        db.query(Unit)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == spcm.id)
        .order_by(Unit.number)
        .all()
    )
    spcm_unit_nums = [u.number for u in spcm_units]
    assert spcm_unit_nums == [1, 2, 3, 4, 5], f"SPCM must have units 1..5, got {spcm_unit_nums}"


def test_unique_unit_numbers_and_all_topics_mapped_to_units(db: Session):
    """Verify that every Unit.number in every course is unique and every topic has a valid Unit."""
    for course in db.query(Course).all():
        syl = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
        if not syl:
            continue
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).all()
        nums = [u.number for u in units]
        assert len(nums) == len(set(nums)), f"Course {course.code} has duplicate unit numbers: {nums}"

    # All topics map to exactly one Unit
    topics = db.query(Topic).all()
    for t in topics:
        assert t.unit_id is not None, f"Topic {t.name} has null unit_id"
        u = db.query(Unit).filter(Unit.id == t.unit_id).first()
        assert u is not None, f"Topic {t.name} points to non-existent unit {t.unit_id}"


def test_paper_assessment_identification_provenance(db: Session):
    """Verify that paper identification resolves assessment identity with source provenance."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    calc_exams = db.query(Exam).filter(Exam.course_id == calc.id).all()
    assert len(calc_exams) >= 3

    for ex in calc_exams:
        ident = identify_exam_assessment(ex, calc.id)
        assert ident.normalized_code is not None
        assert ident.identification_source in ("metadata", "document_metadata", "document_title", "filename", "fallback")
        assert 0.0 <= ident.confidence <= 1.0
        assert ident.evidence_text is not None


def test_paper_observed_coverage_question_lineage(db: Session):
    """Verify paper-level observed coverage derives units strictly through question -> topic -> unit."""
    chem = db.query(Course).filter(Course.canonical_code == "21CYB101J").first()
    exam = db.query(Exam).filter(Exam.course_id == chem.id, Exam.year == 2018).first()
    assert exam is not None

    paper_cov = compute_paper_observed_coverage(exam)
    assert paper_cov.total_questions > 0
    assert paper_cov.mapped_questions_count > 0
    assert len(paper_cov.observed_unit_numbers) > 0

    # Ensure observed units match only those present in question lineage
    lineage_units = set()
    for q_lineage in paper_cov.question_lineage:
        if q_lineage.is_mapped:
            assert len(q_lineage.topic_ids) > 0
            assert len(q_lineage.unit_numbers) > 0
            lineage_units.update(q_lineage.unit_numbers)

    assert set(paper_cov.observed_unit_numbers) == lineage_units


def test_cycle_level_observed_aggregation(db: Session):
    """Verify cycle-level aggregation summarizes papers without discarding paper-level breakdowns."""
    spcm = db.query(Course).filter(Course.canonical_code == "21PYB102J").first()
    endsem_exams = [
        ex for ex in db.query(Exam).filter(Exam.course_id == spcm.id).all()
        if identify_exam_assessment(ex, spcm.id).student_cycle == "ENDSEM"
    ]
    assert len(endsem_exams) >= 5

    cycle_cov = compute_cycle_observed_coverage(spcm.id, "ENDSEM", endsem_exams)
    assert cycle_cov.paper_count == len(endsem_exams)
    assert len(cycle_cov.papers) == len(endsem_exams)
    assert len(cycle_cov.observed_unit_numbers) == 5
    assert set(cycle_cov.observed_unit_numbers) == {1, 2, 3, 4, 5}
    assert sum(cycle_cov.question_count_by_unit.values()) == cycle_cov.mapped_questions_count


def test_intended_vs_observed_scope_separation(db: Session):
    """Verify AssessmentScope clearly decouples intended_scope from observed_scope."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    scope = get_course_assessment_scope(calc.id, "CT1", db=db)

    # Intended scope comes from authoritative plan (Units 1, 2)
    assert scope.intended_scope is not None
    assert scope.intended_scope["unit_numbers"] == [1, 2]
    assert len(scope.intended_scope["topic_names"]) > 0

    # Observed scope comes from historical exam papers (Unit 1 observed)
    assert scope.observed_scope is not None
    assert scope.observed_scope["unit_numbers"] == [1]
    assert scope.observed_scope["paper_count"] >= 1
    assert 1 in scope.observed_scope["question_count_by_unit"]

    # Evidence status
    assert scope.evidence_status == "EVIDENCE_BACKED"


def test_out_of_scope_observed_detection(db: Session):
    """Verify that empirical questions tested outside intended syllabus plan are flagged as OUT_OF_SCOPE_OBSERVED."""
    chem = db.query(Course).filter(Course.canonical_code == "21CYB101J").first()
    scope = get_course_assessment_scope(chem.id, "CT1", db=db)

    # Intended is [1, 2]
    assert scope.intended_scope["unit_numbers"] == [1, 2]
    # Observed includes units outside [1, 2] (e.g. Unit 8 or 11 from past test papers)
    assert any(u not in [1, 2] for u in scope.observed_scope["unit_numbers"])
    assert scope.evidence_status == "OUT_OF_SCOPE_OBSERVED"


def test_unobserved_in_scope_zero_synthetic_probability(db: Session):
    """Verify that in-scope topics with no historical appearances get zero synthetic probability."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    snapshot = get_intelligence_snapshot(str(calc.id), assessment_cycle="CT1", db=db)

    scope_payload = snapshot["assessment_scope"]
    assert scope_payload["intended_scope"]["unit_numbers"] == [1, 2]

    # Unobserved topics exist because Unit 2 had 0 CT1 historical questions
    unobserved = scope_payload["unobserved_in_scope_topics"]
    assert len(unobserved) > 0
    for item in unobserved:
        assert item["status"] == "UNOBSERVED_IN_SCOPE"
        assert "no historical evidence" in item["message"].lower()

    # Predictions must not contain synthetic probabilities for unobserved topics
    pred_names = {p.get("name") or p.get("topic") for p in snapshot["predictions"]}
    unobserved_names = {item["name"] for item in unobserved}
    assert pred_names.isdisjoint(unobserved_names), "Unobserved topics must NOT receive synthetic predictions!"


def test_coverage_audit_chain(db: Session):
    """Verify build_coverage_audit_chain returns full auditable lineage."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    calc_exam = db.query(Exam).filter(Exam.course_id == calc.id).first()
    assert calc_exam is not None

    chain = build_coverage_audit_chain(calc.id, calc_exam.id, db)
    assert chain["course_id"] == calc.id
    assert chain["exam_id"] == calc_exam.id
    assert "assessment_identity" in chain
    assert "observed_units" in chain
    assert len(chain["question_lineage"]) > 0

    first_q = chain["question_lineage"][0]
    assert "question_id" in first_q
    assert "mapped_topics" in first_q
    assert "canonical_units" in first_q
    if first_q["is_mapped"]:
        assert len(first_q["mapped_topics"]) > 0
        assert len(first_q["canonical_units"]) > 0


def test_end_to_end_api_endpoints_scope_exposure(db: Session):
    """Verify snapshot, predictions, practice, and study expose decoupled scope and evidence status."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()

    # 1. Snapshot
    snap = get_intelligence_snapshot(str(calc.id), assessment_cycle="CT1", db=db)
    assert "intended_scope" in snap
    assert "observed_scope" in snap
    assert "evidence_status" in snap
    assert snap["evidence_status"] == "EVIDENCE_BACKED"

    # 2. Predictions
    pred = get_prediction(str(calc.id), assessment_cycle="CT1", db=db)
    assert "intended_scope" in pred
    assert "observed_scope" in pred
    assert "evidence_status" in pred

    # 3. Practice
    prac = get_practice_questions(calc.name, assessment_cycle="CT1")
    assert "intended_scope" in prac
    assert "observed_scope" in prac
    assert "evidence_status" in prac

    # 4. Study Priorities
    study = get_study_priorities(calc.name, assessment_cycle="CT1", db=db)
    assert "intended_scope" in study
    assert "observed_scope" in study
    assert "evidence_status" in study


def test_question_count_reconciliation_total_equals_mapped_plus_unmapped(db: Session):
    """Invariant: total_questions == mapped_questions_count + unmapped_questions_count for all papers and cycles."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    assert calc is not None

    exams = db.query(Exam).filter(Exam.course_id == calc.id).all()
    for ex in exams:
        pcov = compute_paper_observed_coverage(ex)
        assert pcov.total_questions == pcov.mapped_questions_count + pcov.unmapped_questions_count, (
            f"Exam {ex.id} count discrepancy: total={pcov.total_questions} != mapped({pcov.mapped_questions_count}) + unmapped({pcov.unmapped_questions_count})"
        )

    # Calculus CT2 cycle reconciliation (Post-mapping: 17 mapped, 5 unmapped, total=22)
    calc_ct2_exams = [
        ex for ex in exams
        if identify_exam_assessment(ex, calc.id).student_cycle == "CT2"
    ]
    assert len(calc_ct2_exams) == 3
    ccov = compute_cycle_observed_coverage(calc.id, "CT2", calc_ct2_exams)
    assert ccov.total_questions == 22
    assert ccov.mapped_questions_count == 17
    assert ccov.unmapped_questions_count == 5
    assert ccov.total_questions == ccov.mapped_questions_count + ccov.unmapped_questions_count
    assert ccov.mapping_rate == round(17 / 22 * 100, 2)


def test_marks_accounting_distinguishes_known_vs_unknown_marks(db: Session):
    """Invariant: total_questions == questions_with_known_marks + questions_with_unknown_marks; never fabricate marks."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    calc_ct2_exams = [
        ex for ex in db.query(Exam).filter(Exam.course_id == calc.id).all()
        if identify_exam_assessment(ex, calc.id).student_cycle == "CT2"
    ]
    ccov = compute_cycle_observed_coverage(calc.id, "CT2", calc_ct2_exams)

    # Every question has either known marks or unknown marks
    assert ccov.total_questions == ccov.questions_with_known_marks + ccov.questions_with_unknown_marks
    assert ccov.questions_with_known_marks == 14
    assert ccov.questions_with_unknown_marks == 8

    # Paper 3 (2015) has all 8 questions with unknown marks (marks=None in DB)
    p3 = [p for p in ccov.papers if p["exam_id"] == 3][0]
    assert p3["total_questions"] == 8
    assert p3["questions_with_unknown_marks"] == 8
    assert p3["questions_with_known_marks"] == 0
    assert p3["known_marks_total"] == 0.0

    # Papers 17 and 18 have known marks (71.0 each)
    p17 = [p for p in ccov.papers if p["exam_id"] == 17][0]
    p18 = [p for p in ccov.papers if p["exam_id"] == 18][0]
    assert p17["known_marks_total"] == 71.0
    assert p18["known_marks_total"] == 71.0

    # Cycle marks_by_unit reflects mapped questions with known marks
    assert ccov.known_marks_total == 142.0
    assert ccov.marks_by_unit.get(1) == 84.0
    assert ccov.marks_by_unit.get(5) == 16.0
    assert ccov.marks_by_unit.get(6) == 42.0
    assert round(sum(ccov.marks_by_unit.values()), 2) == ccov.known_marks_total


def test_fallback_assessment_identity_does_not_corrupt_cycle_predictions(db: Session):
    """Invariant: Fallback papers default to ALL and are excluded from CT1 / CT2 cycle predictions."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    all_exams = db.query(Exam).filter(Exam.course_id == calc.id).all()
    for ex in all_exams:
        ident = identify_exam_assessment(ex, calc.id)
        if ident.identification_source == "fallback":
            assert ident.student_cycle == "ALL"
            assert ident.confidence <= 0.5
            assert ident.student_cycle not in ("CT1", "CT2")


def test_successfully_resolved_fallback_papers_enter_correct_cycle(db: Session):
    """Invariant: Documents with conclusive title/session evidence resolve to correct cycle with provenance."""
    # Exam 25: Calculus PYQ 2024 Dec -> ENDSEM
    ex25 = db.query(Exam).filter(Exam.id == 25).first()
    assert ex25 is not None
    ident25 = identify_exam_assessment(ex25, ex25.course_id)
    assert ident25.normalized_code == "ENDSEM"
    assert ident25.student_cycle == "ENDSEM"
    assert ident25.identification_source == "document_title"
    assert ident25.confidence == 0.9

    # Exam 252: Electronic System And PCB Design test-fj-ii -> CT2
    ex252 = db.query(Exam).filter(Exam.id == 252).first()
    assert ex252 is not None
    ident252 = identify_exam_assessment(ex252, ex252.course_id)
    assert ident252.normalized_code == "CT2"
    assert ident252.student_cycle == "CT2"
    assert ident252.identification_source == "document_title"
    assert ident252.confidence == 0.9

    # Exam 6: Chem Q-Bank.pdf -> Must remain fallback UNKNOWN / ALL
    ex6 = db.query(Exam).filter(Exam.id == 6).first()
    assert ex6 is not None
    ident6 = identify_exam_assessment(ex6, ex6.course_id)
    assert ident6.normalized_code == "UNKNOWN"
    assert ident6.student_cycle == "ALL"
    assert ident6.identification_source == "fallback"


def test_unmapped_questions_never_become_prediction_evidence(db: Session):
    """Invariant: Questions without topic mapping are excluded from prediction evidence."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    pred_resp = get_prediction(str(calc.id), assessment_cycle="CT2", db=db)
    
    # Predictions must come strictly from mapped topics
    assert "predictions" in pred_resp
    pred_topic_names = {p["name"] for p in pred_resp["predictions"]}
    
    # Exam 3 question 13 (Solve (D^2 + 6D + 9) y = 3e^{4x}) is unmapped
    q13 = db.query(Question).filter(Question.id == 13).first()
    assert q13 is not None
    assert len(q13.topics) == 0  # Still unmapped
    
    # Unmapped topics must not receive fake prediction scores
    assert "Second-Order ODE" not in pred_topic_names


def test_provenance_survives_and_raw_data_unmutated(db: Session):
    """Invariant: Dynamic assessment resolution never mutates raw Exam.assessment_type or Document fields."""
    ex25 = db.query(Exam).filter(Exam.id == 25).first()
    assert ex25.assessment_type is None  # Raw field remains unmutated!
    
    ident = identify_exam_assessment(ex25, ex25.course_id)
    assert ident.normalized_code == "ENDSEM"
    assert ident.raw_type is None
    assert ident.identification_source == "document_title"


def test_no_fake_topic_unit_mapping(db: Session):
    """Invariant: All mapped questions resolve to valid canonical units through topic.unit, never question numbering."""
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    # Question 460 is Q#5 in Exam 17 Part-B, but mapped to Quadratic Forms (Unit 1), NOT Unit 5!
    q460 = db.query(Question).filter(Question.id == 460).first()
    assert q460 is not None
    assert q460.question_number == "5"
    assert len(q460.topics) == 1
    assert q460.topics[0].name == "Quadratic Forms"
    assert q460.topics[0].unit.number == 1  # Strictly Unit 1, NOT Unit 5!


