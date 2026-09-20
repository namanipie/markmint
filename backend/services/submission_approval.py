import os
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.models.core import Document, Course, Exam, Question, question_topic
from backend.models.submission import PaperSubmission, SubmissionStatus
from backend.services.document import DocumentService
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor


class SubmissionApprovalService:
    """
    Safely bridges moderated submissions into the production corpus.
    Uploads stay quarantined in `PaperSubmission` until this approval workflow is executed.
    """

    def __init__(self, db: Session):
        self.db = db
        self.doc_service = DocumentService(db, auto_commit=False)

    def approve_submission(
        self,
        submission_id: int,
        reviewer: str = "admin",
        override_course_id: Optional[int] = None,
        override_assessment: Optional[str] = None,
        override_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Approves a PENDING or REVIEW submission and ingests it into production documents, exams, and questions.
        """
        submission = self.db.query(PaperSubmission).get(submission_id)
        if not submission:
            raise ValueError(f"Submission #{submission_id} not found.")

        if submission.status == SubmissionStatus.APPROVED.value:
            raise ValueError(f"Submission #{submission_id} is already approved and ingested.")

        target_course_id = override_course_id or submission.course_id
        if not target_course_id:
            raise ValueError("Cannot approve submission without an associated Course ID.")

        course = self.db.query(Course).get(target_course_id)
        if not course:
            raise ValueError(f"Course #{target_course_id} does not exist.")

        if not os.path.exists(submission.file_path):
            raise FileNotFoundError(f"Submitted file not found on disk at {submission.file_path}")

        # 1. Parse pages from the file
        with open(submission.file_path, "rb") as f:
            pages_data = PDFParser.extract_text_with_pages(f, allow_ocr=True)

        if not pages_data:
            raise ValueError("Failed to extract any text or pages from submitted PDF.")

        # 2. Extract structured exam questions
        extraction_result = QuestionExtractor.extract(pages_data)

        # 3. Determine metadata
        final_year = override_year or submission.detected_year
        final_assessment = override_assessment or submission.declared_assessment or submission.detected_assessment or "EndSem"

        # 4. Create production Document with STUDENT_SUBMISSION provenance
        provenance_url = f"student_submission:{submission.id}/session:{submission.uploader_session_id or 'anonymous'}"
        doc = self.doc_service.get_or_create_document(
            document_hash=submission.file_hash,
            source="STUDENT_SUBMISSION",
            title=submission.original_filename,
            subject=course.name,
            semester=str(submission.semester or ""),
            resource_type="question_paper",
            year=final_year,
            exam_type=final_assessment,
            original_url=provenance_url
        )

        # 6. Import Exam, Sections, and Questions
        exam = self.doc_service.import_exam_extraction(
            document_id=doc.id,
            course_id=course.id,
            year=final_year,
            term=final_assessment,
            extraction_data=extraction_result.model_dump()
        )

        # 7. Attempt conservative taxonomy mapping if rules exist for this course
        mapped_count = self._try_map_taxonomy(course.id, exam.id)

        # 8. Update submission record state
        submission.status = SubmissionStatus.APPROVED.value
        submission.ingested_document_id = doc.id
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by = reviewer
        if override_course_id:
            submission.course_id = override_course_id

        self.db.commit()
        self.db.refresh(submission)

        total_questions = sum(len(sec.questions) for sec in exam.sections)

        return {
            "submission_id": submission.id,
            "status": submission.status,
            "document_id": doc.id,
            "exam_id": exam.id,
            "course_id": course.id,
            "course_name": course.name,
            "year": final_year,
            "assessment_type": final_assessment,
            "questions_ingested": total_questions,
            "questions_mapped": mapped_count,
        }

    def reject_submission(
        self,
        submission_id: int,
        reason: str,
        reviewer: str = "admin"
    ) -> Dict[str, Any]:
        """
        Rejects a submission with a clear audit reason.
        Strictly guarantees NO production records (Document, Exam, Question) are generated.
        """
        submission = self.db.query(PaperSubmission).get(submission_id)
        if not submission:
            raise ValueError(f"Submission #{submission_id} not found.")

        submission.status = SubmissionStatus.REJECTED.value
        submission.rejection_reason = reason
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by = reviewer

        self.db.commit()
        self.db.refresh(submission)

        return {
            "submission_id": submission.id,
            "status": submission.status,
            "rejection_reason": submission.rejection_reason,
            "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
            "reviewed_by": submission.reviewed_by,
        }

    def _try_map_taxonomy(self, course_id: int, exam_id: int) -> int:
        """
        Optionally links extracted questions to syllabus topics if taxonomy rules exist for this course.
        """
        try:
            # Check if we have registered rules for this course
            from backend.services.taxonomy_rules import (
                CHEMISTRY_TAXONOMY_RULES,
                SPCM_TAXONOMY_RULES,
                POE_TAXONOMY_RULES,
                ICB_TAXONOMY_RULES,
                PPS_TAXONOMY_RULES,
                FOE_TAXONOMY_RULES,
                BMB_TAXONOMY_RULES,
                CELLBIO_TAXONOMY_RULES,
                MICROBIO_TAXONOMY_RULES,
                PAC_TAXONOMY_RULES,
                BIOCHEM_TAXONOMY_RULES,
                EEE_TAXONOMY_RULES,
                ACCA_TAXONOMY_RULES,
                OODP_TAXONOMY_RULES,
                ESPCB_TAXONOMY_RULES,
                ENGMECH_TAXONOMY_RULES,
                PROB_TAXONOMY_RULES,
                BLDMAT_TAXONOMY_RULES,
                ENG_TAXONOMY_RULES,
            )
            from backend.services.taxonomy_classifier import TaxonomyClassifierService

            course_rules_map = {
                2: CHEMISTRY_TAXONOMY_RULES,
                3: SPCM_TAXONOMY_RULES,
                4: POE_TAXONOMY_RULES,
                5: ICB_TAXONOMY_RULES,
                6: PPS_TAXONOMY_RULES,
                7: FOE_TAXONOMY_RULES,
                8: BMB_TAXONOMY_RULES,
                9: CELLBIO_TAXONOMY_RULES,
                10: MICROBIO_TAXONOMY_RULES,
                11: PAC_TAXONOMY_RULES,
                12: BIOCHEM_TAXONOMY_RULES,
                13: EEE_TAXONOMY_RULES,
                14: ACCA_TAXONOMY_RULES,
                15: OODP_TAXONOMY_RULES,
                16: ESPCB_TAXONOMY_RULES,
                17: ENGMECH_TAXONOMY_RULES,
                18: PROB_TAXONOMY_RULES,
                19: BLDMAT_TAXONOMY_RULES,
                20: ENG_TAXONOMY_RULES,
            }

            rules = course_rules_map.get(course_id)
            if not rules:
                return 0

            classifier = TaxonomyClassifierService(rules)

            # Get newly inserted questions for this exam
            questions = (
                self.db.query(Question)
                .join(Exam, Question.section.has(exam_id=exam_id))
                .all()
            )

            if not questions:
                return 0

            payloads = [{"id": q.id, "original_text": q.original_text} for q in questions]
            proposals = classifier.classify_batch(payloads)

            mapped_count = 0
            for prop in proposals:
                if prop.topic_id and prop.confidence in ["HIGH", "MEDIUM"]:
                    # Insert into question_topic
                    self.db.execute(
                        question_topic.insert().values(
                            question_id=prop.question_id,
                            topic_id=prop.topic_id
                        )
                    )
                    mapped_count += 1

            self.db.flush()
            return mapped_count
        except Exception as e:
            # Mapping failure should not abort the exam ingestion
            import logging
            logging.getLogger("markmint").warning(f"Taxonomy auto-mapping deferred for Exam #{exam_id}: {e}")
            return 0
