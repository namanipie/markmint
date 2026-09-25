"""
Post-Ingestion Pipeline for MarkMint.

Ensures newly crawled or submitted exams automatically receive:
1. Conservative syllabus topic mappings (HIGH/MEDIUM confidence).
2. QuestionFamily linking and QuestionFamilyMembership creation (enforcing UNIQUE question_id invariant).
3. Intelligence cache invalidation across Tier 1 (memory) and Tier 2 (DB).
"""

import logging
from typing import Optional, Dict, Any, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.core import (
    Course,
    Exam,
    Section,
    Question,
    QuestionFamily,
    QuestionFamilyMembership,
    question_topic,
)
from backend.services.intelligence_cache import IntelligenceCacheService

logger = logging.getLogger(__name__)


class PostIngestionPipeline:
    """
    Deterministic post-ingestion pipeline ensuring newly crawled or submitted exams
    automatically receive syllabus topic mappings, question family assignments, and
    intelligence cache invalidation.
    """

    def __init__(self, db: Session):
        self.db = db

    def map_exam_topics(self, course_id: int, exam_id: int, track_id: Optional[int] = None) -> int:
        """
        Idempotently maps unmapped questions in exam_id using TaxonomyRegistry or fallback syllabus rules.
        Only questions not yet mapped in question_topic will be processed.
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
            except Exception as e:
                logger.debug("TaxonomyRegistry lookup skipped or failed for course %s: %s", course_id, e)

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

            # Get questions for this exam
            questions = (
                self.db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .filter(Section.exam_id == exam_id)
                .all()
            )

            # Idempotency check: only process questions that do NOT already have topic mappings
            unmapped_questions = [q for q in questions if not q.topics]
            if not unmapped_questions:
                return 0

            payloads = [{"id": q.id, "original_text": q.original_text} for q in unmapped_questions]
            proposals = classifier.classify_batch(payloads)

            mapped_count = 0
            for prop in proposals:
                # Conservative threshold: HIGH or MEDIUM confidence only
                if prop.topic_id and prop.confidence in ["HIGH", "MEDIUM"]:
                    existing_link = self.db.query(question_topic).filter(
                        question_topic.c.question_id == prop.question_id,
                        question_topic.c.topic_id == prop.topic_id,
                    ).first()
                    if not existing_link:
                        self.db.execute(
                            question_topic.insert().values(
                                question_id=prop.question_id,
                                topic_id=prop.topic_id,
                            )
                        )
                        mapped_count += 1

            self.db.flush()
            return mapped_count
        except Exception as e:
            logger.warning("Taxonomy mapping deferred/failed for Exam #%s: %s", exam_id, e)
            return 0

    def assign_exam_families(self, course_or_id: Union[Course, int], exam_or_id: Union[Exam, int]) -> int:
        """
        Assigns questions in the given exam to QuestionFamily and QuestionFamilyMembership.
        Reuses the exact/singleton family linking logic:
        - If matching family exists in the subject, join that family.
        - Otherwise, spawn a new QuestionFamily as a singleton.
        - Idempotent: respects UNIQUE(question_id) and skips already-linked questions.
        """
        if isinstance(course_or_id, Course):
            course = course_or_id
        else:
            course = self.db.query(Course).filter(Course.id == course_or_id).first()

        if isinstance(exam_or_id, Exam):
            exam = exam_or_id
        else:
            exam = self.db.query(Exam).filter(Exam.id == exam_or_id).first()

        if not course or not exam:
            return 0

        questions = (
            self.db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .filter(Section.exam_id == exam.id)
            .all()
        )
        if not questions:
            return 0

        # Load existing candidate families for this course/subject filtered strictly by track
        fam_query = self.db.query(QuestionFamily).filter(QuestionFamily.subject == course.name)
        if exam.track_id is not None:
            fam_query = fam_query.filter(QuestionFamily.track_id == exam.track_id)
        else:
            fam_query = fam_query.filter(QuestionFamily.track_id.is_(None))
        existing_families = fam_query.all()

        from backend.services.families.normalizer import QuestionNormalizer
        norm_to_family = {}
        for fam in existing_families:
            fn = QuestionNormalizer.normalize(fam.canonical_name)
            if fn and len(fn) > 10:
                norm_to_family[fn] = fam

        count_linked = 0
        for q in questions:
            # Check existing membership row (for absolute uniqueness and idempotency)
            existing_mem = (
                self.db.query(QuestionFamilyMembership)
                .filter(QuestionFamilyMembership.question_id == q.id)
                .first()
            )
            if existing_mem:
                if q.family_id is None:
                    q.family_id = existing_mem.family_id
                count_linked += 1
                continue

            if q.family_id is not None:
                # Family assigned on question but membership row missing
                membership = QuestionFamilyMembership(
                    question_id=q.id,
                    family_id=q.family_id,
                    match_type="exact",
                    similarity_score=1.0,
                    decision_method="existing_family_link",
                    algorithm_version="v1.0",
                )
                self.db.add(membership)
                count_linked += 1
                continue

            q_norm = QuestionNormalizer.normalize(q.original_text or "")
            matched_fam = norm_to_family.get(q_norm) if len(q_norm) > 10 else None

            if matched_fam:
                q.family_id = matched_fam.id
                if exam.year:
                    if matched_fam.latest_seen_year is None or exam.year > matched_fam.latest_seen_year:
                        matched_fam.latest_seen_year = exam.year
                if matched_fam.repetition_type in ("singleton", None):
                    matched_fam.repetition_type = "exact_repeat"

                membership = QuestionFamilyMembership(
                    question_id=q.id,
                    family_id=matched_fam.id,
                    match_type="exact",
                    similarity_score=1.0,
                    decision_method="lexical_hash",
                    algorithm_version="v1.0",
                )
                self.db.add(membership)
            else:
                new_family = QuestionFamily(
                    canonical_name=q.original_text or f"Question #{q.id}",
                    subject=course.name,
                    track_id=exam.track_id,
                    first_seen_year=exam.year,
                    latest_seen_year=exam.year,
                    repetition_type="singleton",
                )
                self.db.add(new_family)
                self.db.flush()

                q.family_id = new_family.id
                if len(q_norm) > 10:
                    norm_to_family[q_norm] = new_family

                membership = QuestionFamilyMembership(
                    question_id=q.id,
                    family_id=new_family.id,
                    match_type="exact",
                    similarity_score=1.0,
                    decision_method="spawn",
                    algorithm_version="v1.0",
                )
                self.db.add(membership)

            count_linked += 1

        self.db.flush()
        return count_linked

    def invalidate_cache(self, course_id: int) -> int:
        """Invalidates Tier 1 memory cache and Tier 2 persistent cache for the course."""
        return IntelligenceCacheService.invalidate_course(self.db, course_id)

    def process_exam(self, exam_id: int, course_id: int, track_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes complete post-ingestion pipeline for an exam:
        1. Topic mapping
        2. Family assignment
        3. Cache invalidation
        """
        mapped = self.map_exam_topics(course_id, exam_id, track_id=track_id)
        linked = self.assign_exam_families(course_id, exam_id)
        cache_deleted = self.invalidate_cache(course_id)
        self.db.commit()

        logger.info(
            "Post-ingestion complete for Exam #%d (Course %d): mapped=%d, families=%d, cache_evicted=%d",
            exam_id, course_id, mapped, linked, cache_deleted
        )
        return {
            "exam_id": exam_id,
            "course_id": course_id,
            "questions_mapped": mapped,
            "families_linked": linked,
            "cache_invalidated": cache_deleted,
        }
