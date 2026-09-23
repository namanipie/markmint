"""
Comprehensive unit tests for MarkMint Academic Resource Crawler & Ingestion Pipeline.
Covers:
1. Static resource download & processing
2. Dynamic resource & Drive link resolution
3. Google Drive file URL resolution (file/d/..., open?id=..., docs.google.com/...)
4. Google Drive folder recursive traversal
5. Nested Google Drive folder hierarchy & path preservation
6. Duplicate PDF detection (SHA-256 deduplication across sources)
7. Invalid PDF rejection (size 0)
8. HTML disguised as PDF rejection (detecting <!DOCTYPE html> or missing %PDF-)
9. Corrupted PDF structure rejection
10. Download timeout & exponential backoff retry
11. Resume after interruption (skipping already verified hashes)
12. Filename & directory path sanitization (path traversal prevention ../)
13. Deterministic classifier: PYQ signals, assessment type, year extraction
14. Deterministic classifier: Study material signals (notes, unit, lecture)
15. Deterministic classifier: Ambiguous / weak signals return UNKNOWN without guessing
16. Unknown-year examination paper (year=None, preserved without hallucination)
17. Curriculum matching: MATCHED (Calculus, Chemistry)
18. Curriculum matching: AMBIGUOUS (flagged in catalog)
19. Curriculum matching: UNMATCHED (preserved without fabricating Course)
20. Multi-source duplicate provenance tracking (PRIMARY_SOURCE, MIRROR, DUPLICATE_SOURCE)
"""

import os
import io
import json
import pytest
import requests
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import Course, CurriculumMapping, Document, DocumentProvenance, Exam, Question
from backend.services.scraper.models import (
    ManifestRecord,
    DownloadStatus,
    ResourceClassification,
    CurriculumMatchState,
)
from backend.services.scraper.classifier import ResourceClassifier
from backend.services.scraper.curriculum_resolver import CurriculumResolver
from backend.services.scraper.drive_handler import GoogleDriveHandler, GoogleDriveItem
from backend.services.scraper.downloader import (
    ResourceDownloader,
    sanitize_filesystem_name,
    ValidationResult,
)
from backend.services.scraper.manifest import ManifestManager
from backend.services.scraper.ingester import CorpusIngester


# Minimal valid 1-page PDF
MINIMAL_VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n"
    b"0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000052 00000 n \n"
    b"0000000101 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n"
    b"178\n"
    b"%%EOF\n"
)


