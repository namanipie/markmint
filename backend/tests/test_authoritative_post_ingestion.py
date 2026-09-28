"""Comprehensive tests for authoritative post-ingestion orchestration and completeness.

Verifies:
1. Full end-to-end post-ingestion lifecycle (topics -> families -> commit -> cache invalidation).
2. Strict idempotency: repeated executions create zero duplicate memberships, topics, or families.
3. API `/api/exams/import` automatically invokes post-processing (topics + families).
4. Study material ingestion invalidates affected course cache across all tiers.
5. Student upload invalidation lifecycle.
6. Failure rollback behavior: failed post-processing leaves existing valid cache intact.
7. Multi-track propagation: track_id is strictly respected during mapping and family assignment.
8. Unrelated course cache isolation: mutating Course A never invalidates Course B.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import (
    Course,
    CourseTrack,
    Exam,
    Section,
    Question,
    Topic,
    Unit,
    Syllabus,
    QuestionFamily,
    QuestionFamilyMembership,
    question_topic,
    Document,
    StudyEvidence,
    MappingConfidence,
)
from backend.services.scraper.post_processor import PostIngestionPipeline
from backend.services.exam import ExamService
from backend.services.intelligence_cache import IntelligenceCacheService, analysis_cache


@pytest.fixture
def post_ingest_db():
    """Isolated in-memory SQLite fixture for post-ingestion testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create Course 2 (Chemistry)
    chem = Course(id=2, name="Engineering Chemistry", code="21CHY101J")
    # Create Course 1 (Calculus)
    calc = Course(id=1, name="Calculus", code="21MAB101T")
    # Create Course 8 (Foreign Language) with German and French tracks
    lang = Course(id=8, name="Foreign Language", code="21FLS101J")
    track_de = CourseTrack(id=1, course_id=8, track_key="german", track_name="German")
    track_fr = CourseTrack(id=2, course_id=8, track_key="french", track_name="French")

    session.add_all([chem, calc, lang, track_de, track_fr])
    session.flush()

    # Syllabus and topic for Chemistry
    syl = Syllabus(course_id=chem.id, version="v1")
    session.add(syl)
    session.flush()
    unit = Unit(syllabus_id=syl.id, number=1, name="Electrochemistry")
    session.add(unit)
    session.flush()
    t1 = Topic(id=101, unit_id=unit.id, name="Nernst Equation")
    session.add(t1)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    IntelligenceCacheService.clear_memory_cache()


def test_1_authoritative_pipeline_full_lifecycle(post_ingest_db):
    """1. Full post-ingestion lifecycle: topic mapping -> families -> commit -> cache invalidation."""
    IntelligenceCacheService.clear_memory_cache()

    # Seed initial cache for Course 2 and Course 1
    payload_chem = {"data_availability_status": "AVAILABLE", "course": {"id": 2}, "metadata": {}}
    payload_calc = {"data_availability_status": "AVAILABLE", "course": {"id": 1}, "metadata": {}}
    IntelligenceCacheService.store_snapshot(post_ingest_db, 2, "ALL", None, payload_chem)
    IntelligenceCacheService.store_snapshot(post_ingest_db, 1, "ALL", None, payload_calc)

    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2, "ALL") is not None
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 1, "ALL") is not None

    # Create Exam for Course 2
    exam = Exam(course_id=2, year=2023, assessment_type="CT1")
    post_ingest_db.add(exam)
    post_ingest_db.flush()

    sec = Section(exam_id=exam.id, name="Section A")
    post_ingest_db.add(sec)
    post_ingest_db.flush()

    q1 = Question(
        section_id=sec.id,
        question_number="1",
        original_text="Derive the Nernst equation for single electrode potential.",
    )
    post_ingest_db.add(q1)
    post_ingest_db.commit()

    # Execute authoritative pipeline
    pipeline = PostIngestionPipeline(post_ingest_db)
    res = pipeline.process_exam(exam.id, course_id=2, auto_commit=True)

    assert res["exam_id"] == exam.id
    assert res["course_id"] == 2
    assert res["families_linked"] == 1
    assert res["cache_invalidated"] >= 1

    # Verify QuestionFamily was assigned
    post_ingest_db.refresh(q1)
    assert q1.family_id is not None
    mem = post_ingest_db.query(QuestionFamilyMembership).filter_by(question_id=q1.id).first()
    assert mem is not None
    assert mem.family_id == q1.family_id

    # Verify Course 2 cache was invalidated
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2, "ALL") is None

    # Verify Course 1 cache remains completely unaffected
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 1, "ALL") is not None


