import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.models.core import Document, Course, CourseTrack, Exam, Section, Question, question_topic
from backend.models.submission import PaperSubmission, SubmissionStatus
from backend.services.document import DocumentService
from backend.services.extraction.pdf_parser import PDFParser
from backend.services.extraction.question_extractor import QuestionExtractor
from backend.services.observed_assessment_coverage import (
    identify_exam_assessment,
    compute_paper_observed_coverage,
)


class SubmissionApprovalService:
    """
    Safely bridges moderated submissions into the production corpus.
    Uploads stay quarantined in `PaperSubmission` until this approval workflow is executed.
    Guarantees:
    1. Idempotency (repeated approval returns consistent summary without data duplication)
    2. Duplicate hash never creates a second production document
    3. Raw filename and provenance survive
    4. Auditable course/track/assessment metadata
    5. Mapping failures remain explicitly unresolved
    6. Submissions only affect prediction evidence upon successful ingestion
    7. Atomic transactions: failures trigger immediate rollback leaving zero orphan records
    8. Rejections create zero prediction evidence
    """

    def __init__(self, db: Session):
        self.db = db
        self.doc_service = DocumentService(db, auto_commit=False)

    def approve_submission(
        self,
        submission_id: int,
        reviewer: str = "admin",
        override_course_id: Optional[int] = None,
        override_track_id: Optional[int] = None,
        override_assessment: Optional[str] = None,
        override_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Approves a PENDING or REVIEW submission and ingests it into production documents, exams, and questions.
        Idempotent: if already approved, returns existing review summary without duplicating.
        """
        submission = self.db.query(PaperSubmission).get(submission_id)
        if not submission:
            raise ValueError(f"Submission #{submission_id} not found.")

        # 1. Idempotency check: Already approved submissions return clean existing summary
        if submission.status == SubmissionStatus.APPROVED.value:
            summary = self.get_admin_review_summary(submission.id)
            return {
                "submission_id": submission.id,
                "status": submission.status,
                "document_id": submission.ingested_document_id,
                "exam_id": summary.get("approval_state", {}).get("exam_id"),
                "course_id": submission.course_id,
                "course_name": summary.get("course", {}).get("name") if summary.get("course") else submission.subject_name,
                "year": summary.get("year"),
                "assessment_type": summary.get("assessment"),
                "questions_ingested": summary.get("question_count", {}).get("total", 0),
                "questions_mapped": summary.get("question_count", {}).get("mapped", 0),
                "is_idempotent_replay": True,
                "review_summary": summary,
            }

        target_course_id = override_course_id or submission.course_id
        if not target_course_id:
            raise ValueError("Cannot approve submission without an associated Course ID.")

        course = self.db.query(Course).get(target_course_id)
        if not course:
            raise ValueError(f"Course #{target_course_id} does not exist.")

        target_track_id = override_track_id or getattr(submission, "track_id", None)
        final_year = override_year or submission.detected_year
        final_assessment = override_assessment or submission.declared_assessment or submission.detected_assessment or "ENDSEM"

        # 2. Check for duplicate document hash in production documents
        existing_doc = self.db.query(Document).filter(Document.document_hash == submission.file_hash).first()
        if existing_doc:
            provenance_url = f"student_submission:{submission.id}/session:{submission.uploader_session_id or 'anonymous'}"
            self.doc_service.add_provenance(
                document_id=existing_doc.id,
                source_site="STUDENT_SUBMISSION",
                source_url=provenance_url,
                resolved_url=submission.original_filename,
                source_priority="DUPLICATE_SOURCE",
            )
            existing_exam = self.db.query(Exam).filter(Exam.document_id == existing_doc.id).first()
            if existing_exam and target_track_id and not existing_exam.track_id:
                existing_exam.track_id = target_track_id

            submission.status = SubmissionStatus.APPROVED.value
            submission.ingested_document_id = existing_doc.id
            submission.is_duplicate = True
            submission.duplicate_of_document_id = existing_doc.id
            submission.reviewed_at = datetime.utcnow()
            submission.reviewed_by = reviewer
            if override_course_id:
                submission.course_id = override_course_id
            if target_track_id:
                submission.track_id = target_track_id

            self.db.commit()
            self.db.refresh(submission)

            summary = self.get_admin_review_summary(submission.id)
            total_q = summary.get("question_count", {}).get("total", 0)
            mapped_q = summary.get("question_count", {}).get("mapped", 0)
            return {
                "submission_id": submission.id,
                "status": submission.status,
                "document_id": existing_doc.id,
                "exam_id": existing_exam.id if existing_exam else None,
                "course_id": course.id,
                "course_name": course.name,
                "year": final_year,
                "assessment_type": final_assessment,
                "questions_ingested": total_q,
                "questions_mapped": mapped_q,
                "is_duplicate_hash": True,
                "review_summary": summary,
            }

        # 3. Fresh ingestion wrapped in atomic transaction
        if not os.path.exists(submission.file_path):
            raise FileNotFoundError(f"Submitted file not found on disk at {submission.file_path}")

        try:
            # Parse pages from submitted PDF
            with open(submission.file_path, "rb") as f:
                pages_data = PDFParser.extract_text_with_pages(f, allow_ocr=True)

            if not pages_data:
                raise ValueError("Failed to extract any text or pages from submitted PDF.")

            # Extract structured exam questions
            extraction_result = QuestionExtractor.extract(pages_data)
            extraction_dict = extraction_result.model_dump()
            extraction_dict["assessment_type"] = final_assessment
            extraction_dict["year"] = final_year

            # Create production Document preserving raw filename and provenance
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
                original_url=provenance_url,
            )

            # Record detailed provenance entry
            self.doc_service.add_provenance(
                document_id=doc.id,
                source_site="STUDENT_SUBMISSION",
                source_url=provenance_url,
                resolved_url=submission.original_filename,
                source_priority="PRIMARY_SOURCE",
            )

            # Import Exam, Sections, and Questions
            exam = self.doc_service.import_exam_extraction(
                document_id=doc.id,
                course_id=course.id,
                year=final_year,
                term=final_assessment,
                extraction_data=extraction_dict,
            )
            if target_track_id:
                exam.track_id = target_track_id
            if final_assessment:
                exam.assessment_type = final_assessment

            # Attempt conservative taxonomy mapping (unresolved questions remain explicitly unmapped)
            mapped_count = self._try_map_taxonomy(course.id, exam.id, track_id=target_track_id)

            # Compute Paper-derived observed coverage
            coverage = compute_paper_observed_coverage(exam)

            # Update submission record state
            submission.status = SubmissionStatus.APPROVED.value
            submission.ingested_document_id = doc.id
            submission.reviewed_at = datetime.utcnow()
            submission.reviewed_by = reviewer
            if override_course_id:
                submission.course_id = override_course_id
            if target_track_id:
                submission.track_id = target_track_id

            self.db.commit()
            self.db.refresh(submission)

            summary = self.get_admin_review_summary(submission.id)
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
                "is_idempotent_replay": False,
                "review_summary": summary,
            }
        except Exception as exc:
            self.db.rollback()
            raise exc

    def reject_submission(
        self,
        submission_id: int,
        reason: str,
        reviewer: str = "admin",
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

    def get_admin_review_summary(self, submission_id: int) -> Dict[str, Any]:
        """
        Returns full structured audit review summary showing:
        - course (id, code, name)
        - track if applicable (id, name, key)
        - assessment (declared, detected, final, normalized cycle, confidence)
        - year (detected or confirmed)
        - duplicate state (is_duplicate, duplicate IDs, status string)
        - question count (total, mapped, unmapped)
        - mapping rate (float and formatted percentage)
        - provenance (source, session, filename, hash, size, timestamp)
        - approval state (status, reviewer, reviewed_at, rejection_reason, document_id, exam_id)
        """
        submission = self.db.query(PaperSubmission).get(submission_id)
        if not submission:
            raise ValueError(f"Submission #{submission_id} not found.")

        # Course info
        course_data = None
        if submission.course_id:
            c = self.db.query(Course).get(submission.course_id)
            if c:
                course_data = {
                    "id": c.id,
                    "code": c.code,
                    "name": c.name,
                }

        # Track info
        track_data = None
        track_id = getattr(submission, "track_id", None)
        if track_id:
            tr = self.db.query(CourseTrack).get(track_id)
            if tr:
                track_data = {
                    "id": tr.id,
                    "name": tr.track_name,
                    "key": tr.track_key,
                }

        # Exam & question counts if approved
        doc = self.db.query(Document).get(submission.ingested_document_id) if submission.ingested_document_id else None
        exam = self.db.query(Exam).filter(Exam.document_id == doc.id).first() if doc else None

        total_questions = 0
        mapped_questions = 0
        unmapped_questions = 0
        observed_coverage_summary = None

        if exam:
            total_questions = sum(len(sec.questions) for sec in exam.sections)
            for sec in exam.sections:
                for q in sec.questions:
                    if q.topics:
                        mapped_questions += 1
                    else:
                        unmapped_questions += 1

            cov = compute_paper_observed_coverage(exam)
            observed_coverage_summary = {
                "observed_units": cov.observed_unit_numbers,
                "observed_topics_count": len(cov.observed_topic_names),
                "assessment_cycle": cov.assessment_identity.student_cycle,
                "confidence": cov.assessment_identity.confidence,
            }
            assessment_label = exam.assessment_type or exam.term or submission.declared_assessment or submission.detected_assessment or "UNKNOWN"
            exam_year = exam.year
            if not track_data and exam.track_id:
                tr = self.db.query(CourseTrack).get(exam.track_id)
                if tr:
                    track_data = {"id": tr.id, "name": tr.track_name, "key": tr.track_key}
        else:
            assessment_label = submission.declared_assessment or submission.detected_assessment or "UNKNOWN"
            exam_year = submission.detected_year

        mapping_rate = (mapped_questions / total_questions) if total_questions > 0 else 0.0

        duplicate_status = "UNIQUE"
        if submission.duplicate_of_document_id or submission.is_duplicate:
            duplicate_status = "DUPLICATE_DOCUMENT"
        elif submission.duplicate_of_submission_id:
            duplicate_status = "DUPLICATE_SUBMISSION"

        duplicate_state = {
            "is_duplicate": bool(submission.is_duplicate),
            "duplicate_of_document_id": submission.duplicate_of_document_id,
            "duplicate_of_submission_id": submission.duplicate_of_submission_id,
            "status": duplicate_status,
        }

        provenance = {
            "submission_id": submission.id,
            "source": submission.source,
            "uploader_session_id": submission.uploader_session_id,
            "original_filename": submission.original_filename,
            "file_hash": submission.file_hash,
            "file_size": submission.file_size,
            "uploaded_at": submission.created_at.isoformat() if submission.created_at else None,
        }

        approval_state = {
            "status": submission.status,
            "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
            "reviewed_by": submission.reviewed_by,
            "rejection_reason": submission.rejection_reason,
            "ingested_document_id": submission.ingested_document_id,
            "exam_id": exam.id if exam else None,
        }

        return {
            "submission_id": submission.id,
            "course": course_data,
            "track": track_data,
            "assessment": assessment_label,
            "year": exam_year,
            "duplicate_state": duplicate_state,
            "question_count": {
                "total": total_questions,
                "mapped": mapped_questions,
                "unmapped": unmapped_questions,
            },
            "mapping_rate": round(mapping_rate, 4),
            "mapping_rate_formatted": f"{round(mapping_rate * 100, 1)}%",
            "provenance": provenance,
            "approval_state": approval_state,
            "observed_coverage": observed_coverage_summary,
        }

    def get_submitter_feedback(self, submission_id: int) -> Dict[str, Any]:
        """
        Returns respectful, actionable status and feedback for the submitter
        WITHOUT exposing internal reviewer usernames, consistency algorithms, or internal IDs.
        """
        submission = self.db.query(PaperSubmission).get(submission_id)
        if not submission:
            raise ValueError(f"Submission #{submission_id} not found.")

        status = submission.status
        if status == SubmissionStatus.PENDING.value:
            badge_title = "Queued for Moderation"
            message = "Your examination paper was received and is queued for academic moderation. Thank you for helping build MarkMint!"
            actionable_tip = "Our team will verify the course and paper quality before extracting exam questions."
        elif status == SubmissionStatus.REVIEW.value:
            badge_title = "Under Academic Review"
            message = "Your paper is currently being evaluated for course alignment and complete question readability."
            actionable_tip = "Extraction and syllabus taxonomy mapping will run once review is complete."
        elif status == SubmissionStatus.APPROVED.value:
            badge_title = "Verified & Added to Corpus"
            message = "Your examination paper was verified and approved into the MarkMint intelligence corpus! Extracted questions now contribute to predictive exam forecasts."
            actionable_tip = "Explore course predictions in MintAI to see updated recurrence insights."
        elif status == SubmissionStatus.REJECTED.value:
            badge_title = "Submission Not Accepted"
            # Sanitize rejection reason for public consumption
            reason = submission.rejection_reason or "The uploaded document did not meet legibility or course alignment requirements."
            message = f"Submission notice: {reason}"
            actionable_tip = "You may submit a clearer copy or different examination paper anytime."
        else:
            badge_title = status
            message = "Your submission is currently being processed."
            actionable_tip = ""

        return {
            "tracking_id": f"#SUB-{submission.id}",
            "submission_id": submission.id,
            "status": status,
            "status_badge": badge_title,
            "subject_name": submission.subject_name,
            "original_filename": submission.original_filename,
            "submitted_at": submission.created_at.isoformat() if submission.created_at else None,
            "status_message": message,
            "actionable_tip": actionable_tip,
            "is_contributed_to_corpus": status == SubmissionStatus.APPROVED.value,
        }

    def _try_map_taxonomy(self, course_id: int, exam_id: int, track_id: Optional[int] = None) -> int:
        """
        Optionally links extracted questions to syllabus topics if taxonomy rules exist for this course.
        Supports both declarative TaxonomyRegistry definitions and individual course rules.
        Mapping failures remain explicitly unresolved (no row in question_topic).
        """
        try:
            from backend.services.taxonomy_classifier import TaxonomyClassifierService

            rules = None
            # 1. Try declarative TaxonomyRegistry first
            try:
                from backend.services.taxonomy_registry.registry import TaxonomyRegistry
                registry = TaxonomyRegistry()
                if registry.has_course(course_id):
                    rules = registry.get_topic_rules(course_id, track_id=track_id)
            except Exception:
                pass

            # 2. Fallback to hardcoded course rules map
            if not rules:
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
                # Conservative threshold: HIGH or MEDIUM confidence only
                if prop.topic_id and prop.confidence in ["HIGH", "MEDIUM"]:
                    self.db.execute(
                        question_topic.insert().values(
                            question_id=prop.question_id,
                            topic_id=prop.topic_id,
                        )
                    )
                    mapped_count += 1
                # Any question that does NOT meet the threshold remains unmapped (explicitly unresolved)

            self.db.flush()
            return mapped_count
        except Exception as e:
            import logging
            logging.getLogger("markmint").warning(f"Taxonomy auto-mapping deferred for Exam #{exam_id}: {e}")
            return 0
