"""Offline ingestion checks: isolated SQLite, temporary checkpoints, mocked Gemini."""
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path
import shutil

from backend.services.scraper.manifest import ManifestManager
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.core.database import Base
from backend.models.core import Course, Document, DocumentProvenance, Exam, Question, Section, StudyEvidence
from backend.schemas import DocumentExtractionResult, ExtractedQuestion, ExtractedSection, KnowledgeExtractionResult, ExtractedConcept
from backend.services.scraper.ingester import CorpusIngester
from backend.services.scraper.models import ManifestRecord, DownloadStatus, ResourceClassification
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor
from backend.services.extraction.knowledge_extractor import KnowledgeExtractor
from backend.services.extraction.vision_extractor import VisionExtractor
import backend.services.extraction.vision_extractor as vision


@pytest.fixture
def harness(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///:memory:')
    event.listen(engine, 'connect', lambda conn, _: conn.execute('PRAGMA foreign_keys=ON'))
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add(Course(name='Calculus And Linear Algebra', code='TEST-MATH'))
    db.commit()
    monkeypatch.setenv('GEMINI_API_KEY', 'offline-test-key')
    result = DocumentExtractionResult(successful=True, total_pages=1, sections=[
        ExtractedSection(name='Part A', questions=[ExtractedQuestion(
            question_number='1', original_text='Compute the derivative of x squared.',
            page_number=1, confidence=0.9, marks=2)])])
    local = Mock(return_value=result)
    remote = Mock(return_value=result)
    parser = Mock(return_value=[{'page_number': 1, 'text': 'Question 1 ' + 'Differentiate x squared. ' * 15}])
    monkeypatch.setattr(PDFParser, 'extract_text_with_pages', parser)
    monkeypatch.setattr(QuestionExtractor, 'extract', local)
    monkeypatch.setattr(VisionExtractor, 'extract_pdf', remote)
    monkeypatch.setattr('backend.services.scraper.ingester.time.sleep', lambda _: None)
    ingester = CorpusIngester(db, checkpoint_path=str(tmp_path / 'checkpoint.json'))

    def record(name='paper', category='PYQ', year=2023):
        path = tmp_path / (name + '.pdf')
        payload = b'%PDF-1.4\n' + name.encode() + b'\n%%EOF'
        path.write_bytes(payload)
        return ManifestRecord(source_site='Studique', source_url='https://example.test/' + name,
            semester='1', subject='Calculus And Linear Algebra', title=name,
            classification=ResourceClassification(category), extracted_year=year,
            download_status=DownloadStatus.DOWNLOADED, terminal_status='DOWNLOADED',
            local_path=str(path), sha256=hashlib.sha256(payload).hexdigest())

    yield SimpleNamespace(db=db, ingester=ingester, record=record, parser=parser,
                          local=local, remote=remote, result=result)
    db.close()
    engine.dispose()


def test_real_null_manifest_same_url_different_hash(harness, tmp_path, monkeypatch):
    h = harness
    root = Path(__file__).resolve().parents[2]
    raw = json.loads((root / 'data/manifests/first_year_union_manifest.json').read_text(encoding='utf-8'))
    original = next(item for item in raw if item.get('potential_content_duplicate') is None
                    and item.get('terminal_status') == 'DOWNLOADED')
    first_path = tmp_path / 'first.pdf'
    shutil.copyfile(root / original['local_path'], first_path)
    payload = first_path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == original['sha256']
    first = dict(original, local_path=str(first_path))
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.write_text(json.dumps([first]), encoding='utf-8')
    manager = ManifestManager(str(manifest_path))
    assert len(manager.records) == 1
    record = next(iter(manager.records.values()))
    assert record.potential_content_duplicate is None

    # Mapping/extraction are controlled fixtures; identity and provenance use real services.
    record.course_id = h.db.query(Course).one().id
    record.curriculum_status = 'MATCHED'
    record.classification = ResourceClassification.PYQ

    second_path = tmp_path / 'second.pdf'
    second_payload = payload + b'\n% distinct test content\n'
    second_path.write_bytes(second_payload)
    second = record.model_copy(update={'local_path': str(second_path),
        'sha256': hashlib.sha256(second_payload).hexdigest()})
    assert second.source_url == record.source_url
    assert second.sha256 != record.sha256
    monkeypatch.setattr(vision.genai, 'Client', Mock(side_effect=AssertionError('Network forbidden')))
    for item in (record, second):
        assert h.ingester.ingest_record(item).ingestion_status == 'INGESTED'
    assert h.db.query(Document).count() == 2
    docs = h.db.query(Document).all()
    assert {doc.document_hash for doc in docs} == {record.sha256, second.sha256}
    for doc in docs:
        assert h.db.query(DocumentProvenance).filter_by(
            document_id=doc.id, source_url=record.source_url).count() == 1
    models = (Document, DocumentProvenance, Exam, Section, Question)
    counts = tuple(h.db.query(model).count() for model in models)
    assert counts[2:] == (2, 2, 2)
    for item in (record, second):
        assert h.ingester.ingest_record(item).ingestion_status == 'INGESTED'
    assert tuple(h.db.query(model).count() for model in models) == counts
    assert h.local.call_count == 2


def test_dry_run_counts():
    """Dry-run the manifest to obtain current counts without persisting to DB."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / 'data/manifests/first_year_union_manifest.json'
    raw = json.loads(manifest_path.read_text(encoding='utf-8'))
    total = len(raw)
    null_dup = sum(1 for record in raw if record.get('potential_content_duplicate') is None)
    duplicates = sum(1 for record in raw if record.get('potential_content_duplicate') is True)
    pyq = sum(1 for record in raw if record.get('classification') == 'PYQ')
    study = sum(1 for record in raw if record.get('classification') == 'STUDY_MATERIAL')
    syllabus = sum(1 for record in raw if record.get('classification') == 'SYLLABUS')
    lab = sum(1 for record in raw if record.get('classification') == 'LAB')
    unknown = sum(1 for record in raw if record.get('classification') == 'UNKNOWN')
    print(f"Dry-run counts: total={total}, null-dup={null_dup}, dup={duplicates}, PYQ={pyq}, study={study}, syllabus={syllabus}, lab={lab}, unknown={unknown}")
    # Basic sanity: totals should match manifest lines
    assert total == 990
    assert null_dup == 865
    # Ensure at least some PYQs exist
    assert pyq > 0


def test_manifest_validation_preserves_null_and_rejects_invalid_records(tmp_path):
    valid = {
        "source_site": "Studique",
        "source_url": "https://example.test/valid",
        "title": "Valid record",
        "potential_content_duplicate": None,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([valid]), encoding="utf-8")
    manager = ManifestManager(str(manifest_path))
    assert next(iter(manager.records.values())).potential_content_duplicate is None

    manifest_path.write_text(json.dumps([{**valid, "source_site": None}]), encoding="utf-8")
    with pytest.raises(Exception):
        ManifestManager(str(manifest_path))


def test_manifest_null_accepted_and_preserved(tmp_path):
    """1. null accepted and preserved."""
    records = [
        {
            "source_site": "Studique",
            "source_url": "https://example.test/r1",
            "title": "Record 1",
            "potential_content_duplicate": None,
        },
        {
            "source_site": "TheHelpers",
            "source_url": "https://example.test/r2",
            "title": "Record 2",
        },
    ]
    manifest_path = tmp_path / "manifest_null.json"
    manifest_path.write_text(json.dumps(records), encoding="utf-8")
    manager = ManifestManager(str(manifest_path))
    assert len(manager.records) == 2
    for r in manager.records.values():
        assert r.potential_content_duplicate is None
        assert r.potential_content_duplicate_reference is None


def test_manifest_legacy_encodings_normalized(tmp_path):
    """2. every actual legacy encoding found in the manifest."""
    records = [
        {
            "source_site": "Studique",
            "source_url": "https://example.test/canonical_res",
            "title": "Canonical by res_id",
            "resource_id": "studique_abc123",
            "sha256": "hash_canonical_1",
            "potential_content_duplicate": None,
        },
        {
            "source_site": "TheHelpers",
            "source_url": "https://example.test/dup_res",
            "title": "Duplicate pointing to res_id",
            "resource_id": "helpers_dup1",
            "sha256": "hash_canonical_1",
            "potential_content_duplicate": "studique_abc123",
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/canonical_drive",
            "title": "Canonical by drive_id",
            "google_drive_id": "1ge5x8_13MtSTnMzAS7swwtscwK7tU7cv",
            "sha256": "hash_canonical_2",
            "potential_content_duplicate": None,
        },
        {
            "source_site": "TheHelpers",
            "source_url": "https://example.test/dup_drive",
            "title": "Duplicate pointing to drive_id",
            "sha256": "hash_canonical_2",
            "potential_content_duplicate": "1ge5x8_13MtSTnMzAS7swwtscwK7tU7cv",
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/bool_true",
            "title": "Boolean True",
            "potential_content_duplicate": True,
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/bool_false",
            "title": "Boolean False",
            "potential_content_duplicate": False,
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/str_true",
            "title": "String true",
            "potential_content_duplicate": "true",
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/str_false",
            "title": "String false",
            "potential_content_duplicate": "false",
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/int_1",
            "title": "Numeric 1",
            "potential_content_duplicate": 1,
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/int_0",
            "title": "Numeric 0",
            "potential_content_duplicate": 0,
        },
    ]
    manifest_path = tmp_path / "manifest_legacy.json"
    manifest_path.write_text(json.dumps(records), encoding="utf-8")
    manager = ManifestManager(str(manifest_path))
    assert len(manager.records) == len(records)

    r_dup_res = manager.records["TheHelpers:https://example.test/dup_res"]
    assert r_dup_res.potential_content_duplicate is True
    assert r_dup_res.potential_content_duplicate_reference == "studique_abc123"

    r_dup_drive = manager.records["TheHelpers:https://example.test/dup_drive"]
    assert r_dup_drive.potential_content_duplicate is True
    assert r_dup_drive.potential_content_duplicate_reference == "1ge5x8_13MtSTnMzAS7swwtscwK7tU7cv"

    assert manager.records["Studique:https://example.test/bool_true"].potential_content_duplicate is True
    assert manager.records["Studique:https://example.test/bool_false"].potential_content_duplicate is False
    assert manager.records["Studique:https://example.test/str_true"].potential_content_duplicate is True
    assert manager.records["Studique:https://example.test/str_false"].potential_content_duplicate is False
    assert manager.records["Studique:https://example.test/int_1"].potential_content_duplicate is True
    assert manager.records["Studique:https://example.test/int_0"].potential_content_duplicate is False


def test_manifest_invalid_ambiguous_values_raise_validation_errors(tmp_path):
    """3. genuinely invalid/ambiguous values raise validation errors."""
    manifest_path = tmp_path / "manifest_invalid.json"

    bad_string = [{
        "source_site": "Studique",
        "source_url": "https://example.test/bad",
        "title": "Bad Record",
        "potential_content_duplicate": "ambiguous_unknown_val",
    }]
    manifest_path.write_text(json.dumps(bad_string), encoding="utf-8")
    with pytest.raises(ValueError, match="unrecognized duplicate reference"):
        ManifestManager(str(manifest_path))

    mismatched_sha = [
        {
            "source_site": "Studique",
            "source_url": "https://example.test/t1",
            "title": "Target",
            "resource_id": "studique_target",
            "sha256": "sha_A",
        },
        {
            "source_site": "TheHelpers",
            "source_url": "https://example.test/t2",
            "title": "Mismatch",
            "resource_id": "helpers_sub",
            "sha256": "sha_B",
            "potential_content_duplicate": "studique_target",
        },
    ]
    manifest_path.write_text(json.dumps(mismatched_sha), encoding="utf-8")
    with pytest.raises(ValueError, match="different SHA-256"):
        ManifestManager(str(manifest_path))


def test_manifest_validation_error_identifies_affected_record(tmp_path):
    """4. validation errors identify the affected record."""
    records = [
        {
            "source_site": "Studique",
            "source_url": "https://example.test/good",
            "title": "Good Record",
            "potential_content_duplicate": None,
        },
        {
            "source_site": "TheHelpers",
            "source_url": "https://example.test/faulty",
            "title": "Faulty Record",
            "resource_id": "helpers_faulty_999",
            "potential_content_duplicate": "nonexistent_ref_xyz",
        },
    ]
    manifest_path = tmp_path / "manifest_ident.json"
    manifest_path.write_text(json.dumps(records), encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        ManifestManager(str(manifest_path))
    err_str = str(excinfo.value)
    assert "Manifest record 1" in err_str
    assert "helpers_faulty_999" in err_str


def test_manifest_validation_failure_cannot_silently_produce_empty_workload(tmp_path):
    """5. validation failure cannot silently produce an empty workload."""
    bad_data = [
        {
            "source_site": "Studique",
            "source_url": "https://example.test/r1",
            "title": "Valid Record",
        },
        {
            "source_site": "Studique",
            "source_url": "https://example.test/r2",
            "title": "Corrupt Record",
            "potential_content_duplicate": "unparseable_string_not_in_manifest",
        },
    ]
    manifest_path = tmp_path / "manifest_silent_fail.json"
    manifest_path.write_text(json.dumps(bad_data), encoding="utf-8")

    with pytest.raises(ValueError):
        ManifestManager(str(manifest_path))


def test_deduplication_and_provenance(harness):
    h = harness
    first = h.record()
    assert h.ingester.ingest_record(first).ingestion_status == 'INGESTED'
    second = first.model_copy(update={'source_site': 'TheHelpers', 'source_url': 'https://other.test/paper'})
    h.ingester.ingest_record(second)
    h.ingester.ingest_record(second)
    assert h.db.query(Document).count() == 1
    assert h.db.query(DocumentProvenance).count() == 2
    assert h.db.query(Exam).count() == h.db.query(Section).count() == h.db.query(Question).count() == 1
    assert h.local.call_count == 1



def test_native_text_vs_vision_routing(harness):
    h = harness
    h.ingester.allow_gemini = True
    h.ingester.ingest_record(h.record('native'))
    h.parser.return_value = [{'page_number': 1, 'text': ''}]
    h.ingester.ingest_record(h.record('scan'))
    assert h.local.call_count == h.remote.call_count == 1
    assert h.db.query(Exam).count() == 2



@pytest.mark.parametrize('error', ['429 RESOURCE_EXHAUSTED', '503 UNAVAILABLE'])
def test_gemini_transient_failures(tmp_path, monkeypatch, error):
    monkeypatch.setenv('GEMINI_API_KEY', 'offline-test-key')
    client = Mock()
    client.files.upload.return_value = SimpleNamespace(name='test-upload', state=SimpleNamespace(name='ACTIVE'))
    client.models.generate_content.side_effect = [RuntimeError(error), SimpleNamespace(text='{"sections": []}')]
    monkeypatch.setattr(vision.genai, 'Client', Mock(return_value=client))
    sleep = Mock()
    monkeypatch.setattr(vision.time, 'sleep', sleep)
    assert VisionExtractor.extract_pdf(str(tmp_path / 'mock.pdf')).successful
    assert client.models.generate_content.call_count == 2
    assert 0 < sleep.call_args.args[0] <= 60
    client.files.delete.assert_called_once_with(name='test-upload')



def test_gemini_permanent_failure(tmp_path, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'offline-test-key')
    client = Mock()
    client.files.upload.return_value = SimpleNamespace(name='test-upload', state=SimpleNamespace(name='ACTIVE'))
    client.models.generate_content.side_effect = RuntimeError('400 INVALID_ARGUMENT')
    monkeypatch.setattr(vision.genai, 'Client', Mock(return_value=client))
    assert not VisionExtractor.extract_pdf(str(tmp_path / 'mock.pdf')).successful
    assert client.models.generate_content.call_count == 1



def test_resumability_checkpointing(harness):
    h = harness
    record = h.record()
    h.ingester.ingest_record(record)
    resumed = CorpusIngester(h.db, checkpoint_path=h.ingester.checkpoint_path)
    resumed.ingest_record(record)
    assert h.local.call_count == 1
    assert json.loads(open(resumed.checkpoint_path).read())[record.sha256]['status'] == 'INGESTED'
    failed = h.record('failed')
    h.local.return_value = DocumentExtractionResult(successful=False, total_pages=1, sections=[], error_message='parse failure')
    h.remote.return_value = h.local.return_value
    assert resumed.ingest_record(failed).ingestion_status == 'FAILED'
    h.local.return_value = h.result
    assert resumed.ingest_record(failed).ingestion_status == 'INGESTED'
    assert h.db.query(Exam).count() == 2
    assert json.loads(open(resumed.checkpoint_path).read())[failed.sha256]['status'] == 'INGESTED'



def test_unknown_year_isolation(harness):
    h = harness
    h.local.return_value = h.result.model_copy(update={'year': 2099})
    h.ingester.ingest_record(h.record(year=None))
    assert h.db.query(Document).one().year is None
    assert h.db.query(Exam).one().year is None
    assert h.db.query(Exam).filter(Exam.year < 2025).count() == 0



@pytest.mark.parametrize('category', ['STUDY_MATERIAL', 'SYLLABUS', 'LAB', 'UNKNOWN'])
def test_non_pyq_routing(harness, monkeypatch, category):
    h = harness
    knowledge = Mock(return_value=KnowledgeExtractionResult(successful=True, total_pages=1, concepts=[
        ExtractedConcept(concept_name='Derivative', knowledge_type='definition', content='Rate of change',
                         original_text='Definition: Rate of change', confidence=0.8)]))
    monkeypatch.setattr(KnowledgeExtractor, 'extract', knowledge)
    assert h.ingester.ingest_record(h.record(category=category)).ingestion_status == 'INGESTED'
    assert h.db.query(Document).count() == 1
    assert h.db.query(Exam).count() == h.db.query(Question).count() == 0
    assert h.db.query(StudyEvidence).count() == (1 if category == 'STUDY_MATERIAL' else 0)
    h.local.assert_not_called()
    h.remote.assert_not_called()


def test_transactional_isolation(harness, monkeypatch):
    h = harness
    h.ingester.ingest_record(h.record('good'))
    importer = h.ingester.doc_service.import_exam_extraction

    def broken(**kwargs):
        importer(**kwargs)
        raise RuntimeError('failure after partial import')

    monkeypatch.setattr(h.ingester.doc_service, 'import_exam_extraction', broken)
    bad = h.record('bad')
    assert h.ingester.ingest_record(bad).ingestion_status == 'FAILED'
    assert h.db.query(Document).filter_by(document_hash=bad.sha256).count() == 0
    assert h.db.query(Exam).count() == 1
    monkeypatch.setattr(h.ingester.doc_service, 'import_exam_extraction', importer)
    h.ingester.ingest_record(h.record('next'))
    assert h.db.query(Exam).count() == 2


def test_sha256_file_mismatch_rejection(harness, tmp_path):
    """Phase 2 regression: file whose SHA-256 differs from manifest is rejected."""
    h = harness
    rec = h.record("mismatched_file")
    with open(rec.local_path, "wb") as f:
        f.write(b"%PDF-1.4\ncorrupted or overwritten content\n%%EOF")

    res = h.ingester.ingest_record(rec)
    assert res.ingestion_status == "FAILED"
    assert "SHA-256 mismatch" in (res.failure_reason or "")
    assert h.ingester.checkpoint[rec.sha256]["status"] == "FAILED"
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 0


def test_stale_ingested_checkpoint_with_missing_db_document_is_processed(harness):
    """Phase 4.1: stale INGESTED checkpoint + missing DB Document => record is processed."""
    h = harness
    rec = h.record("stale_chk")
    h.ingester._save_checkpoint(rec.sha256, "INGESTED", method="LEGACY")
    assert rec.sha256 in h.ingester.checkpoint
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 0

    res = h.ingester.ingest_record(rec)
    assert res.ingestion_status == "INGESTED"
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 1
    assert h.db.query(Exam).count() == 1


def test_ingested_checkpoint_with_existing_document_skipped_safely(harness):
    """Phase 4.2: INGESTED checkpoint + existing matching Document => record may be skipped safely."""
    h = harness
    rec = h.record("existing_doc")
    h.ingester.ingest_record(rec)
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 1
    assert h.local.call_count == 1

    res2 = h.ingester.ingest_record(rec)
    assert res2.ingestion_status == "INGESTED"
    assert h.local.call_count == 1


def test_checkpoint_not_written_before_db_commit(harness, monkeypatch):
    """Phase 4.3: checkpoint is not written before DB commit."""
    h = harness
    rec = h.record("commit_ordering")
    original_commit = h.db.commit
    checkpoint_at_commit_time = None

    def spy_commit():
        nonlocal checkpoint_at_commit_time
        checkpoint_at_commit_time = h.ingester.checkpoint.get(rec.sha256, {}).get("status")
        original_commit()

    monkeypatch.setattr(h.db, "commit", spy_commit)
    h.ingester.ingest_record(rec)

    assert checkpoint_at_commit_time != "INGESTED"
    assert h.ingester.checkpoint.get(rec.sha256, {}).get("status") == "INGESTED"


def test_simulated_failure_rollback_clears_success_checkpoint(harness, monkeypatch):
    """Phase 4.4: simulated failure/rollback => no success checkpoint."""
    h = harness
    rec = h.record("rollback_test")
    importer = h.ingester.doc_service.import_exam_extraction

    def failing_import(**kwargs):
        importer(**kwargs)
        raise RuntimeError("database error during exam persistence")

    monkeypatch.setattr(h.ingester.doc_service, "import_exam_extraction", failing_import)
    res = h.ingester.ingest_record(rec)
    assert res.ingestion_status == "FAILED"
    chk_status = h.ingester.checkpoint.get(rec.sha256, {}).get("status")
    assert chk_status != "INGESTED"
    assert chk_status == "FAILED"
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 0


def test_rerun_after_failure_is_idempotent(harness, monkeypatch):
    """Phase 4.5: rerun after failure is idempotent."""
    h = harness
    rec = h.record("idempotent_retry")
    importer = h.ingester.doc_service.import_exam_extraction

    fail_mock = Mock(side_effect=RuntimeError("transient network/db error"))
    monkeypatch.setattr(h.ingester.doc_service, "import_exam_extraction", fail_mock)
    res1 = h.ingester.ingest_record(rec)
    assert res1.ingestion_status == "FAILED"
    assert h.db.query(Exam).count() == 0

    monkeypatch.setattr(h.ingester.doc_service, "import_exam_extraction", importer)
    res2 = h.ingester.ingest_record(rec)
    assert res2.ingestion_status == "INGESTED"
    assert h.db.query(Exam).count() == 1
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 1

    res3 = h.ingester.ingest_record(rec)
    assert res3.ingestion_status == "INGESTED"
    assert h.db.query(Exam).count() == 1
    assert h.db.query(Document).filter_by(document_hash=rec.sha256).count() == 1