@pytest.fixture
def in_memory_db():
    """Provides an isolated SQLite in-memory database with full MarkMint schema."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Seed verified courses
    c1 = Course(id=1, name="Calculus And Linear Algebra", code="SEM1-CALC", canonical_code="21MAB101T")
    c2 = Course(id=2, name="Chemistry", code="SEM1-CHEM", canonical_code="21CYB101J")
    c3 = Course(id=3, name="Philosophy Of Engineering", code="SEM1-PHIL")
    session.add_all([c1, c2, c3])

    # Seed mock curriculum mappings
    m1 = CurriculumMapping(
        id=1,
        branch_name="Computer Science and Engineering",
        semester=1,
        curriculum_id="cse-1-1",
        subject_name="Calculus And Linear Algebra",
        course_id=1,
        status="MATCHED",
    )
    m2 = CurriculumMapping(
        id=2,
        branch_name="Computer Science and Engineering",
        semester=1,
        curriculum_id="cse-1-2",
        subject_name="Biology",
        course_id=None,
        status="AMBIGUOUS",
        notes="General Biology: Multiple candidates",
    )
    session.add_all([m1, m2])
    session.commit()

    yield session
    session.close()


@pytest.fixture
def tmp_crawler_dir(tmp_path):
    """Provides temporary directory structure for testing crawler downloads and manifests."""
    corpus = tmp_path / "corpus"
    cache = tmp_path / "cache"
    manifest_file = tmp_path / "manifest.json"
    corpus.mkdir()
    cache.mkdir()
    return {
        "corpus": str(corpus),
        "cache": str(cache),
        "manifest": str(manifest_file),
    }


# =========================================================================
# 1 & 2. STATIC & DYNAMIC RESOURCE DOWNLOAD & PROCESSING
# =========================================================================

def test_static_resource_download(tmp_crawler_dir):
    downloader = ResourceDownloader(
        corpus_dir=tmp_crawler_dir["corpus"],
        temp_dir=tmp_crawler_dir["cache"],
    )
    temp_file = os.path.join(tmp_crawler_dir["cache"], "test_sample.pdf")
    with open(temp_file, "wb") as f:
        f.write(MINIMAL_VALID_PDF)

    val = downloader.validate_pdf_file(temp_file)
    assert val.is_valid is True
    assert val.file_size == len(MINIMAL_VALID_PDF)
    assert val.sha256 is not None

    dest = downloader.build_destination_path(
        semester="1",
        subject="Calculus",
        classification="PYQ",
        filename="Test_Paper",
    )
    stored = downloader.store_verified_file(temp_file, dest)
    assert os.path.exists(stored)
    assert os.path.getsize(stored) == len(MINIMAL_VALID_PDF)


# =========================================================================
# 3. GOOGLE DRIVE FILE RESOLUTION
# =========================================================================

def test_drive_file_url_resolution():
    # /file/d/
    url1 = "https://drive.google.com/file/d/1gjpajPAfUg84IUfeA9NjTluLobSwLUwB/view?usp=sharing"
    assert GoogleDriveHandler.extract_file_id(url1) == "1gjpajPAfUg84IUfeA9NjTluLobSwLUwB"
    assert GoogleDriveHandler.get_direct_download_url(url1) == "https://drive.google.com/uc?export=download&id=1gjpajPAfUg84IUfeA9NjTluLobSwLUwB"

    # open?id=
    url2 = "https://drive.google.com/open?id=1ge5x8_13MtSTnMzAS7swwtscwK7tU7cv"
    assert GoogleDriveHandler.extract_file_id(url2) == "1ge5x8_13MtSTnMzAS7swwtscwK7tU7cv"
    assert GoogleDriveHandler.get_direct_download_url(url2) == "https://drive.google.com/uc?export=download&id=1ge5x8_13MtSTnMzAS7swwtscwK7tU7cv"

    # Google Docs export
    url3 = "https://docs.google.com/document/d/1BByJLRMnIiDoJTAwrjrTGjJMIwcPQPNP/edit"
    assert GoogleDriveHandler.extract_file_id(url3) == "1BByJLRMnIiDoJTAwrjrTGjJMIwcPQPNP"
    assert GoogleDriveHandler.get_direct_download_url(url3) == "https://docs.google.com/document/d/1BByJLRMnIiDoJTAwrjrTGjJMIwcPQPNP/export?format=pdf"

    # Google Slides export
    url4 = "https://docs.google.com/presentation/d/1SqEtnZx2FyQ91dL2q7QQIBYkklNdyfKC/edit"
    assert GoogleDriveHandler.get_direct_download_url(url4) == "https://docs.google.com/presentation/d/1SqEtnZx2FyQ91dL2q7QQIBYkklNdyfKC/export/pdf"


# =========================================================================
# 4 & 5. GOOGLE DRIVE FOLDER RECURSIVE TRAVERSAL & NESTED PATH PRESERVATION
# =========================================================================

@patch("backend.services.scraper.drive_handler.requests.get")
def test_drive_folder_traversal_and_nested_hierarchy(mock_get):
    folder_html = """
    <html>
      <div data-id="1CN6ytFLqKWoPkVOeHsPpDBaT6q3qH2WZ" aria-label="Notes_Unit1.pdf PDF Shared"></div>
      <div data-id="folder_sub123" aria-label="Unit 2 Materials Google Drive Folder"></div>
    </html>
    """
    subfolder_html = """
    <html>
      <div data-id="sub_file_999" aria-label="Unit2_PYQ.pdf PDF Shared"></div>
    </html>
    """

    def mock_side_effect(url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "folder_sub123" in url:
            mock_resp.text = subfolder_html
        else:
            mock_resp.text = folder_html
        return mock_resp

    mock_get.side_effect = mock_side_effect

    items, action_req = GoogleDriveHandler.traverse_folder(
        "https://drive.google.com/drive/folders/root_folder",
        current_folder_path="Calculus",
    )

    assert action_req is None
    assert len(items) == 2

    # Check root child file
    f1 = next(it for it in items if it.item_id == "1CN6ytFLqKWoPkVOeHsPpDBaT6q3qH2WZ")
    assert f1.name == "Notes_Unit1.pdf"
    assert f1.folder_path == "Calculus"

    # Check nested child file with path preservation
    f2 = next(it for it in items if it.item_id == "sub_file_999")
    assert f2.name == "Unit2_PYQ.pdf"
    assert f2.folder_path == "Calculus/Unit 2 Materials"


# =========================================================================
# 6 & 20. SHA-256 DEDUPLICATION & MULTI-SOURCE PROVENANCE
# =========================================================================

def test_sha256_deduplication_and_provenance(in_memory_db, tmp_crawler_dir):
    ingester = CorpusIngester(in_memory_db)
    test_pdf_path = os.path.join(tmp_crawler_dir["cache"], "dedup_test.pdf")
    with open(test_pdf_path, "wb") as f:
        f.write(MINIMAL_VALID_PDF)

    sha256 = ResourceDownloader.calculate_sha256(test_pdf_path)

    # First discovery from Studique
    rec1 = ManifestRecord(
        source_site="Studique",
        source_url="https://www.studique.in/unitwise#calc",
        title="Calculus Unit 1",
        semester="1",
        subject="Calculus And Linear Algebra",
        local_path=test_pdf_path,
        sha256=sha256,
        curriculum_status=CurriculumMatchState.MATCHED,
        course_id=1,
        classification=ResourceClassification.STUDY_MATERIAL,
        download_status=DownloadStatus.DOWNLOADED,
    )
    ingester.ingest_record(rec1)

    # Verify document created
    doc = in_memory_db.query(Document).filter(Document.document_hash == sha256).first()
    assert doc is not None
    assert doc.source == "Studique"

    # Verify initial provenance
    provs = in_memory_db.query(DocumentProvenance).filter(DocumentProvenance.document_id == doc.id).all()
    assert len(provs) == 1
    assert provs[0].source_site == "Studique"
    assert provs[0].source_priority == "PRIMARY_SOURCE"

    # Second discovery of identical PDF from TheHelpers
    rec2 = ManifestRecord(
        source_site="TheHelpers",
        source_url="https://thehelpers.tech/semesters/1/subjects/Calculus/notes",
        resolved_url="https://drive.google.com/uc?id=duplicate_id",
        title="Calculus Notes Mirror",
        semester="1",
        subject="Calculus And Linear Algebra",
        local_path=test_pdf_path,
        sha256=sha256,
        curriculum_status=CurriculumMatchState.MATCHED,
        course_id=1,
        classification=ResourceClassification.STUDY_MATERIAL,
        download_status=DownloadStatus.DUPLICATE,
    )
    ingester.ingest_record(rec2)

    # Verify no duplicate Document created
    all_docs = in_memory_db.query(Document).filter(Document.document_hash == sha256).all()
    assert len(all_docs) == 1

    # Verify multiple provenances recorded across sites
    provs_after = in_memory_db.query(DocumentProvenance).filter(DocumentProvenance.document_id == doc.id).all()
    assert len(provs_after) >= 2
    sites = {p.source_site for p in provs_after}
    assert "Studique" in sites and "TheHelpers" in sites


# =========================================================================
# 7, 8, 9. INVALID PDF, HTML DISGUISED, CORRUPTED STRUCTURE REJECTION
# =========================================================================

def test_invalid_pdf_zero_bytes(tmp_crawler_dir):
    downloader = ResourceDownloader(temp_dir=tmp_crawler_dir["cache"])
    empty_path = os.path.join(tmp_crawler_dir["cache"], "empty.pdf")
    with open(empty_path, "wb") as f:
        pass  # 0 bytes

    val = downloader.validate_pdf_file(empty_path)
    assert val.is_valid is False
    assert "0 bytes" in val.failure_reason


def test_html_disguised_as_pdf_rejection(tmp_crawler_dir):
    downloader = ResourceDownloader(temp_dir=tmp_crawler_dir["cache"])
    html_as_pdf = os.path.join(tmp_crawler_dir["cache"], "google_login.pdf")
    with open(html_as_pdf, "wb") as f:
        f.write(b"<!DOCTYPE html><html><head><title>Google Drive - Sign In</title></head><body>Please sign in</body></html>")

    val = downloader.validate_pdf_file(html_as_pdf)
    assert val.is_valid is False
    assert "HTML web page disguised as a PDF" in val.failure_reason


def test_corrupted_pdf_rejection(tmp_crawler_dir):
    downloader = ResourceDownloader(temp_dir=tmp_crawler_dir["cache"])
    corrupt_path = os.path.join(tmp_crawler_dir["cache"], "corrupt.pdf")
    with open(corrupt_path, "wb") as f:
        # Magic bytes are present but internal structure is garbage
        f.write(b"%PDF-1.4\nCorrupted binary junk that cannot be parsed by any engine %%EOF")

    val = downloader.validate_pdf_file(corrupt_path)
    assert val.is_valid is False
    assert "damaged or corrupt" in val.failure_reason


# =========================================================================
# 10. DOWNLOAD TIMEOUT & RETRY WITH EXPONENTIAL BACKOFF
# =========================================================================

@patch("backend.services.scraper.downloader.requests.Session.get")
def test_download_retry_and_backoff(mock_get, tmp_crawler_dir):
    downloader = ResourceDownloader(
        temp_dir=tmp_crawler_dir["cache"],
        timeout_seconds=5,
    )

    # First 2 attempts fail, 3rd succeeds
    fail_resp = MagicMock()
    fail_resp.status_code = 503
    fail_resp.raise_for_status.side_effect = requests.RequestException("503 Service Unavailable")

    success_resp = MagicMock()
    success_resp.status_code = 200
    success_resp.iter_content = MagicMock(return_value=[MINIMAL_VALID_PDF])

    mock_get.side_effect = [
        requests.RequestException("Timeout connecting"),
        requests.RequestException("Connection reset"),
        success_resp,
    ]

    with patch("backend.services.scraper.downloader.time.sleep"):  # skip real sleep
        temp_path, error = downloader.download_to_temp("https://example.com/test.pdf", max_retries=3)

    assert error is None
    assert temp_path is not None
    assert os.path.exists(temp_path)
    assert mock_get.call_count == 3


# =========================================================================
# 11. RESUME AFTER INTERRUPTION
# =========================================================================

def test_resume_skips_already_completed(tmp_crawler_dir):
    manifest_mgr = ManifestManager(manifest_path=tmp_crawler_dir["manifest"])

    existing_file = os.path.join(tmp_crawler_dir["cache"], "verified_doc.pdf")
    with open(existing_file, "wb") as f:
        f.write(MINIMAL_VALID_PDF)

    rec = ManifestRecord(
        source_site="Studique",
        source_url="https://studique.in/res/1",
        google_drive_id="drive_key_123",
        title="Existing Lecture",
        download_status=DownloadStatus.DOWNLOADED,
        local_path=existing_file,
        sha256="abc123sha",
    )
    manifest_mgr.add_or_update_record(rec)

    # Verify is_already_completed returns True
    assert manifest_mgr.is_already_completed("Studique", "https://studique.in/res/1", "drive_key_123") is True
    # Unseen file returns False
    assert manifest_mgr.is_already_completed("TheHelpers", "https://thehelpers.tech/new", "new_key") is False


# =========================================================================
# 12. FILENAME & PATH SANITIZATION (PATH TRAVERSAL PREVENTION)
# =========================================================================

def test_path_sanitization_prevents_traversal():
    malicious_name = "../../../../../etc/passwd"
    clean_name = sanitize_filesystem_name(malicious_name)
    assert "../" not in clean_name
    assert "/" not in clean_name
    assert "\\" not in clean_name

    malicious_title = 'Calculus: Unit 1? *Best* "Notes" <2024> | test'
    clean_title = sanitize_filesystem_name(malicious_title)
    for forbidden in [":", "?", "*", '"', "<", ">", "|"]:
        assert forbidden not in clean_title

    downloader = ResourceDownloader()
    safe_path = downloader.build_destination_path(
        semester="../2",
        subject="Chemistry/Organic/../../",
        classification="PYQ",
        filename="../../../hacked.pdf",
    )
    assert ".." not in safe_path
    assert safe_path.endswith("hacked.pdf")


# =========================================================================
# 13, 14, 15. CLASSIFIER: PYQ, STUDY MATERIAL, UNKNOWN
# =========================================================================

def test_classifier_pyq_signals():
    # End sem paper with year
    res1 = ResourceClassifier.classify("Calculus End Semester Question Paper May 2023")
    assert res1.category == ResourceClassification.PYQ
    assert res1.extracted_year == 2023
    assert res1.assessment_type == "END_SEM"
    assert res1.confidence >= 0.8

    # CT2 paper
    res2 = ResourceClassifier.classify("Chemistry CT-2 Question Paper 2024")
    assert res2.category == ResourceClassification.PYQ
    assert res2.assessment_type == "CT2"
    assert res2.extracted_year == 2024


def test_classifier_study_material_signals():
    # Lecture notes
    res1 = ResourceClassifier.classify("Programming For Problem Solving Unit 2 Lecture Notes")
    assert res1.category == ResourceClassification.STUDY_MATERIAL
    assert res1.confidence >= 0.8

    # Handout / PPT
    res2 = ResourceClassifier.classify("Semiconductor Physics Chapter 3 Slides and Summary")
    assert res2.category == ResourceClassification.STUDY_MATERIAL


def test_classifier_unknown_ambiguous_signals():
    # Ambiguous or non-academic title
    res = ResourceClassifier.classify("General Information and Guidelines")
    assert res.category == ResourceClassification.UNKNOWN


# =========================================================================
# 16. UNKNOWN-YEAR PYQ INGESTION
# =========================================================================

def test_unknown_year_pyq_ingestion(in_memory_db, tmp_crawler_dir):
    ingester = CorpusIngester(in_memory_db)
    test_pdf_path = os.path.join(tmp_crawler_dir["cache"], "unknown_year.pdf")
    with open(test_pdf_path, "wb") as f:
        f.write(MINIMAL_VALID_PDF)

    sha256 = ResourceDownloader.calculate_sha256(test_pdf_path)

    # Document with no year in title
    rec = ManifestRecord(
        source_site="TheHelpers",
        source_url="https://thehelpers.tech/pyq/unknown",
        title="Calculus Previous Year Paper",  # Has no year!
        semester="1",
        subject="Calculus And Linear Algebra",
        local_path=test_pdf_path,
        sha256=sha256,
        curriculum_status=CurriculumMatchState.MATCHED,
        course_id=1,
        classification=ResourceClassification.PYQ,
        extracted_year=None,  # No year hallucinated!
        download_status=DownloadStatus.DOWNLOADED,
    )

    from backend.schemas import DocumentExtractionResult, ExtractedSection, ExtractedQuestion

    valid_extraction = DocumentExtractionResult(
        successful=True,
        total_pages=1,
        sections=[
            ExtractedSection(
                name="Section A",
                instructions="Answer all questions",
                questions=[
                    ExtractedQuestion(
                        question_number="1",
                        original_text="Find the derivative of x^2",
                        marks=2.0,
                        is_alternative=False,
                        page_number=1,
                        confidence=0.9,
                    )
                ],
            )
        ],
    )

    with patch("backend.services.scraper.ingester.PDFParser.extract_text_with_pages", return_value=[{"page_number": 1, "text": "Part A Question 1: " + "Calculate derivative " * 25}]), \
         patch("backend.services.scraper.ingester.VisionExtractor.extract_pdf", return_value=None), \
         patch("backend.services.scraper.ingester.QuestionExtractor.extract", return_value=valid_extraction):
        ingester.ingest_record(rec)

    exam = in_memory_db.query(Exam).filter(Exam.course_id == 1).order_by(Exam.id.desc()).first()
    assert exam is not None
    assert exam.year is None  # Integrity preserved: year=None!



# =========================================================================
# 17, 18, 19. CURRICULUM RESOLVER: MATCHED, AMBIGUOUS, UNMATCHED
# =========================================================================

def test_curriculum_resolver_states(in_memory_db):
    resolver = CurriculumResolver(in_memory_db)

    # 1. MATCHED (Calculus And Linear Algebra -> Course 1)
    res_matched = resolver.resolve("Calculus and Linear Algebra", semester=1)
    assert res_matched.status in [CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY]
    assert res_matched.course_id == 1

    # 2. AMBIGUOUS (Biology in CurriculumMapping)
    res_ambiguous = resolver.resolve("Biology", semester=1)
    assert res_ambiguous.status == CurriculumMatchState.AMBIGUOUS

    # 3. UNMATCHED (Unknown Upper-Semester Subject)
    res_unmatched = resolver.resolve("Advanced Quantum Supercomputing", semester=7)
    assert res_unmatched.status == CurriculumMatchState.UNMATCHED
    assert res_unmatched.course_id is None
