"""
Unit tests specifically targeting the Exhaustive Source Union Crawler.
Verifies:
1. Unquoted subject key extraction from The Helpers chunk.
2. Native Google Drive window['_DRIVE_ivd'] decoding.
3. Multi-source union graph merging and provenance tracking.
4. Download source fallback when primary link fails.
5. Permanent HTTP error immediate abort.
6. Strict PDF validation (%PDF- magic bytes and %%EOF marker).
7. Multi-semester (Semesters 1-8+) catalog discovery and validation.
"""

import os
import json
import pytest
import requests
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import Course, CurriculumMapping
from backend.services.scraper.models import (
    ManifestRecord,
    DownloadStatus,
    ResourceClassification,
    CurriculumMatchState,
)
from backend.services.scraper.drive_handler import GoogleDriveHandler
from backend.services.scraper.downloader import ResourceDownloader
from backend.services.scraper.crawler import AcademicResourceCrawler
from backend.services.scraper.manifest import ManifestManager

PADDING = b"% " + (b"X" * 1024) + b"\n"
VALID_PDF_BYTES = (
    b"%PDF-1.4\n"
    + PADDING
    + b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
)


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    session.add(Course(id=1, name="Calculus And Linear Algebra", code="SEM1-CALC"))
    session.add(Course(id=2, name="Chemistry", code="SEM1-CHEM"))
    session.add(Course(id=3, name="Database Management Systems", code="SEM4-DBMS"))

    session.add(CurriculumMapping(id=1, branch_name="CSE", semester=1, curriculum_id="calc_101", subject_name="Calculus And Linear Algebra", course_id=1))
    session.add(CurriculumMapping(id=2, branch_name="CSE", semester=1, curriculum_id="chem_101", subject_name="Chemistry", course_id=2))
    session.add(CurriculumMapping(id=3, branch_name="CSE", semester=4, curriculum_id="dbms_101", subject_name="Database Management Systems", course_id=3))
    session.commit()

    yield session
    session.close()


def test_unquoted_subject_key_extraction(test_db):
    """Verify that subjects with unquoted keys (e.g. Chemistry:{...}) are extracted alongside quoted keys."""
    mock_chunk = (
        'r={1:["Calculus And Linear Algebra","Chemistry"],2:["Physics"]};'
        'l={"Calculus And Linear Algebra":{notes:[{name:"Calc Notes",url:"https://drive.google.com/file/d/CALC123/view"}]},'
        'Chemistry:{notes:[{name:"Chem Notes",url:"https://drive.google.com/file/d/CHEM456/view"}]}};'
    )

    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = mock_chunk
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        records = crawler.discover_thehelpers()

        titles = [r.title for r in records]
        assert any("Calculus And Linear Algebra - Calc Notes" in t for t in titles)
        assert any("Chemistry - Chem Notes" in t for t in titles)
        assert len(records) == 2


def test_native_drive_ivd_decoding():
    """Verify that GoogleDriveHandler._parse_drive_ivd decodes embedded JSON payload with files and folders."""
    raw_payload = json.dumps([
        ["FILE_ID_11111111111111111111", ["PARENT_ID"], "Calculus_Unit1.pdf", "application/pdf", None, None, None, None, None, None, None, None, None, 1048576],
        ["FOLDER_ID_222222222222222222", ["PARENT_ID"], "Past Papers", "application/vnd.google-apps.folder", None, None, None, None, None, None, None, None, None, 0],
    ])
    escaped_payload = raw_payload.replace('"', '\"')
    mock_html = f"<html><head><script>window['_DRIVE_ivd'] = '{escaped_payload}';</script></head></html>"

    items = GoogleDriveHandler._parse_drive_ivd(mock_html)
    assert len(items) == 2

    file_item = next(it for it in items if not it["is_folder"])
    assert file_item["id"] == "FILE_ID_11111111111111111111"
    assert file_item["name"] == "Calculus_Unit1.pdf"
    assert file_item["mime"] == "application/pdf"
    assert file_item["size"] == 1048576

    folder_item = next(it for it in items if it["is_folder"])
    assert folder_item["id"] == "FOLDER_ID_222222222222222222"
    assert folder_item["name"] == "Past Papers"


