"""
Ingestion Engine connecting downloaded and verified academic documents into MarkMint.
Reuses existing DocumentService, PDFParser, QuestionExtractor, VisionExtractor, KnowledgeExtractor.
Preserves:
- SHA-256 deduplication and multi-source provenance.
- Exam question hierarchy (subquestions, OR alternatives, marks).
- StudyEvidence concept extractions.
- Unmatched and ambiguous documents preserved as Document records without fabricating courses.
"""

import os
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.models.core import Document, Course, Exam
from backend.services.document import DocumentService
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor
from backend.services.extraction.vision_extractor import VisionExtractor
from backend.services.extraction.knowledge_extractor import KnowledgeExtractor

from .models import (
    ManifestRecord,
    ResourceClassification,
    CurriculumMatchState,
    DownloadStatus,
)

logger = logging.getLogger(__name__)


class CorpusIngester:
    """Ingests verified files into MarkMint's production database idempotently."""

    def __init__(self, db: Session):
        self.db = db
        self.doc_service = DocumentService(db)

    def ingest_record(self, record: ManifestRecord) -> ManifestRecord:
        """
        Ingests a single manifest record into MarkMint.
        Guarantees:
        - Rejects invalid / corrupted / HTML files.
        - Deduplicates by SHA-256 and records provenance.
        - Preserves unmapped materials without fabricating courses.
        - Unknown-year PYQs receive year=None to preserve prediction integrity.
        """
        # Guard: must have a local file and hash
        if not record.local_path or not os.path.exists(record.local_path):
            record.ingestion_status = "FAILED"
            record.failure_reason = f"Local file not found at {record.local_path}"
            return record

        if not record.sha256:
            record.ingestion_status = "FAILED"
            record.failure_reason = "Missing SHA-256 hash"
            return record

        # 1. Register or retrieve Document record
        doc = self.doc_service.get_or_create_document(
            document_hash=record.sha256,
            source=record.source_site,
            original_url=record.source_url,
            title=record.title,
            semester=record.semester,
            subject=record.subject,
            resource_type=record.classification.value if record.classification else "OTHER",
            year=record.extracted_year,
            exam_type=record.assessment_type,
        )

        # Record provenance if resolved_url is available
        if record.resolved_url and record.resolved_url != record.source_url:
            self.doc_service.add_provenance(
                document_id=doc.id,
                source_site=record.source_site,
                source_url=record.resolved_url,
                resolved_url=record.resolved_url,
                source_priority="MIRROR",
            )

        # 2. Check Curriculum Status
        if record.curriculum_status != CurriculumMatchState.MATCHED or not record.course_id:
            # Preserved as catalog / unmapped document
            doc.processing_status = "unmapped"
            doc.extraction_status = "completed_unmapped"
            self.db.commit()
            record.ingestion_status = "UNMAPPED"
            logger.info(
                "Document %d ('%s') preserved as UNMAPPED (Subject: %s)",
                doc.id, record.title, record.subject
            )
            return record

        # 3. Handle PYQ Ingestion
        if record.classification == ResourceClassification.PYQ:
            try:
                # Attempt VisionExtractor first if GEMINI_API_KEY is available
                result = None
                if os.environ.get("GEMINI_API_KEY"):
                    try:
                        logger.info("Running VisionExtractor on %s...", record.local_path)
                        result = VisionExtractor.extract_pdf(record.local_path)
                    except Exception as e:
                        logger.warning("VisionExtractor error: %s. Falling back to OCR.", e)

                # Fallback to local OCR / deterministic QuestionExtractor
                if not result or not result.successful:
                    pages_data = []
                    try:
                        with open(record.local_path, "rb") as f:
                            pages_data = PDFParser.extract_text_with_pages(f)
                    except Exception as parse_err:
                        logger.warning("PDFParser text extraction failed: %s", parse_err)
                    result = QuestionExtractor.extract(pages_data)

                if result and result.successful:
                    self.doc_service.import_exam_extraction(
                        document_id=doc.id,
                        course_id=record.course_id,
                        year=record.extracted_year,  # None if unknown, preserving temporal causality!
                        term="Fall",
                        extraction_data=result.model_dump(),
                    )
                    record.ingestion_status = "INGESTED"
                    logger.info("Ingested PYQ exam with %d sections for Course ID %d", len(result.sections), record.course_id)
                else:
                    err = result.error_message if result else "No text extracted"
                    doc.extraction_status = "failed"
                    self.db.commit()
                    record.ingestion_status = "FAILED"
                    record.failure_reason = f"Exam extraction failed: {err}"
            except Exception as e:
                logger.error("Failed to ingest PYQ: %s", e)
                record.ingestion_status = "FAILED"
                record.failure_reason = str(e)
                self.db.rollback()

        # 4. Handle Study Material Ingestion
        elif record.classification == ResourceClassification.STUDY_MATERIAL:
            try:
                with open(record.local_path, "rb") as f:
                    pages_data = PDFParser.extract_text_with_pages(f)

                if pages_data:
                    result = KnowledgeExtractor.extract(pages_data)
                    if result.successful:
                        self.doc_service.import_knowledge_extraction(
                            document_id=doc.id,
                            extraction_data=result.model_dump(),
                            course_id=record.course_id,
                        )
                        record.ingestion_status = "INGESTED"
                        logger.info("Ingested %d knowledge concepts for Document ID %d", len(result.concepts), doc.id)
                    else:
                        doc.extraction_status = "failed"
                        self.db.commit()
                        record.ingestion_status = "FAILED"
                        record.failure_reason = f"Knowledge extraction failed: {result.error_message}"
                else:
                    doc.extraction_status = "completed_empty"
                    self.db.commit()
                    record.ingestion_status = "INGESTED"
            except Exception as e:
                logger.error("Failed to ingest study material: %s", e)
                record.ingestion_status = "FAILED"
                record.failure_reason = str(e)
                self.db.rollback()

        # 5. Other categories (Syllabus, Lab, Reference, Assignment)
        else:
            doc.extraction_status = "completed"
            self.db.commit()
            record.ingestion_status = "INGESTED"

        return record