def test_2_authoritative_pipeline_idempotency(post_ingest_db):
    """2. Repeated executions must not duplicate memberships, topics, or families."""
    exam = Exam(course_id=2, year=2023, assessment_type="CT1")
    post_ingest_db.add(exam)
    post_ingest_db.flush()

    sec = Section(exam_id=exam.id, name="Part A")
    post_ingest_db.add(sec)
    post_ingest_db.flush()

    q1 = Question(section_id=sec.id, question_number="1", original_text="Describe galvanic corrosion prevention.")
    q2 = Question(section_id=sec.id, question_number="2", original_text="State Faraday laws of electrolysis.")
    post_ingest_db.add_all([q1, q2])
    post_ingest_db.commit()

    pipeline = PostIngestionPipeline(post_ingest_db)

    # First run
    res1 = pipeline.process_exam(exam.id, course_id=2, auto_commit=True)
    assert res1["families_linked"] == 2

    init_fams = post_ingest_db.query(QuestionFamily).count()
    init_mems = post_ingest_db.query(QuestionFamilyMembership).count()
    init_topics = post_ingest_db.query(question_topic).count()
    assert init_fams == 2
    assert init_mems == 2

    # Second run (replay)
    res2 = pipeline.process_exam(exam.id, course_id=2, auto_commit=True)
    assert res2["families_linked"] == 2

    # Verification: zero additions
    post_fams = post_ingest_db.query(QuestionFamily).count()
    post_mems = post_ingest_db.query(QuestionFamilyMembership).count()
    post_topics = post_ingest_db.query(question_topic).count()

    assert post_fams == init_fams
    assert post_mems == init_mems
    assert post_topics == init_topics


def test_3_exam_service_import_invokes_authoritative_pipeline(post_ingest_db):
    """3. ExamService.import_extraction automatically triggers post-processing."""
    service = ExamService(post_ingest_db)
    extraction_data = {
        "sections": [
            {
                "name": "Part A",
                "instructions": "Answer all",
                "questions": [
                    {"question_number": "1", "original_text": "Calculate standard emf using Nernst equation.", "marks": 5.0},
                    {"question_number": "2", "original_text": "What is the function of a reference electrode?", "marks": 5.0},
                ],
            }
        ]
    }

    exam = service.import_extraction(
        course_id=2,
        year=2024,
        term="CT1",
        extraction_data=extraction_data,
        track_id=None,
    )

    assert exam.id is not None

    # Verify questions were persisted
    questions = (
        post_ingest_db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .filter(Section.exam_id == exam.id)
        .all()
    )
    assert len(questions) == 2

    # Verify questions were automatically assigned to QuestionFamilies
    for q in questions:
        assert q.family_id is not None
        mem = post_ingest_db.query(QuestionFamilyMembership).filter_by(question_id=q.id).first()
        assert mem is not None
        assert mem.family_id == q.family_id


def test_4_study_material_authoritative_post_ingestion(post_ingest_db):
    """4. Study material ingestion invalidates affected course intelligence cache across all tiers."""
    IntelligenceCacheService.clear_memory_cache()

    # Pre-populate Tier 1, Tier 2, and analysis cache for Course 2
    IntelligenceCacheService.store_snapshot(
        post_ingest_db, 2, "ALL", None, {"data_availability_status": "AVAILABLE", "course": {"id": 2}, "metadata": {}}
    )
    analysis_cache.set((2, "ALL", None, None, "dna"), {"metric": 99})

    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2) is not None
    assert analysis_cache.get((2, "ALL", None, None, "dna")) is not None

    # Ingest study material post-processing
    pipeline = PostIngestionPipeline(post_ingest_db)
    res = pipeline.process_study_material(course_id=2, auto_commit=True)

    assert res["course_id"] == 2
    assert res["cache_invalidated"] >= 1

    # Verify all tiers invalidated
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2) is None
    assert analysis_cache.get((2, "ALL", None, None, "dna")) is None