def test_union_graph_provenance_merging():
    """Verify that Studique and The Helpers records pointing to same Google Drive ID are unified."""
    rec1 = ManifestRecord(
        source_site="Studique",
        source_url="https://studique.in/unitwise#Calculus",
        resolved_url="https://drive.google.com/uc?export=download&id=SHARED_DRIVE_ID_12345",
        sources=["Studique"],
        source_urls=["https://studique.in/unitwise#Calculus"],
        resolved_urls=["https://drive.google.com/uc?export=download&id=SHARED_DRIVE_ID_12345"],
        drive_ids=["SHARED_DRIVE_ID_12345"],
        google_drive_id="SHARED_DRIVE_ID_12345",
        semester="1",
        subject="Calculus",
        title="Calculus - Unit 1 PPT",
        unit="Unit 1",
    )

    rec2 = ManifestRecord(
        source_site="TheHelpers",
        source_url="https://thehelpers.tech/semesters/1/subjects/Calculus",
        resolved_url="https://drive.google.com/uc?export=download&id=SHARED_DRIVE_ID_12345",
        sources=["TheHelpers"],
        source_urls=["https://thehelpers.tech/semesters/1/subjects/Calculus"],
        resolved_urls=["https://drive.google.com/uc?export=download&id=SHARED_DRIVE_ID_12345"],
        drive_ids=["SHARED_DRIVE_ID_12345"],
        google_drive_id="SHARED_DRIVE_ID_12345",
        semester="1",
        subject="Calculus",
        title="Calculus - Unit 1",
    )

    unified = AcademicResourceCrawler.build_union_graph([rec1], [rec2])

    assert len(unified) == 1
    item = unified[0]
    assert set(item.sources) == {"Studique", "TheHelpers"}
    assert "Studique" in item.source_site and "TheHelpers" in item.source_site
    assert len(item.source_urls) == 2
    assert item.google_drive_id == "SHARED_DRIVE_ID_12345"
    assert item.unit == "Unit 1"


def test_download_source_fallback(tmp_path, test_db):
    """Verify that if primary URL fails, crawler falls back to secondary URL in resolved_urls."""
    downloader = ResourceDownloader(corpus_dir=str(tmp_path / "corpus"))
    manifest = ManifestManager(manifest_path=str(tmp_path / "manifest.json"))
    crawler = AcademicResourceCrawler(
        db=test_db,
        manifest_manager=manifest,
        downloader=downloader,
        download_only=True,
    )

    record = ManifestRecord(
        source_site="Studique, TheHelpers",
        source_url="https://studique.in/unitwise#Calculus",
        resolved_url="https://broken-primary-url.com/file.pdf",
        sources=["Studique", "TheHelpers"],
        source_urls=["https://studique.in/unitwise#Calculus", "https://thehelpers.tech/calc"],
        resolved_urls=[
            "https://broken-primary-url.com/file.pdf",
            "https://working-secondary-url.com/file.pdf",
        ],
        google_drive_id="DRIVE_FALLBACK_TEST",
        semester="1",
        subject="Calculus And Linear Algebra",
        title="Calculus - Fallback Notes",
    )

    def mock_download_to_temp(url):
        if "broken" in url:
            return None, "HTTP 404: Not Found"
        tpath = str(tmp_path / "temp.pdf")
        with open(tpath, "wb") as f:
            f.write(VALID_PDF_BYTES)
        return tpath, None

    with patch.object(downloader, "download_to_temp", side_effect=mock_download_to_temp):
        res = crawler.process_record(record)
        assert res.download_status == DownloadStatus.DOWNLOADED
        assert res.terminal_status == "DOWNLOADED"
        assert res.local_path is not None
        assert os.path.exists(res.local_path)


def test_permanent_http_error_abort(tmp_path):
    """Verify HTTP 403/404 fails immediately without retrying."""
    downloader = ResourceDownloader(corpus_dir=str(tmp_path))

    with patch("requests.Session.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error", response=mock_resp)
        mock_get.return_value = mock_resp

        temp_path, error = downloader.download_to_temp("https://example.com/notfound.pdf")
        assert temp_path is None
        assert "404" in error
        assert mock_get.call_count == 1


def test_pdf_strict_magic_and_eof_verification(tmp_path):
    """Verify that PDFs missing EOF marker or invalid magic bytes are rejected."""
    downloader = ResourceDownloader(corpus_dir=str(tmp_path))

    # 1. Valid PDF
    valid_path = tmp_path / "valid.pdf"
    valid_path.write_bytes(VALID_PDF_BYTES)
    res_valid = downloader.validate_pdf_file(str(valid_path))
    assert res_valid.is_valid is True

    # 2. Truncated PDF (missing %%EOF)
    truncated_bytes = VALID_PDF_BYTES.replace(b"%%EOF", b"XXXXX")
    trunc_path = tmp_path / "truncated.pdf"
    trunc_path.write_bytes(truncated_bytes)
    res_trunc = downloader.validate_pdf_file(str(trunc_path))
    assert res_trunc.is_valid is False
    assert "EOF" in res_trunc.failure_reason

    # 3. HTML disguised as PDF
    html_bytes = b"<!DOCTYPE html><html><body>Error 404</body></html>" + (b" " * 1024)
    html_path = tmp_path / "fake.pdf"
    html_path.write_bytes(html_bytes)
    res_html = downloader.validate_pdf_file(str(html_path))
    assert res_html.is_valid is False
    assert "html" in res_html.failure_reason.lower()

    # 4. Non-PDF binary data (invalid magic bytes)
    garbage_bytes = (b"NON_PDF_BINARY_DATA_" * 100)
    garbage_path = tmp_path / "garbage.pdf"
    garbage_path.write_bytes(garbage_bytes)
    res_garbage = downloader.validate_pdf_file(str(garbage_path))
    assert res_garbage.is_valid is False
    assert "magic bytes" in res_garbage.failure_reason.lower()


