"""
Corpus and Intelligence Health Service for MarkMint.
Provides factual, measurable auditing of historical examination data feeding MintAI.
Answers: "Can we trust the data currently feeding MintAI?"
"""

from typing import Any, Dict, List, Optional, Set
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from backend.models.core import (
    Course, CourseTrack, Exam, Section, Question, Topic, Unit, Syllabus,
    Document, QuestionFamily, question_topic
)
from backend.services.dna.analyzer import DNAAnalyzerService, DataSufficiency
from backend.services.assessment_cycle import normalize_assessment_cycle


class CorpusHealthService:
    """Computes factual health metrics for the examination corpus feeding MintAI."""

    @classmethod
    def get_course_health(
        cls,
        db: Session,
        course: Course,
        active_track: Optional[CourseTrack] = None,
        assessment_cycle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive intelligence health report for a specific course."""
        norm_cycle = normalize_assessment_cycle(assessment_cycle) if assessment_cycle else None

        # 1. Exams Query (strictly isolated by course, track, cycle)
        exams_q = db.query(Exam).filter(Exam.course_id == course.id)
        if active_track:
            exams_q = exams_q.filter(Exam.track_id == active_track.id)
        if norm_cycle and norm_cycle != "ALL":
            exams_q = exams_q.filter(func.upper(Exam.assessment_type) == norm_cycle.upper())

        exams = exams_q.all()
        exam_ids = [e.id for e in exams]

        # Year categorization (separating valid from unknown/null years)
        valid_year_exams = [e for e in exams if e.year is not None and e.year > 0]
        unknown_year_exams = [e for e in exams if e.year is None or e.year <= 0]
        unknown_year_exam_ids = sorted([e.id for e in unknown_year_exams])

        years_observed = sorted(list({e.year for e in valid_year_exams}))
        year_range = [years_observed[0], years_observed[-1]] if years_observed else None

        # Missing years strictly calculated over the observed span
        if years_observed and len(years_observed) > 1:
            full_span = list(range(years_observed[0], years_observed[-1] + 1))
            missing_years = [y for y in full_span if y not in years_observed]
        else:
            missing_years = []

        exams_by_year_counter = Counter(e.year for e in valid_year_exams)
        exams_by_year: Dict[str, int] = {str(y): exams_by_year_counter[y] for y in years_observed}
        if unknown_year_exams:
            exams_by_year["unknown"] = len(unknown_year_exams)

        exams_by_cycle_counter = Counter(
            (normalize_assessment_cycle(e.assessment_type) or "UNKNOWN") for e in exams
        )
        exams_by_cycle: Dict[str, int] = dict(sorted(exams_by_cycle_counter.items()))

        # 2. Questions Query (strictly isolated to retrieved exams)
        if exam_ids:
            questions = (
                db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .filter(Section.exam_id.in_(exam_ids))
                .all()
            )
        else:
            questions = []

        total_extracted = len(questions)
        q_ids = [q.id for q in questions]

        # Topics mapping
        if q_ids:
            mapped_rows = (
                db.query(question_topic.c.question_id, question_topic.c.topic_id)
                .filter(question_topic.c.question_id.in_(q_ids))
                .all()
            )
            q_to_topics: Dict[int, Set[int]] = {}
            for q_id, t_id in mapped_rows:
                q_to_topics.setdefault(q_id, set()).add(t_id)
        else:
            q_to_topics = {}

        classified_with_topic_count = sum(1 for q in questions if len(q_to_topics.get(q.id, set())) > 0)
        classified_with_type_count = sum(1 for q in questions if q.question_type is not None)
        classified_with_family_count = sum(1 for q in questions if q.family_id is not None)

        unresolved_q_ids = sorted([q.id for q in questions if len(q_to_topics.get(q.id, set())) == 0])
        unresolved_questions_count = len(unresolved_q_ids)
        needs_review_count = sum(1 for q in questions if bool(q.needs_review))

        # Unknown year questions
        unknown_year_exam_id_set = set(unknown_year_exam_ids)
        if unknown_year_exam_id_set and q_ids:
            unknown_year_q_count = (
                db.query(func.count(Question.id))
                .join(Section, Question.section_id == Section.id)
                .filter(Section.exam_id.in_(unknown_year_exam_id_set))
                .scalar()
                or 0
            )
        else:
            unknown_year_q_count = 0

        # 3. Question Families Aggregation
        family_ids_in_scope = sorted(list({q.family_id for q in questions if q.family_id is not None}))
        if family_ids_in_scope:
            families_objs = (
                db.query(QuestionFamily)
                .filter(QuestionFamily.id.in_(family_ids_in_scope))
                .all()
            )
            fam_rep_types = {f.id: (f.repetition_type or "singleton") for f in families_objs}
        else:
            fam_rep_types = {}

        fam_q_counter = Counter(q.family_id for q in questions if q.family_id is not None)
        recurring_families_count = 0
        singleton_families_count = 0
        repetition_type_counts: Dict[str, int] = {}

        for fid in family_ids_in_scope:
            rep_type = fam_rep_types.get(fid, "singleton")
            repetition_type_counts[rep_type] = repetition_type_counts.get(rep_type, 0) + 1
            q_occ = fam_q_counter.get(fid, 0)
            if rep_type in ("exact_repeat", "family_repeat", "structural_repeat", "exact", "near") or q_occ >= 2:
                recurring_families_count += 1
            else:
                singleton_families_count += 1

        repetition_type_breakdown = dict(sorted(repetition_type_counts.items()))

        # 4. Syllabus & Topic Coverage
        syl_q = db.query(Syllabus).filter(Syllabus.course_id == course.id)
        if active_track:
            # If syllabus tracks exist for this course
            has_track_syl = db.query(Syllabus).filter(
                Syllabus.course_id == course.id,
                Syllabus.track_id == active_track.id
            ).count() > 0
            if has_track_syl:
                syl_q = syl_q.filter(Syllabus.track_id == active_track.id)

        syl_ids = [s.id for s in syl_q.all()]
        if syl_ids:
            syllabus_topics = (
                db.query(Topic)
                .join(Unit, Topic.unit_id == Unit.id)
                .filter(Unit.syllabus_id.in_(syl_ids))
                .all()
            )
        else:
            syllabus_topics = []

        syllabus_topic_id_set = {t.id for t in syllabus_topics}
        observed_topic_id_set = {t_id for t_set in q_to_topics.values() for t_id in t_set}

        observed_syllabus_topics = observed_topic_id_set & syllabus_topic_id_set
        unobserved_syllabus_topics = syllabus_topic_id_set - observed_topic_id_set
        out_of_syllabus_topics = observed_topic_id_set - syllabus_topic_id_set

        unobserved_topic_names = sorted([
            t.name for t in syllabus_topics if t.id in unobserved_syllabus_topics
        ])
        topic_coverage_ratio = (
            round(len(observed_syllabus_topics) / len(syllabus_topic_id_set), 4)
            if syllabus_topic_id_set else 0.0
        )

        # 5. Track Coverage
        course_tracks_list: List[Dict[str, Any]] = []
        if course.tracks:
            for t in sorted(course.tracks, key=lambda x: x.id):
                t_exams = db.query(Exam).filter(Exam.course_id == course.id, Exam.track_id == t.id).all()
                t_e_ids = [e.id for e in t_exams]
                if t_e_ids:
                    t_q_count = (
                        db.query(func.count(Question.id))
                        .join(Section, Question.section_id == Section.id)
                        .filter(Section.exam_id.in_(t_e_ids))
                        .scalar()
                        or 0
                    )
                else:
                    t_q_count = 0
                course_tracks_list.append({
                    "track_id": t.id,
                    "track_key": t.track_key,
                    "track_name": t.track_name,
                    "track_code": t.track_code,
                    "exams_count": len(t_exams),
                    "questions_count": t_q_count,
                    "status": "OBSERVED" if len(t_exams) > 0 else "UNOBSERVED",
                })

        # 6. Ingestion & Extraction Failures
        doc_ids = sorted(list({e.document_id for e in exams if e.document_id is not None}))
        if doc_ids:
            docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        else:
            docs = []

        failed_docs = [
            {
                "document_id": d.id,
                "title": d.title,
                "extraction_status": d.extraction_status,
                "processing_status": d.processing_status,
                "year": d.year,
            }
            for d in docs
            if (d.extraction_status and d.extraction_status.lower() in ("failed", "error"))
            or (d.processing_status and d.processing_status.lower() in ("failed", "error"))
        ]

        # 7. Trust Assessment (Defensible & Deterministic)
        sufficiency = DNAAnalyzerService.determine_sufficiency(len(valid_year_exams), total_extracted)
        sufficiency_val = sufficiency.value if hasattr(sufficiency, "value") else str(sufficiency)

        # Defensible trust criteria: minimum sample size and non-zero topic coverage
        trustworthy_for_prediction = (
            sufficiency_val in ("STRONG", "MODERATE")
            and len(valid_year_exams) >= 2
            and total_extracted >= 10
            and (len(syllabus_topic_id_set) == 0 or topic_coverage_ratio > 0.0)
        )

        identified_gaps: List[str] = []
        if unknown_year_exams:
            identified_gaps.append(
                f"{len(unknown_year_exams)} examination(s) have missing/unknown years and cannot be used in temporal models"
            )
        if missing_years:
            identified_gaps.append(
                f"Missing historical examination years in sequence: {missing_years}"
            )
        if unresolved_questions_count > 0:
            identified_gaps.append(
                f"{unresolved_questions_count} extracted question(s) have no mapped syllabus topic"
            )
        if needs_review_count > 0:
            identified_gaps.append(
                f"{needs_review_count} question(s) are flagged as requiring review"
            )
        if failed_docs:
            identified_gaps.append(
                f"{len(failed_docs)} linked document(s) failed ingestion or extraction"
            )
        if sufficiency_val == "INSUFFICIENT":
            identified_gaps.append(
                "Historical exam count or question volume is insufficient for statistical confidence"
            )
        elif sufficiency_val == "LIMITED":
            identified_gaps.append(
                "Limited examination sample size (1-3 exams or <= 30 questions)"
            )
        if syllabus_topic_id_set and topic_coverage_ratio < 0.30:
            identified_gaps.append(
                f"Low syllabus coverage: only {topic_coverage_ratio:.1%} of syllabus topics are represented"
            )

        return {
            "scope": {
                "course_id": course.id,
                "course_name": course.name,
                "course_code": course.code,
                "canonical_code": course.canonical_code,
                "track": {
                    "track_id": active_track.id,
                    "track_key": active_track.track_key,
                    "track_name": active_track.track_name,
                } if active_track else None,
                "assessment_cycle": norm_cycle or "ALL",
            },
            "exams": {
                "total_exams": len(exams),
                "valid_year_exams": len(valid_year_exams),
                "unknown_year_exams": len(unknown_year_exams),
                "unknown_year_exam_ids": unknown_year_exam_ids,
                "years_observed": years_observed,
                "year_range": year_range,
                "missing_years": missing_years,
                "by_year": exams_by_year,
                "by_assessment_cycle": exams_by_cycle,
            },
            "questions": {
                "total_extracted": total_extracted,
                "classified_with_topic": classified_with_topic_count,
                "classified_with_question_type": classified_with_type_count,
                "classified_with_family": classified_with_family_count,
                "unresolved_questions": unresolved_questions_count,
                "unresolved_question_sample_ids": unresolved_q_ids[:25],
                "needs_review_count": needs_review_count,
                "unknown_year_questions": unknown_year_q_count,
            },
            "question_families": {
                "total_families": len(family_ids_in_scope),
                "recurring_families": recurring_families_count,
                "singleton_families": singleton_families_count,
                "repetition_type_breakdown": repetition_type_breakdown,
                "questions_in_families": classified_with_family_count,
                "unassigned_questions": total_extracted - classified_with_family_count,
            },
            "topics": {
                "syllabus_topics_total": len(syllabus_topic_id_set),
                "observed_topics": len(observed_syllabus_topics),
                "unobserved_topics": len(unobserved_syllabus_topics),
                "unobserved_topic_names": unobserved_topic_names[:25],
                "topic_coverage_ratio": topic_coverage_ratio,
                "out_of_syllabus_topics_observed": len(out_of_syllabus_topics),
            },
            "tracks": {
                "has_tracks": bool(course.tracks),
                "available_tracks": course_tracks_list,
                "active_track": {
                    "track_id": active_track.id,
                    "track_key": active_track.track_key,
                    "track_name": active_track.track_name,
                } if active_track else None,
            },
            "ingestion_and_extraction": {
                "documents_total": len(docs),
                "documents_failed": len(failed_docs),
                "failed_documents": failed_docs,
            },
            "trust_assessment": {
                "data_sufficiency": sufficiency_val,
                "trustworthy_for_prediction": trustworthy_for_prediction,
                "has_unknown_years": len(unknown_year_exams) > 0,
                "has_missing_years": len(missing_years) > 0,
                "has_unresolved_questions": unresolved_questions_count > 0,
                "identified_gaps": identified_gaps,
            },
        }

    @classmethod
    def get_global_health(
        cls,
        db: Session,
        assessment_cycle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate high-level corpus health across all active courses."""
        courses = db.query(Course).order_by(Course.id).all()
        course_summaries = []

        total_exams_all = 0
        valid_year_exams_all = 0
        unknown_year_exams_all = 0
        total_questions_all = 0
        total_unresolved_all = 0
        total_families_all = db.query(QuestionFamily).count()
        total_docs_failed_all = 0

        for c in courses:
            h = cls.get_course_health(db, c, assessment_cycle=assessment_cycle)
            total_exams_all += h["exams"]["total_exams"]
            valid_year_exams_all += h["exams"]["valid_year_exams"]
            unknown_year_exams_all += h["exams"]["unknown_year_exams"]
            total_questions_all += h["questions"]["total_extracted"]
            total_unresolved_all += h["questions"]["unresolved_questions"]
            total_docs_failed_all += h["ingestion_and_extraction"]["documents_failed"]

            course_summaries.append({
                "course_id": c.id,
                "name": c.name,
                "code": c.code,
                "total_exams": h["exams"]["total_exams"],
                "valid_year_exams": h["exams"]["valid_year_exams"],
                "unknown_year_exams": h["exams"]["unknown_year_exams"],
                "total_questions": h["questions"]["total_extracted"],
                "unresolved_questions": h["questions"]["unresolved_questions"],
                "topic_coverage_ratio": h["topics"]["topic_coverage_ratio"],
                "data_sufficiency": h["trust_assessment"]["data_sufficiency"],
                "trustworthy_for_prediction": h["trust_assessment"]["trustworthy_for_prediction"],
                "gaps_count": len(h["trust_assessment"]["identified_gaps"]),
            })

        return {
            "scope": {
                "assessment_cycle": assessment_cycle or "ALL",
                "total_courses": len(courses),
            },
            "totals": {
                "total_courses": len(courses),
                "total_exams": total_exams_all,
                "valid_year_exams": valid_year_exams_all,
                "unknown_year_exams": unknown_year_exams_all,
                "total_questions_extracted": total_questions_all,
                "total_unresolved_questions": total_unresolved_all,
                "total_question_families": total_families_all,
                "total_documents_failed": total_docs_failed_all,
            },
            "courses": course_summaries,
        }
