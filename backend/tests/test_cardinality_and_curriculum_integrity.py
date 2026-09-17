"""
Regression tests for:
1. Question.topics Many-to-Many cardinality handling across payloads, DNA, and intelligence checks.
2. CurriculumMapping (branch_name, semester, curriculum_id) composite identity isolation.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from backend.core.database import SessionLocal
from backend.models.core import (
    Course, Exam, Section, Question, Topic, Unit, Syllabus, CurriculumMapping
)
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from scripts.curriculum.seed_curriculum import seed_curriculum, verify_integrity


def test_question_mapped_to_two_topics_in_payload():
    """Verify that _build_historical_exam_payloads exposes all mapped topics."""
    db = SessionLocal()
    try:
        # Create an ephemeral exam with a multi-topic question in a rollback context
        exam = db.query(Exam).filter(Exam.course_id == 1).first()
        if not exam:
            pytest.skip("No Course 1 exam found")

        # Pick two distinct topics
        topics = db.query(Topic).limit(2).all()
        if len(topics) < 2:
            pytest.skip("Fewer than 2 topics in database")

        t1, t2 = topics[0], topics[1]

        # Use an existing question or mock object
        q = exam.sections[0].questions[0]
        original_topics = list(q.topics)

        try:
            q.topics = [t1, t2]
            db.flush()

            payloads = _build_historical_exam_payloads([exam])
            exam_p = next(p for p in payloads if p["id"] == exam.id)
            q_p = next(qp for qp in exam_p["questions"] if qp["id"] == q.id)

            # Assert backward compatibility
            assert q_p["topic"] == t1.name
            # Assert all mapped topics are present
            assert "topics" in q_p
            assert len(q_p["topics"]) == 2
            assert t1.name in q_p["topics"]
            assert t2.name in q_p["topics"]

            # Assert topic_mappings structured payload
            assert "topic_mappings" in q_p
            assert len(q_p["topic_mappings"]) == 2
            mapped_names = {tm["topic"] for tm in q_p["topic_mappings"]}
            assert t1.name in mapped_names
            assert t2.name in mapped_names
        finally:
            q.topics = original_topics
            db.rollback()
    finally:
        db.close()


def test_dna_aggregation_sees_every_mapped_topic():
    """Verify that DNAAnalyzerService aggregates metrics for every topic mapped to a question."""
    exam_data = [
        {
            "id": 1001,
            "year": 2024,
            "exam_type": "Regular",
            "questions": [
                {
                    "id": 9001,
                    "marks": 10.0,
                    "is_alternative": False,
                    "topic": "Matrices",
                    "topics": ["Matrices", "Eigenvalues"],
                    "unit": "Linear Algebra",
                    "units": ["Linear Algebra"],
                    "question_type": "Analytical",
                    "repetition_type": "singleton",
                },
                {
                    "id": 9002,
                    "marks": 5.0,
                    "is_alternative": False,
                    "topic": "Matrices",
                    "topics": ["Matrices"],
                    "unit": "Linear Algebra",
                    "units": ["Linear Algebra"],
                    "question_type": "Descriptive",
                    "repetition_type": "singleton",
                }
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exam_data)
    topic_names = {t.topic for t in dna.topics}

    # Both topics must be present in DNA
    assert "Matrices" in topic_names, "Matrices topic must be present in DNA"
    assert "Eigenvalues" in topic_names, "Eigenvalues topic must be present in DNA"

    matrices_dna = next(t for t in dna.topics if t.topic == "Matrices")
    eigenvalues_dna = next(t for t in dna.topics if t.topic == "Eigenvalues")

    # Matrices was mapped to Q 9001 and Q 9002 -> 2 questions, 15 marks
    assert matrices_dna.question_count == 2
    assert matrices_dna.total_marks == 15.0

    # Eigenvalues was mapped to Q 9001 -> 1 question, 10 marks
    assert eigenvalues_dna.question_count == 1
    assert eigenvalues_dna.total_marks == 10.0

    # Total exam sample size must NOT double-count the question
    assert dna.sample_size.questions == 2


def test_timeline_considers_all_mapped_topics():
    """Verify that historical year presence checks see secondary mapped topics."""
    db = SessionLocal()
    try:
        exam = db.query(Exam).filter(Exam.course_id == 2, Exam.year.isnot(None)).first()
        if not exam:
            pytest.skip("No Course 2 exam with year found")

        topics = db.query(Topic).limit(2).all()
        if len(topics) < 2:
            pytest.skip("Fewer than 2 topics in database")

        t1, t2 = topics[0], topics[1]
        q = exam.sections[0].questions[0]
        original_topics = list(q.topics)

        try:
            # Map question to both topics
            q.topics = [t1, t2]
            db.flush()

            # Test timeline matching logic for t2 (which is the SECOND topic)
            hist_exams = [exam]
            t2_years = {
                e.year for e in hist_exams
                if e.year is not None and any(
                    any(t.name == t2.name for t in q_elem.topics)
                    for s in e.sections for q_elem in s.questions
                )
            }
            assert exam.year in t2_years, f"Year {exam.year} must be found for secondary topic {t2.name}"
        finally:
            q.topics = original_topics
            db.rollback()
    finally:
        db.close()


def test_curriculum_mappings_composite_identity_isolation():
    """Verify that curriculum mappings with the same curriculum_id across branches remain independent."""
    db = SessionLocal()
    try:
        # Check compu-1-2 across CSE branches
        mappings = db.query(CurriculumMapping).filter(CurriculumMapping.curriculum_id == "compu-1-2").all()
        assert len(mappings) > 1, "Expected compu-1-2 to exist across multiple branches"

        # Group by branch
        branch_ids = {m.branch_name: m.id for m in mappings}
        assert len(branch_ids) == len(mappings), "Each branch must have a distinct row ID"

        # Verify updating one branch via composite key does NOT modify another branch
        sample_branch = mappings[0].branch_name
        other_branch = mappings[1].branch_name
        other_course_before = mappings[1].course_id
        other_status_before = mappings[1].status

        # Test update_by_composite_key
        updated = CurriculumMapping.update_by_composite_key(
            db,
            branch_name=sample_branch,
            semester=mappings[0].semester,
            curriculum_id="compu-1-2",
            notes="TEST_ISOLATION_UPDATE"
        )
        assert updated is not None
        assert updated.branch_name == sample_branch
        assert updated.notes == "TEST_ISOLATION_UPDATE"

        # Verify other branch was NOT mutated
        other_record = CurriculumMapping.get_by_composite_key(
            db,
            branch_name=other_branch,
            semester=mappings[1].semester,
            curriculum_id="compu-1-2"
        )
        assert other_record.course_id == other_course_before
        assert other_record.status == other_status_before
        assert other_record.notes != "TEST_ISOLATION_UPDATE"
    finally:
        db.rollback()
        db.close()


def test_curriculum_unique_constraint_enforced():
    """Verify database prevents duplicate (branch_name, semester, curriculum_id) triplets."""
    db = SessionLocal()
    try:
        sample = db.query(CurriculumMapping).first()
        assert sample is not None

        # Attempt to insert a duplicate with identical (branch_name, semester, curriculum_id)
        dup = CurriculumMapping(
            branch_name=sample.branch_name,
            semester=sample.semester,
            curriculum_id=sample.curriculum_id,
            subject_name="Duplicate Subject Test",
            credits=3,
            status="UNMATCHED"
        )
        db.add(dup)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_seed_curriculum_is_idempotent_and_preserves_2810():
    """Verify running seed_curriculum is completely idempotent and maintains 2,810 mappings."""
    db = SessionLocal()
    try:
        count_before = db.query(CurriculumMapping).count()
        assert count_before == 2810, f"Expected 2810 mappings, found {count_before}"

        # Run seed_curriculum and verify_integrity
        seed_curriculum(db)
        verify_integrity(db)

        count_after = db.query(CurriculumMapping).count()
        assert count_after == 2810, "seed_curriculum must not add duplicate rows"
    finally:
        db.close()