def test_semester_filtering_first_year(test_db):
    """Verify that specifying semester_filter=1 only discovers Semester 1 subjects and isolates from higher semesters."""
    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    mock_catalog = {
        "subjects": [
            {"name": "Calculus And Linear Algebra", "ppts": [{"name": "Unit 1", "fileKey": "CALC_KEY"}]},
            {"name": "Database Management Systems", "ppts": [{"name": "Unit 1", "fileKey": "DBMS_KEY"}]},
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_catalog
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        records = crawler.discover_studique(semester_filter=1)
        subjs = [r.subject for r in records]
        assert "Calculus And Linear Algebra" in subjs
        assert "Database Management Systems" not in subjs
        assert all(r.semester == "1" for r in records)


def test_semester_3_plus_discovery_studique(test_db):
    """Verify that specifying semester_filter=4 discovers Semester 4 subjects with correct semester tagging."""
    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    mock_catalog = {
        "subjects": [
            {"name": "Calculus And Linear Algebra", "ppts": [{"name": "Unit 1", "fileKey": "CALC_KEY"}]},
            {"name": "Database Management Systems", "ppts": [{"name": "Unit 1", "fileKey": "DBMS_KEY"}]},
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_catalog
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        records = crawler.discover_studique(semester_filter=4)
        subjs = [r.subject for r in records]
        assert "Database Management Systems" in subjs
        assert "Calculus And Linear Algebra" not in subjs
        assert all(r.semester == "4" for r in records)


def test_unfiltered_crawler_discovers_all_supported_semesters(test_db):
    """Verify that when run without filter, all curriculum-backed semesters (1 and 4) are discovered."""
    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    mock_catalog = {
        "subjects": [
            {"name": "Calculus And Linear Algebra", "ppts": [{"name": "Unit 1", "fileKey": "CALC_KEY"}]},
            {"name": "Database Management Systems", "ppts": [{"name": "Unit 1", "fileKey": "DBMS_KEY"}]},
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_catalog
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        records = crawler.discover_studique()
        subjs = {r.subject: r.semester for r in records}
        assert "Calculus And Linear Algebra" in subjs
        assert subjs["Calculus And Linear Algebra"] == "1"
        assert "Database Management Systems" in subjs
        assert subjs["Database Management Systems"] == "4"


def test_invalid_and_unknown_semester_rejected(test_db):
    """Verify that invalid semesters (<= 0) or semesters not in curriculum mapping return 0 records."""
    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    mock_catalog = {
        "subjects": [
            {"name": "Calculus And Linear Algebra", "ppts": [{"name": "Unit 1", "fileKey": "CALC_KEY"}]},
            {"name": "Database Management Systems", "ppts": [{"name": "Unit 1", "fileKey": "DBMS_KEY"}]},
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_catalog
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert crawler.discover_studique(semester_filter=-1) == []
        assert crawler.discover_studique(semester_filter=0) == []
        assert crawler.discover_studique(semester_filter=999) == []


def test_unknown_course_rejected(test_db):
    """Verify that subjects not in authoritative CurriculumMapping catalog are excluded."""
    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    mock_catalog = {
        "subjects": [
            {"name": "Astrophysics and Cosmic Mining", "ppts": [{"name": "Unit 1", "fileKey": "ASTRO_KEY"}]},
            {"name": "Calculus And Linear Algebra", "ppts": [{"name": "Unit 1", "fileKey": "CALC_KEY"}]},
        ]
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_catalog
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        records = crawler.discover_studique()
        subjs = [r.subject for r in records]
        assert "Calculus And Linear Algebra" in subjs
        assert "Astrophysics and Cosmic Mining" not in subjs


def test_thehelpers_semester_4_discovery(test_db):
    """Verify that The Helpers discovers Semester 4 resources when in authoritative catalog."""
    mock_chunk = (
        'r={1:["Calculus And Linear Algebra"],4:["Database Management Systems"]};'
        'l={"Calculus And Linear Algebra":{notes:[{name:"Calc Notes",url:"https://drive.google.com/file/d/CALC123/view"}]},'
        '"Database Management Systems":{notes:[{name:"DBMS Notes",url:"https://drive.google.com/file/d/DBMS456/view"}]}};'
    )

    crawler = AcademicResourceCrawler(db=test_db, download_only=True)

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = mock_chunk
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        # 1. Targeted Semester 4 filter
        records_sem4 = crawler.discover_thehelpers(semester_filter=4)
        assert len(records_sem4) == 1
        assert records_sem4[0].subject == "Database Management Systems"
        assert records_sem4[0].semester == "4"

        # 2. Targeted Semester 1 filter
        records_sem1 = crawler.discover_thehelpers(semester_filter=1)
        assert len(records_sem1) == 1
        assert records_sem1[0].subject == "Calculus And Linear Algebra"
        assert records_sem1[0].semester == "1"

        # 3. Invalid semester rejected
        assert crawler.discover_thehelpers(semester_filter=-5) == []
        assert crawler.discover_thehelpers(semester_filter=999) == []