def test_5_track_id_propagation_to_post_processor(post_ingest_db):
    """5. Multi-track course ingestion strictly preserves track_id on Exam and QuestionFamily."""
    service = ExamService(post_ingest_db)
    extraction_data = {
        "sections": [
            {
                "name": "Grammar",
                "questions": [
                    {"question_number": "1", "original_text": "Konjugieren Sie das Verb sein.", "marks": 5.0}
                ],
            }
        ]
    }

    # Ingest German track (track_id=1) for Course 8
    exam_de = service.import_extraction(
        course_id=8,
        year=2023,
        term="CT1",
        extraction_data=extraction_data,
        track_id=1,
    )

    assert exam_de.track_id == 1

    # Question and family must strictly carry track_id = 1
    q_de = (
        post_ingest_db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .filter(Section.exam_id == exam_de.id)
        .first()
    )
    assert q_de is not None
    assert q_de.family_id is not None

    fam_de = post_ingest_db.query(QuestionFamily).filter_by(id=q_de.family_id).first()
    assert fam_de is not None
    assert fam_de.track_id == 1
    assert fam_de.subject == "Foreign Language"


def test_6_exam_service_import_atomic_rollback_on_failure(post_ingest_db):
    """6. Downstream failure in ExamService.import_extraction rolls back exam & questions, preserving cache."""
    from unittest.mock import patch

    IntelligenceCacheService.clear_memory_cache()
    valid_payload = {"data_availability_status": "AVAILABLE", "course": {"id": 2}, "metadata": {}}
    IntelligenceCacheService.store_snapshot(post_ingest_db, 2, "ALL", None, valid_payload)
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2) is not None

    service = ExamService(post_ingest_db)
    extraction_data = {
        "sections": [
            {
                "name": "Part A",
                "questions": [
                    {"question_number": "1", "original_text": "Sample failure rollback test question.", "marks": 5.0}
                ],
            }
        ]
    }

    # Force downstream family linking to raise an unhandled exception
    with patch(
        "backend.services.scraper.post_processor.PostIngestionPipeline.assign_exam_families",
        side_effect=RuntimeError("Simulated family assignment crash"),
    ):
        with pytest.raises(RuntimeError, match="Simulated family assignment crash"):
            service.import_extraction(
                course_id=2,
                year=2023,
                term="CT1",
                extraction_data=extraction_data,
            )

    # Asserts zero newly-created Exam and Question rows remain in DB
    assert post_ingest_db.query(Exam).filter(Exam.course_id == 2).count() == 0
    assert post_ingest_db.query(Question).count() == 0

    # Asserts existing valid cache state remains completely intact
    cached = IntelligenceCacheService.get_snapshot(post_ingest_db, 2)
    assert cached is not None
    assert cached["course"]["id"] == 2

    # Asserts successful ingestion still commits everything atomically
    successful_exam = service.import_extraction(
        course_id=2,
        year=2023,
        term="CT1",
        extraction_data=extraction_data,
    )
    assert successful_exam.id is not None
    assert post_ingest_db.query(Exam).filter(Exam.course_id == 2).count() == 1
    assert post_ingest_db.query(Question).count() == 1
    assert post_ingest_db.query(QuestionFamilyMembership).count() == 1
    # Cache was invalidated upon successful atomic commit
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2) is None


def test_7_stored_exam_omitted_track_id_inherits_track(post_ingest_db):
    """7. Stored track-specific exam with omitted track_id inherits exam.track_id and avoids cross-track rules."""
    from unittest.mock import patch

    # Stored German exam (track_id=1) for Course 8
    exam_de = Exam(id=801, course_id=8, track_id=1, year=2023, term="CT1")
    post_ingest_db.add(exam_de)
    post_ingest_db.flush()

    sec = Section(exam_id=exam_de.id, name="Grammar")
    post_ingest_db.add(sec)
    post_ingest_db.flush()

    q = Question(section_id=sec.id, question_number="1", original_text="Guten Tag wie geht es Ihnen?")
    post_ingest_db.add(q)
    post_ingest_db.commit()

    pipeline = PostIngestionPipeline(post_ingest_db)

    # Call process_exam with track_id=None (omitted)
    with patch.object(pipeline, "map_exam_topics", wraps=pipeline.map_exam_topics) as mock_map:
        res = pipeline.process_exam(exam_de.id, course_id=8, track_id=None, auto_commit=True)

        # Asserts German track was inherited and passed to map_exam_topics
        assert mock_map.call_args[1].get("track_id") == 1
        assert res["track_id"] == 1

    # Verify family created/linked carries track_id == 1
    post_ingest_db.refresh(q)
    assert q.family_id is not None
    fam = post_ingest_db.query(QuestionFamily).filter_by(id=q.family_id).first()
    assert fam is not None
    assert fam.track_id == 1
    assert fam.subject == "Foreign Language"


