"""
Automated Ingestion Pipeline for newly crawled academic resources:
- Course 30: Transforms and Boundary Value Problems (21MAB201T)
- Course 31: Probability and Queueing Theory (21MAB204T)
- Course 22: Probability and Statistics (21MAB202T)
Processes downloaded PDFs in corpus/ directory:
- SHA-256 deduplication & provenance tracking
- Examination Paper Question Extraction (OCR + Gemini Vision fallback for scanned papers)
- Lecture Notes Knowledge Extraction (KnowledgeExtractor)
- Idempotent database commits with full error handling
"""

import os
import sys
import re
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from backend.core.database import SessionLocal
from backend.models.core import Course, Document, Exam, StudyEvidence
from backend.services.document import DocumentService
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor
from backend.services.extraction.knowledge_extractor import KnowledgeExtractor
from backend.services.extraction.vision_extractor import VisionExtractor
import fitz

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_pipeline")

COURSES_TO_PROCESS = [
    {
        "id": 30,
        "name": "Transforms and Boundary Value Problems",
        "semester": 3,
        "dir": "corpus/Semester_3/Transforms and Boundary Value Problems"
    },
    {
        "id": 31,
        "name": "Probability and Queueing Theory",
        "semester": 4,
        "dir": "corpus/Semester_4/Probability and Queueing Theory"
    },
    {
        "id": 22,
        "name": "Probability and Statistics",
        "semester": 2,
        "dir": "corpus/Semester_2/Probability and Statistics"
    }
]

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_year_term(filename: str):
    year = None
    term = "Fall"
    
    y_match = re.search(r'(201\d|202\d)', filename)
    if y_match:
        year = int(y_match.group(1))

    for m in ["jan", "feb", "mar", "apr", "may", "jun", "june", "jul", "july", "aug", "sep", "oct", "nov", "dec"]:
        if m in filename.lower():
            term = m.capitalize()
            break

    return year, term

def process_exam_pdf(doc_svc: DocumentService, doc: Document, course_id: int, file_path: str, filename: str) -> bool:
    # Check if exam already exists
    existing_exam = doc_svc.db.query(Exam).filter(Exam.document_id == doc.id).first()
    if existing_exam:
        logger.info(f"    [SKIP] Exam already exists for Document ID {doc.id} (Exam ID {existing_exam.id})")
        return True

    year, term = extract_year_term(filename)
    logger.info(f"    [EXAM] Extracting: {filename} (Year={year}, Term={term})...")

    # 1. Check text density with pymupdf
    try:
        pdf_doc = fitz.open(file_path)
        total_text = "".join(p.get_text() for p in pdf_doc).strip()
        pdf_doc.close()
    except Exception as e:
        total_text = ""

    result = None
    # If text is sufficient, try local QuestionExtractor
    if len(total_text) > 300:
        logger.info(f"    [OCR Mode] Extracted {len(total_text)} characters via text stream...")
        try:
            with open(file_path, "rb") as f:
                pages_data = PDFParser.extract_text_with_pages(f)
            if pages_data:
                result = QuestionExtractor.extract(pages_data)
        except Exception as e:
            logger.warning(f"    Local extraction failed: {e}")

    # Fallback to VisionExtractor if local extraction produced 0 questions or failed
    if not result or not result.successful or sum(len(s.questions) for s in result.sections) == 0:
        logger.info("    [Vision Mode] Running Gemini Vision extraction on scanned PDF...")
        try:
            result = VisionExtractor.extract_pdf(file_path)
        except Exception as e:
            logger.error(f"    Vision extraction failed: {e}")
            return False

    if result and result.successful and result.sections:
        exam = doc_svc.import_exam_extraction(
            document_id=doc.id,
            course_id=course_id,
            year=year,
            term=term,
            extraction_data=result.model_dump()
        )
        q_count = sum(len(s.questions) for s in exam.sections)
        logger.info(f"    [SUCCESS] Ingested Exam ID {exam.id}: {len(exam.sections)} sections, {q_count} questions.")
        return True
    else:
        err = result.error_message if result else "Unknown extraction failure"
        logger.warning(f"    [FAILED] Could not extract questions: {err}")
        return False

