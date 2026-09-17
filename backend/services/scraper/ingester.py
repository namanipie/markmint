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
import re
import time
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.models.core import Document, Course, Exam
from backend.services.document import DocumentService
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor
from backend.services.extraction.vision_extractor import VisionExtractor
from backend.services.extraction.knowledge_extractor import KnowledgeExtractor
from .curriculum_resolver import CurriculumResolver

from .models import (
    ManifestRecord,
    ResourceClassification,
    CurriculumMatchState,
    DownloadStatus,
)

logger = logging.getLogger(__name__)


class CorpusIngester:
    """Ingests verified files into MarkMint's production database idempotently."""

    def __init__(
        self,
        db: Session,
        checkpoint_path: Optional[str] = "data/manifests/ingestion_checkpoint.json",
        *,
        allow_gemini: bool = False,
    ):
        self.db = db
        self.doc_service = DocumentService(db, auto_commit=False)
        self.resolver = CurriculumResolver(db)
        self.checkpoint_path = checkpoint_path
        self.checkpoint = self._load_checkpoint() if checkpoint_path else {}
        self.allow_gemini = allow_gemini
        self.stats = {
            "processed": 0,
            "ingested": 0,
            "duplicates": 0,
            "unmapped": 0,
            "failed": 0,
            "gemini_calls": 0,
            "local_calls": 0,
            "exams_created": 0,
            "questions_created": 0,
            "study_evidence_created": 0,
        }

    def _load_checkpoint(self) -> Dict[str, Any]:
        if self.checkpoint_path and os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not load checkpoint from %s: %s", self.checkpoint_path, e)
        return {}

    def _save_checkpoint(self, sha256: str, status: str, method: Optional[str] = None, error: Optional[str] = None):
        if not self.checkpoint_path:
            return
        self.checkpoint[sha256] = {
            "status": status,
            "method": method,
            "error": error,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        try:
            with open(self.checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(self.checkpoint, f, indent=2)
        except Exception as e:
            logger.warning("Could not write checkpoint to %s: %s", self.checkpoint_path, e)

    def _clear_checkpoint_success(self, sha256: str):
        """Ensure no successful checkpoint remains if a transaction failed or rolled back."""
        if self.checkpoint.get(sha256, {}).get("status") in ("INGESTED", "UNMAPPED"):
            self.checkpoint.pop(sha256, None)
            if self.checkpoint_path and os.path.exists(self.checkpoint_path):
                try:
                    with open(self.checkpoint_path, "w", encoding="utf-8") as f:
                        json.dump(self.checkpoint, f, indent=2)
                except Exception:
                    pass

    def ingest_record(self, record: ManifestRecord) -> ManifestRecord:
        """
        Ingests a single manifest record into MarkMint.
        Guarantees:
        - Verifies local file presence and validates exact SHA-256 against file content.
        - Database completion, not historical checkpoint flags, controls whether ingestion proceeds.
        - Successful ingestion: DB transaction commits BEFORE checkpoint marks success.
        - Rolled back or failed transactions clear success checkpoints.
        - Deduplicates by SHA-256 and records multi-source provenance.
        - Preserves unmapped materials without fabricating courses.
        - Unknown-year PYQs receive year=None to preserve prediction integrity.
        """
        self.stats["processed"] += 1
        record.failure_reason = None

        # Guard: must have a local file and hash
        if not record.local_path or not os.path.exists(record.local_path):
            record.ingestion_status = "FAILED"
            record.failure_reason = f"Local file not found at {record.local_path}"
            self.stats["failed"] += 1
            if record.sha256:
                self._save_checkpoint(record.sha256, "FAILED", error=record.failure_reason)
            return record

        if not record.sha256:
            record.ingestion_status = "FAILED"
            record.failure_reason = "Missing SHA-256 hash"
            self.stats["failed"] += 1
            return record

        # Guard: verify actual local file SHA-256 matches record.sha256
        try:
            with open(record.local_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            if actual_hash != record.sha256:
                record.ingestion_status = "FAILED"
                record.failure_reason = f"Local file SHA-256 mismatch: expected {record.sha256}, got {actual_hash}"
                self.stats["failed"] += 1
                self._save_checkpoint(record.sha256, "FAILED", error=record.failure_reason)
                return record
        except Exception as e:
            record.ingestion_status = "FAILED"
            record.failure_reason = f"Could not read local file at {record.local_path}: {e}"
            self.stats["failed"] += 1
            self._save_checkpoint(record.sha256, "FAILED", error=record.failure_reason)
            return record

        # 0. Check existing Document by SHA-256 (Deduplication)
        # Checkpoint is an optimization, not source of truth: Document must exist in DB.
        existing_doc = self.db.query(Document).filter(Document.document_hash == record.sha256).first()
        if existing_doc:
            # Document exists - add provenance if not already present
            self.doc_service.add_provenance(
                document_id=existing_doc.id,
                source_site=record.source_site,
                source_url=record.source_url,
                resolved_url=record.resolved_url or record.source_url,
                source_priority="DUPLICATE_SOURCE" if record.terminal_status == DownloadStatus.DUPLICATE else "PRIMARY_SOURCE",
            )
            if existing_doc.extraction_status in ("completed", "completed_empty", "completed_unmapped"):
                self.db.commit()
                status = "UNMAPPED" if existing_doc.extraction_status == "completed_unmapped" else "INGESTED"
                record.ingestion_status = status
                self.stats["duplicates"] += 1
                self._save_checkpoint(record.sha256, status, method="DEDUPLICATED")
                return record

        # 1. Register new Document record
        doc = self.doc_service.get_or_create_document(
            document_hash=record.sha256,
            source=record.source_site,
            original_url=record.source_url,
            title=record.title,
            semester=str(record.semester) if record.semester is not None else None,
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

        # 2. Curriculum Resolution if not already resolved
        if not record.course_id:
            res = self.resolver.resolve(record.subject, record.semester)
            if res.status in (CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY) and res.course_id:
                record.course_id = res.course_id
                record.curriculum_status = res.status
            else:
                record.curriculum_status = res.status

        # If still unmatched, preserve as unmapped
        if record.curriculum_status not in (CurriculumMatchState.MATCHED, CurriculumMatchState.CATALOG_ONLY) or not record.course_id:
            doc.processing_status = "unmapped"
            doc.extraction_status = "completed_unmapped"
            self.db.commit()
            record.ingestion_status = "UNMAPPED"
            self.stats["unmapped"] += 1
            self._save_checkpoint(record.sha256, "UNMAPPED", method="UNMAPPED")
            logger.info(
                "Document %d ('%s') preserved as UNMAPPED (Subject: %s)",
                doc.id, record.title, record.subject
            )
            return record

        # 3. Handle PYQ Ingestion
        if record.classification == ResourceClassification.PYQ:
            try:
                # Step 3a: Local text inspection first
                pages_data = []
                try:
                    with open(record.local_path, "rb") as f:
                        pages_data = PDFParser.extract_text_with_pages(f)
                except Exception as parse_err:
                    logger.warning("PDFParser text extraction failed: %s", parse_err)

                total_chars = sum(len(p.get("text", "")) for p in pages_data)
                full_text = " ".join(p.get("text", "") for p in pages_data)
                has_question_patterns = bool(re.search(r'\b(Part\s+[A-C]|Question\s+\d+|Q\.\s*\d|\([a-d]\))\b', full_text, re.IGNORECASE))
                is_native_text = total_chars >= 200 and has_question_patterns

                result = None
                method_used = "LOCAL_TEXT"

                if is_native_text:
                    try:
                        self.stats["local_calls"] += 1
                        result = QuestionExtractor.extract(pages_data)
                    except Exception as qe_err:
                        logger.warning("QuestionExtractor failed: %s", qe_err)

                # Step 3b: Route to Gemini Vision if not native text or QuestionExtractor yielded 0 questions
                total_extracted_q = sum(len(s.questions) for s in result.sections) if (result and result.successful and result.sections) else 0
                if total_extracted_q == 0:
                    if self.allow_gemini and os.environ.get("GEMINI_API_KEY"):
                        try:
                            logger.info("Routing %s to VisionExtractor...", record.local_path)
                            method_used = "GEMINI_VISION"
                            self.stats["gemini_calls"] += 1
                            result = VisionExtractor.extract_pdf(record.local_path)
                            time.sleep(1.0)  # Bounded rate limiting
                        except Exception as e:
                            logger.warning("VisionExtractor error: %s", e)

                if result and result.successful and result.sections and sum(len(s.questions) for s in result.sections) > 0:
                    new_exam = self.doc_service.import_exam_extraction(
                        document_id=doc.id,
                        course_id=record.course_id,
                        year=record.extracted_year,  # None if unknown, preserving temporal causality!
                        term="Fall",
                        extraction_data={**result.model_dump(), "year": record.extracted_year},
                    )
                    # DB COMMIT FIRST
                    self.db.commit()
                    # SUCCESS CHECKPOINT ONLY AFTER COMMIT
                    record.ingestion_status = "INGESTED"
                    q_count = sum(len(s.questions) for s in result.sections)
                    self.stats["ingested"] += 1
                    self.stats["exams_created"] += 1
                    self.stats["questions_created"] += q_count
                    self._save_checkpoint(record.sha256, "INGESTED", method=method_used)
                    logger.info("Ingested PYQ exam with %d sections (%d questions) via %s for Course ID %d", len(result.sections), q_count, method_used, record.course_id)
                else:
                    err = result.error_message if result else "No questions extracted"
                    doc.extraction_status = "failed"
                    self.db.commit()
                    record.ingestion_status = "FAILED"
                    record.failure_reason = f"Exam extraction failed: {err}"
                    self.stats["failed"] += 1
                    self._save_checkpoint(record.sha256, "FAILED", method=method_used, error=err)
            except Exception as e:
                logger.error("Failed to ingest PYQ: %s", e)
                self.db.rollback()
                self._clear_checkpoint_success(record.sha256)
                record.ingestion_status = "FAILED"
                record.failure_reason = str(e)
                self.stats["failed"] += 1
                self._save_checkpoint(record.sha256, "FAILED", error=str(e))

        # 4. Handle Study Material Ingestion
        elif record.classification == ResourceClassification.STUDY_MATERIAL:
            try:
                pages_data = []
                try:
                    with open(record.local_path, "rb") as f:
                        pages_data = PDFParser.extract_text_with_pages(f)
                except Exception as parse_err:
                    logger.warning("PDFParser text extraction failed: %s", parse_err)

                if pages_data:
                    result = KnowledgeExtractor.extract(pages_data)
                    if result.successful and result.concepts:
                        self.doc_service.import_knowledge_extraction(
                            document_id=doc.id,
                            extraction_data=result.model_dump(),
                            course_id=record.course_id,
                        )
                        # DB COMMIT FIRST
                        self.db.commit()
                        # SUCCESS CHECKPOINT ONLY AFTER COMMIT
                        record.ingestion_status = "INGESTED"
                        self.stats["ingested"] += 1
                        self.stats["study_evidence_created"] += len(result.concepts)
                        self._save_checkpoint(record.sha256, "INGESTED", method="LOCAL_KNOWLEDGE")
                        logger.info("Ingested %d knowledge concepts for Document ID %d", len(result.concepts), doc.id)
                    else:
                        doc.extraction_status = "completed_empty"
                        self.db.commit()
                        record.ingestion_status = "INGESTED"
                        self.stats["ingested"] += 1
                        self._save_checkpoint(record.sha256, "INGESTED", method="EMPTY_KNOWLEDGE")
                else:
                    doc.extraction_status = "completed_empty"
                    self.db.commit()
                    record.ingestion_status = "INGESTED"
                    self.stats["ingested"] += 1
                    self._save_checkpoint(record.sha256, "INGESTED", method="EMPTY_PAGES")
            except Exception as e:
                logger.error("Failed to ingest study material: %s", e)
                self.db.rollback()
                self._clear_checkpoint_success(record.sha256)
                record.ingestion_status = "FAILED"
                record.failure_reason = str(e)
                self.stats["failed"] += 1
                self._save_checkpoint(record.sha256, "FAILED", error=str(e))

        # 5. Other categories (Syllabus, Lab, Reference, Assignment, Unknown)
        else:
            try:
                doc.extraction_status = "completed"
                self.db.commit()
                record.ingestion_status = "INGESTED"
                self.stats["ingested"] += 1
                self._save_checkpoint(record.sha256, "INGESTED", method="DOCUMENT_ONLY")
            except Exception as e:
                self.db.rollback()
                self._clear_checkpoint_success(record.sha256)
                record.ingestion_status = "FAILED"
                record.failure_reason = str(e)
                self.stats["failed"] += 1
                self._save_checkpoint(record.sha256, "FAILED", error=str(e))

        return record