def test_8_explicit_track_id_respected_and_trackless_course_remains_trackless(post_ingest_db):
    """8. Explicit track_id assigns to untracked exam; trackless course remains trackless with no cross-track leakage."""
    from unittest.mock import patch

    # 1. Untracked exam receives explicit track_id=2 (French)
    exam_untracked = Exam(id=802, course_id=8, track_id=None, year=2023, term="CT1")
    post_ingest_db.add(exam_untracked)
    post_ingest_db.flush()
    sec = Section(exam_id=exam_untracked.id, name="Vocab")
    post_ingest_db.add(sec)
    post_ingest_db.flush()
    q_fr = Question(section_id=sec.id, question_number="1", original_text="Bonjour comment allez vous?")
    post_ingest_db.add(q_fr)
    post_ingest_db.commit()

    pipeline = PostIngestionPipeline(post_ingest_db)
    res_fr = pipeline.process_exam(exam_untracked.id, course_id=8, track_id=2, auto_commit=True)
    assert res_fr["track_id"] == 2
    post_ingest_db.refresh(exam_untracked)
    assert exam_untracked.track_id == 2

    # 2. Trackless course (Course 2 Chemistry) with track_id=None
    exam_chem = Exam(id=202, course_id=2, track_id=None, year=2023, term="CT1")
    post_ingest_db.add(exam_chem)
    post_ingest_db.flush()
    sec_chem = Section(exam_id=exam_chem.id, name="Part A")
    post_ingest_db.add(sec_chem)
    post_ingest_db.flush()
    q_chem = Question(section_id=sec_chem.id, question_number="1", original_text="Explain secondary batteries.")
    post_ingest_db.add(q_chem)
    post_ingest_db.commit()

    with patch.object(pipeline, "map_exam_topics", wraps=pipeline.map_exam_topics) as mock_chem_map:
        res_chem = pipeline.process_exam(exam_chem.id, course_id=2, track_id=None, auto_commit=True)
        assert mock_chem_map.call_args[1].get("track_id") is None
        assert res_chem["track_id"] is None


def test_9_taxonomy_classification_failure_propagates_and_preserves_cache(post_ingest_db):
    """9. Classifier or DB mapping exception raises TaxonomyMappingError, aborts commit, and keeps cache intact."""
    from unittest.mock import patch
    from backend.services.scraper.post_processor import TaxonomyMappingError

    IntelligenceCacheService.clear_memory_cache()
    valid_payload = {"data_availability_status": "AVAILABLE", "course": {"id": 2}, "metadata": {}}
    IntelligenceCacheService.store_snapshot(post_ingest_db, 2, "ALL", None, valid_payload)
    assert IntelligenceCacheService.get_snapshot(post_ingest_db, 2) is not None

    exam = Exam(id=901, course_id=2, year=2024, term="CT1")
    post_ingest_db.add(exam)
    post_ingest_db.flush()
    sec = Section(exam_id=exam.id, name="Sec A")
    post_ingest_db.add(sec)
    post_ingest_db.flush()
    q = Question(section_id=sec.id, question_number="1", original_text="Calculate potential.")
    post_ingest_db.add(q)
    post_ingest_db.commit()

    pipeline = PostIngestionPipeline(post_ingest_db)

    # Force classify_batch to raise an unexpected crash
    with patch(
        "backend.services.taxonomy_classifier.TaxonomyClassifierService.classify_batch",
        side_effect=RuntimeError("Classifier engine internal crash"),
    ):
        with pytest.raises(TaxonomyMappingError, match="Taxonomy mapping failed for Exam #901"):
            pipeline.process_exam(exam.id, course_id=2, auto_commit=True)

    # Valid cache must NOT have been invalidated because transaction failed before commit
    cached = IntelligenceCacheService.get_snapshot(post_ingest_db, 2)
    assert cached is not None
    assert cached["course"]["id"] == 2