def process_study_material_pdf(doc_svc: DocumentService, doc: Document, course_id: int, file_path: str, filename: str) -> bool:
    # Check if study evidence already exists
    existing = doc_svc.db.query(StudyEvidence).filter(StudyEvidence.document_id == doc.id).first()
    if existing:
        logger.info(f"    [SKIP] StudyEvidence already exists for Document ID {doc.id}")
        return True

    logger.info(f"    [STUDY MATERIAL] Extracting concepts: {filename}...")
    try:
        with open(file_path, "rb") as f:
            pages_data = PDFParser.extract_text_with_pages(f)

        if not pages_data or len("".join(p.get("text", "") for p in pages_data).strip()) < 100:
            logger.info("    [!] File has low text density, parsing with fitz...")
            pdf_doc = fitz.open(file_path)
            pages_data = [{"page_number": i + 1, "text": p.get_text()} for i, p in enumerate(pdf_doc) if len(p.get_text().strip()) > 30]
            pdf_doc.close()

        if not pages_data:
            logger.warning(f"    [EMPTY] No readable text found in {filename}")
            return False

        result = KnowledgeExtractor.extract(pages_data)
        if result and result.successful:
            doc_svc.import_knowledge_extraction(
                document_id=doc.id,
                extraction_data=result.model_dump(),
                course_id=course_id
            )
            logger.info(f"    [SUCCESS] Ingested {len(result.concepts)} concepts for Document ID {doc.id}.")
            return True
        else:
            logger.warning(f"    [FAILED] Knowledge extraction unsuccessful: {result.error_message if result else 'None'}")
            return False
    except Exception as e:
        logger.error(f"    [ERROR] Processing study material: {e}")
        return False

def run_ingestion():
    print("=" * 70)
    print("  MARKMINT PRODUCTION INGESTION PIPELINE")
    print("=" * 70)

    db = SessionLocal()
    doc_svc = DocumentService(db)

    stats = {
        "processed": 0,
        "exams_ingested": 0,
        "study_evidence_ingested": 0,
        "skipped": 0,
        "failed": 0
    }

    try:
        for ccfg in COURSES_TO_PROCESS:
            c_dir = ccfg["dir"]
            cid = ccfg["id"]
            cname = ccfg["name"]
            sem = ccfg["semester"]

            if not os.path.exists(c_dir):
                print(f"[!] Directory not found: {c_dir}")
                continue

            print(f"\n{'='*60}")
            print(f"  Ingesting Course {cid}: {cname} (Semester {sem})")
            print(f"{'='*60}")

            for root, dirs, files in os.walk(c_dir):
                category = os.path.basename(root)
                for f in sorted(files):
                    if not f.endswith(".pdf") or f.endswith(".tmp"):
                        continue

                    file_path = os.path.join(root, f)
                    file_hash = compute_sha256(file_path)
                    filename = f[:-4]

                    # Map resource type
                    if category == "EXAMINATION_PAPERS":
                        rtype = "examination papers / PYQs"
                    elif category == "STUDY_MATERIAL":
                        rtype = "lecture notes"
                    elif category == "SYLLABUS":
                        rtype = "syllabi"
                    else:
                        rtype = "study material / other"

                    # Register Document
                    doc = doc_svc.get_or_create_document(
                        document_hash=file_hash,
                        source="MarkMintScraper",
                        original_url=file_path,
                        title=filename,
                        semester=str(sem),
                        subject=cname,
                        resource_type=rtype
                    )

                    stats["processed"] += 1

                    if category == "EXAMINATION_PAPERS":
                        ok = process_exam_pdf(doc_svc, doc, cid, file_path, filename)
                        if ok:
                            stats["exams_ingested"] += 1
                        else:
                            stats["failed"] += 1
                    elif category == "STUDY_MATERIAL":
                        ok = process_study_material_pdf(doc_svc, doc, cid, file_path, filename)
                        if ok:
                            stats["study_evidence_ingested"] += 1
                        else:
                            stats["failed"] += 1
                    elif category == "SYLLABUS":
                        doc.extraction_status = "completed"
                        doc.extraction_confidence = 1.0
                        db.commit()
                        logger.info(f"    [SYLLABUS] Registered: {filename}")
                        stats["skipped"] += 1

        print(f"\n{'='*70}")
        print("  INGESTION PIPELINE COMPLETE")
        print(f"{'='*70}")
        print(f"  Total Files Evaluated:         {stats['processed']}")
        print(f"  Exams Processed/Ingested:      {stats['exams_ingested']}")
        print(f"  Study Evidences Ingested:      {stats['study_evidence_ingested']}")
        print(f"  Syllabi / Skipped:             {stats['skipped']}")
        print(f"  Failures:                      {stats['failed']}")
        print(f"{'='*70}")

    finally:
        db.close()

if __name__ == "__main__":
    run_ingestion()