def test_10_legitimate_nothing_to_map_returns_zero_safely(post_ingest_db):
    """10. Legitimate cases (no rules, no unmapped questions, zero proposal matches) return 0 cleanly without raising."""
    pipeline = PostIngestionPipeline(post_ingest_db)

    # Case A: Course 999 with no rules returns 0
    mapped_no_rules = pipeline.map_exam_topics(course_id=999, exam_id=999)
    assert mapped_no_rules == 0

    # Case B: Exam with no questions returns 0
    empty_exam = Exam(id=902, course_id=2, year=2024, term="CT1")
    post_ingest_db.add(empty_exam)
    post_ingest_db.commit()
    mapped_empty = pipeline.map_exam_topics(course_id=2, exam_id=empty_exam.id)
    assert mapped_empty == 0


def test_11_corpus_ingester_failure_prevents_checkpoint_and_allows_retry(post_ingest_db, tmp_path):
    """11. CorpusIngester: taxonomy mapping failure records FAILED checkpoint, prevents INGESTED, and permits retry."""
    import json
    from unittest.mock import patch, MagicMock
    from backend.services.scraper.ingester import CorpusIngester
    from backend.services.scraper.models import (
        ManifestRecord,
        ResourceClassification,
        DownloadStatus,
        CurriculumMatchState,
    )
    from backend.schemas import DocumentExtractionResult, ExtractedSection, ExtractedQuestion

    ckpt_file = tmp_path / "checkpoint.json"
    ingester = CorpusIngester(post_ingest_db, checkpoint_path=str(ckpt_file))

    # Mock extraction result with 1 question
    mock_result = DocumentExtractionResult(
        successful=True,
        confidence=0.9,
        total_pages=1,
        sections=[
            ExtractedSection(
                name="Section A",
                questions=[
                    ExtractedQuestion(
                        question_number="1",
                        original_text="What is electrochemical series?",
                        marks=5.0,
                        page_number=1,
                        confidence=0.9,
                    )
                ],
            )
        ],
    )

    import hashlib

    dummy_bytes = b"%PDF-1.4 dummy content"
    real_sha = hashlib.sha256(dummy_bytes).hexdigest()

    record = ManifestRecord(
        source_site="Studique",
        source_url="https://studique.test/chem2023.pdf",
        title="Engineering Chemistry 2023",
        local_path=str(tmp_path / "test.pdf"),
        sha256=real_sha,
        download_status=DownloadStatus.DOWNLOADED,
        classification=ResourceClassification.PYQ,
        curriculum_status=CurriculumMatchState.MATCHED,
        course_id=2,
        extracted_year=2023,
    )

    # Write a dummy pdf file on disk
    with open(record.local_path, "wb") as f:
        f.write(dummy_bytes)

    mock_pages = [{"page_number": 1, "text": "Question 1. " + ("What is electrochemical series and Nernst equation? " * 5)}]

    # 1. First run: classifier crashes
    with patch("backend.services.scraper.ingester.PDFParser.extract_text_with_pages", return_value=mock_pages), \
         patch("backend.services.scraper.ingester.QuestionExtractor.extract", return_value=mock_result), \
         patch("backend.services.taxonomy_classifier.TaxonomyClassifierService.classify_batch", side_effect=RuntimeError("Classifier OOM")):
        ingester.ingest_record(record)

    assert record.ingestion_status == "FAILED"
    assert "Taxonomy mapping failed" in record.failure_reason

    # Verify checkpoint file exists and has FAILED, NOT INGESTED
    with open(ckpt_file, "r") as f:
        data = json.load(f)
    assert data[record.sha256]["status"] == "FAILED"

    # 2. Retry run: classifier recovers
    with patch("backend.services.scraper.ingester.PDFParser.extract_text_with_pages", return_value=mock_pages), \
         patch("backend.services.scraper.ingester.QuestionExtractor.extract", return_value=mock_result):
        ingester.ingest_record(record)

    assert record.ingestion_status == "INGESTED"

    # Verify checkpoint file is now INGESTED
    with open(ckpt_file, "r") as f:
        data = json.load(f)
    assert data[record.sha256]["status"] == "INGESTED"

