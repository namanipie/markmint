"""
Academic Analytics API endpoints for MarkMint.
Answers the central analytical question: "WHAT HAS ACTUALLY REPEATED IN THIS SUBJECT?"
Implements:
- Topic repetition metrics & paper coverage (Phase 5)
- Repeated question families & recurrence history (Phase 6)
- Exact repeat vs family repeat vs related variant breakdown (Phase 7)
- Dynamic multi-criteria filtering (Phase 10)
- Topic drilldown connecting to MintAI (Phase 11)
- Year-to-year exam evolution (Phase 12)
- Unit-level distribution (Phase 13)
- Marks analytics & weight distribution (Phase 14)
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc

from backend.core.database import get_db
from backend.models.core import (
    Course, Exam, Section, Question, Topic, Unit, Syllabus, Document,
    QuestionFamily, QuestionFamilyMembership, StudentTopicProgress, question_topic,
    CourseTrack
)
from backend.api.endpoints.predictions import _find_course, _build_historical_exam_payloads
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.prediction.context import PredictionTarget

router = APIRouter()


def _resolve_track(course: Course, language: Optional[str]) -> Optional[CourseTrack]:
    if not course or not course.tracks or not language:
        return None
    lang_clean = language.strip().lower()
    for t in course.tracks:
        if (
            t.track_key.lower() == lang_clean
            or t.track_name.lower() == lang_clean
            or (t.track_code and t.track_code.lower() == lang_clean)
        ):
            return t
    return None


@router.get("/{course_id}/overview")
def get_analytics_overview(
    course_id: str,
    language: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """High-level summary of historical exam evidence for a course."""
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    active_track = _resolve_track(course, language)
    exams_query = db.query(Exam).filter(Exam.course_id == course.id)
    if active_track:
        exams_query = exams_query.filter(Exam.track_id == active_track.id)
    exams = exams_query.all()
    total_papers = len(exams)

    questions_query = (
        db.query(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
    )
    if active_track:
        questions_query = questions_query.filter(Exam.track_id == active_track.id)
    total_questions = questions_query.count()

    years = sorted(list({e.year for e in exams if e.year is not None}))
    assessment_types = sorted(list({e.assessment_type for e in exams if e.assessment_type is not None}))

    # Top repeated topics
    topic_stats_query = (
        db.query(
            Topic.id,
            Topic.name,
            func.count(distinct(Exam.id)).label("paper_count"),
            func.count(Question.id).label("q_count"),
            func.sum(func.coalesce(Question.marks, 0.0)).label("total_marks")
        )
        .join(question_topic, Topic.id == question_topic.c.topic_id)
        .join(Question, question_topic.c.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
    )
    if active_track:
        topic_stats_query = topic_stats_query.filter(Exam.track_id == active_track.id)
    topic_stats = (
        topic_stats_query
        .group_by(Topic.id, Topic.name)
        .order_by(desc("paper_count"), desc("total_marks"))
        .limit(5)
        .all()
    )

    top_topics = [
        {
            "topic_id": t[0],
            "topic_name": t[1],
            "paper_count": t[2],
            "paper_coverage": round(t[2] / total_papers, 4) if total_papers > 0 else 0,
            "question_count": t[3],
            "total_marks": round(float(t[4] or 0), 1),
        }
        for t in topic_stats
    ]

    # Top repeated question families
    family_stats_query = (
        db.query(
            QuestionFamily.id,
            QuestionFamily.canonical_name,
            QuestionFamily.repetition_type,
            func.count(distinct(Exam.id)).label("paper_count"),
            func.count(Question.id).label("q_count")
        )
        .join(Question, QuestionFamily.id == Question.family_id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
    )
    if active_track:
        family_stats_query = family_stats_query.filter(Exam.track_id == active_track.id)
    family_stats = (
        family_stats_query
        .group_by(QuestionFamily.id, QuestionFamily.canonical_name, QuestionFamily.repetition_type)
        .order_by(desc("paper_count"), desc("q_count"))
        .limit(5)
        .all()
    )

    top_families = [
        {
            "family_id": f[0],
            "canonical_name": f[1],
            "repetition_type": f[2] or "singleton",
            "paper_count": f[3],
            "question_count": f[4],
        }
        for f in family_stats
    ]

    # Marks statistics
    marks_rows = (
        questions_query
        .filter(Question.marks != None, Question.is_alternative == False)
        .with_entities(Question.marks)
        .all()
    )
    marks_list = [m[0] for m in marks_rows if m[0] is not None]
    min_marks = min(marks_list) if marks_list else 0.0
    max_marks = max(marks_list) if marks_list else 0.0
    avg_marks = round(sum(marks_list) / len(marks_list), 2) if marks_list else 0.0

    return {
        "course_id": course.id,
        "course_name": course.name,
        "code": course.code,
        "canonical_code": course.canonical_code,
        "readiness_status": "READY" if total_papers > 0 and total_questions > 0 else "CATALOG_ONLY",
        "total_papers": total_papers,
        "total_questions": total_questions,
        "years": years,
        "time_range": f"{years[0]}-{years[-1]}" if len(years) > 1 else (str(years[0]) if years else "N/A"),
        "assessment_types": assessment_types,
        "marks_summary": {
            "min_question_marks": min_marks,
            "max_question_marks": max_marks,
            "avg_question_marks": avg_marks,
            "total_marks_analyzed": round(sum(marks_list), 1),
        },
        "top_repeated_topics": top_topics,
        "top_repeated_families": top_families,
    }


@router.get("/{course_id}/topics")
def get_topic_repetition_analytics(
    course_id: str,
    year: Optional[int] = Query(None),
    assessment_type: Optional[str] = Query(None),
    unit: Optional[int] = Query(None),
    min_marks: Optional[float] = Query(None),
    max_marks: Optional[float] = Query(None),
    language: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Factual topic repetition metrics.
    Answers: Which topics appeared most often? Which carry the highest marks?
    Which are recurring recently vs historically?
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    active_track = _resolve_track(course, language)

    # Base exams for course
    base_exams_query = db.query(Exam).filter(Exam.course_id == course.id)
    if active_track:
        base_exams_query = base_exams_query.filter(Exam.track_id == active_track.id)
    base_exams = base_exams_query.all()
    total_papers_course = len(base_exams)
    all_years = sorted(list({e.year for e in base_exams if e.year is not None}))
    max_year = max(all_years) if all_years else 0
    recent_years = {y for y in all_years if y >= max_year - 1} if max_year > 0 else set()

    # Query topics mapped to this course syllabus
    topics_query = (
        db.query(Topic, Unit.name, Unit.number)
        .join(Unit, Topic.unit_id == Unit.id)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == course.id)
    )
    if active_track:
        topics_query = topics_query.filter(Syllabus.track_id == active_track.id)
    if isinstance(unit, int):
        topics_query = topics_query.filter(Unit.number == unit)

    syllabus_topics = topics_query.all()

    # Prepare query for questions with optional filters
    q_filter = (
        db.query(
            question_topic.c.topic_id,
            Question.id.label("q_id"),
            Question.marks,
            Question.is_alternative,
            Exam.id.label("exam_id"),
            Exam.year,
            Exam.assessment_type,
        )
        .join(Question, question_topic.c.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
    )
    if active_track:
        q_filter = q_filter.filter(Exam.track_id == active_track.id)

    if isinstance(year, int):
        q_filter = q_filter.filter(Exam.year == year)
    if isinstance(assessment_type, str) and assessment_type.strip():
        q_filter = q_filter.filter(func.lower(Exam.assessment_type) == assessment_type.lower())
    if isinstance(min_marks, (int, float)):
        q_filter = q_filter.filter(Question.marks >= min_marks)
    if isinstance(max_marks, (int, float)):
        q_filter = q_filter.filter(Question.marks <= max_marks)

    question_rows = q_filter.all()

    # Aggregate by topic_id
    topic_data: Dict[int, Dict[str, Any]] = {}
    for row in question_rows:
        tid = row.topic_id
        if tid not in topic_data:
            topic_data[tid] = {
                "questions": set(),
                "exams": set(),
                "marks_non_alt": 0.0,
                "max_marks": 0.0,
                "years": set(),
                "recent_q_count": 0,
                "assessment_types": {},
            }

        td = topic_data[tid]
        td["questions"].add(row.q_id)
        td["exams"].add(row.exam_id)

        m = float(row.marks or 0.0)
        if not row.is_alternative:
            td["marks_non_alt"] += m
        if m > td["max_marks"]:
            td["max_marks"] = m

        if row.year is not None:
            td["years"].add(row.year)
            if row.year in recent_years:
                td["recent_q_count"] += 1

        atype = row.assessment_type or "UNKNOWN"
        td["assessment_types"][atype] = td["assessment_types"].get(atype, 0) + 1

    # Format result records
    results = []
    for topic_obj, unit_name, unit_num in syllabus_topics:
        tid = topic_obj.id
        stats = topic_data.get(tid)

        if stats:
            p_count = len(stats["exams"])
            q_count = len(stats["questions"])
            tot_m = round(stats["marks_non_alt"] if stats["marks_non_alt"] > 0 else stats["max_marks"], 1)
            coverage = round(p_count / total_papers_course, 4) if total_papers_course > 0 else 0.0
            avg_m = round(tot_m / p_count, 2) if p_count > 0 else 0.0
            years_seen = sorted(list(stats["years"]))
            first_seen = years_seen[0] if years_seen else None
            last_seen = years_seen[-1] if years_seen else None

            # Recurrence classification
            if last_seen and last_seen in recent_years and p_count >= 2:
                rec_status = "RECENTLY_RECURRING"
            elif p_count >= 2:
                rec_status = "HISTORICALLY_STABLE"
            elif last_seen and max_year and last_seen < max_year - 1:
                rec_status = "DORMANT"
            else:
                rec_status = "LIMITED_EVIDENCE"

            results.append({
                "topic_id": tid,
                "topic_name": topic_obj.name,
                "unit_name": unit_name,
                "unit_number": unit_num,
                "occurrence_count": q_count,
                "paper_count": p_count,
                "paper_coverage": coverage,
                "total_marks": tot_m,
                "average_marks": avg_m,
                "max_marks": stats["max_marks"],
                "first_seen_year": first_seen,
                "last_seen_year": last_seen,
                "recent_occurrence_count": stats["recent_q_count"],
                "recurrence_status": rec_status,
                "assessment_type_breakdown": stats["assessment_types"],
            })
        else:
            # If explicit filters are applied (year, assessment_type, min_marks, max_marks), skip topics with 0 matching questions
            if isinstance(year, int) or (isinstance(assessment_type, str) and assessment_type.strip()) or isinstance(min_marks, (int, float)) or isinstance(max_marks, (int, float)):
                continue

            # Topic exists in syllabus but 0 questions in historical exams
            results.append({
                "topic_id": tid,
                "topic_name": topic_obj.name,
                "unit_name": unit_name,
                "unit_number": unit_num,
                "occurrence_count": 0,
                "paper_count": 0,
                "paper_coverage": 0.0,
                "total_marks": 0.0,
                "average_marks": 0.0,
                "max_marks": 0.0,
                "first_seen_year": None,
                "last_seen_year": None,
                "recent_occurrence_count": 0,
                "recurrence_status": "NEVER_EXAMINED",
                "assessment_type_breakdown": {},
            })

    # Sort descending by paper coverage, then total marks
    results.sort(key=lambda x: (x["paper_coverage"], x["total_marks"], x["occurrence_count"]), reverse=True)

    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_papers_analyzed": total_papers_course,
        "total_topics": len(results),
        "topics_with_questions": len([r for r in results if r["paper_count"] > 0]),
        "filters_applied": {
            "year": year if isinstance(year, int) else None,
            "assessment_type": assessment_type if isinstance(assessment_type, str) and assessment_type.strip() else None,
            "unit": unit if isinstance(unit, int) else None,
            "min_marks": min_marks if isinstance(min_marks, (int, float)) else None,
            "max_marks": max_marks if isinstance(max_marks, (int, float)) else None,
            "language": language if isinstance(language, str) and language.strip() else None,
        },
        "topics": results,
    }


@router.get("/{course_id}/families")
def get_repeated_family_analytics(
    course_id: str,
    assessment_type: Optional[str] = Query(None),
    min_occurrences: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Detailed analytics for repeated question families.
    Exposes chronological appearances, marks, and actual question text.
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    exams = db.query(Exam).filter(Exam.course_id == course.id).all()
    total_papers = len(exams)
    course_exam_years = sorted(list({e.year for e in exams if e.year is not None}))
    all_span_years = list(range(course_exam_years[0], course_exam_years[-1] + 1)) if course_exam_years else []
    gap_years = [y for y in all_span_years if y not in course_exam_years]

    # Fetch all families with questions in this course
    query = (
        db.query(QuestionFamily)
        .join(Question, QuestionFamily.id == Question.family_id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
        .distinct()
    )

    families = query.all()

    results = []
    for fam in families:
        # Get questions belonging to this family in this course
        q_query = (
            db.query(Question, Exam.year, Exam.assessment_type, Exam.term)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == course.id, Question.family_id == fam.id)
        )
        if assessment_type:
            q_query = q_query.filter(func.lower(Exam.assessment_type) == assessment_type.lower())

        q_rows = q_query.order_by(Exam.year.asc().nullslast(), Question.id.asc()).all()
        if len(q_rows) < min_occurrences:
            continue

        distinct_papers = len({(r[1], r[2]) for r in q_rows if r[1] is not None})
        appearances = []
        marks_history = []
        assessments_set = set()
        years_set = set()

        for q, yr, atype, term in q_rows:
            if yr is not None:
                years_set.add(yr)
            if atype:
                assessments_set.add(atype)

            label = f"{yr or 'Unknown'} {atype or term or 'Exam'}"
            marks_val = float(q.marks or 0.0)
            marks_history.append({"label": label, "marks": marks_val, "year": yr})

            appearances.append({
                "question_id": q.id,
                "question_number": q.question_number,
                "year": yr,
                "assessment_type": atype,
                "term": term,
                "marks": marks_val,
                "is_alternative": q.is_alternative,
                "original_text": q.original_text,
                "normalized_text": q.normalized_text,
            })

        first_year = min(years_set) if years_set else fam.first_seen_year
        last_year = max(years_set) if years_set else fam.latest_seen_year

        fam_timeline = [
            {
                "year": y,
                "exam_exists": True,
                "topic_present": y in years_set,
                "family_present": y in years_set,
                "present": y in years_set,
                "status": "FAMILY_PRESENT" if (y in years_set) else "FAMILY_ABSENT",
            }
            for y in course_exam_years
        ]

        results.append({
            "family_id": fam.id,
            "canonical_name": fam.canonical_name,
            "repetition_type": fam.repetition_type or "singleton",
            "occurrence_count": len(q_rows),
            "appearances_count": len(q_rows),
            "paper_count": max(1, distinct_papers),
            "first_seen_year": first_year,
            "last_seen_year": last_year,
            "assessment_history": sorted(list(assessments_set)),
            "marks_history": marks_history,
            "appearances": appearances,
            "timeline": fam_timeline,
        })

    # Sort by occurrences descending, then paper count
    results.sort(key=lambda x: (x["occurrence_count"], x["paper_count"]), reverse=True)

    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_papers": total_papers,
        "total_families_found": len(results),
        "multi_repeat_families_count": len([f for f in results if f["occurrence_count"] >= 2]),
        "observed_years": course_exam_years,
        "unobserved_years": gap_years,
        "gap_years": gap_years,
        "families": results,
    }


@router.get("/{course_id}/families/{family_id}")
def get_family_detail_evidence(
    course_id: str,
    family_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Focused single question family evidence endpoint.
    Exposes canonical prompt, recurrence type, distinct paper count,
    chronological question appearances, exam names/years, marks, and repeat classification.
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    fam = db.query(QuestionFamily).filter(QuestionFamily.id == family_id).first()
    if not fam:
        raise HTTPException(status_code=404, detail="Question family not found")

    exams = db.query(Exam).filter(Exam.course_id == course.id).all()
    total_papers = len(exams)
    course_exam_years = sorted(list({e.year for e in exams if e.year is not None}))

    q_rows = (
        db.query(Question, Exam.year, Exam.assessment_type, Exam.term, Exam.id, Document.title, Document.original_url)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .outerjoin(Document, Exam.document_id == Document.id)
        .filter(Exam.course_id == course.id, Question.family_id == fam.id)
        .order_by(Exam.year.desc().nullslast(), Question.marks.desc().nullslast(), Question.id.asc())
        .limit(limit)
        .all()
    )

    distinct_exam_ids = {r[4] for r in q_rows if r[4] is not None}
    years_set = {r[1] for r in q_rows if r[1] is not None}
    assessments_set = {r[2] for r in q_rows if r[2]}

    non_alt_marks = [float(r[0].marks) for r in q_rows if not r[0].is_alternative and r[0].marks is not None]
    avg_marks = round(sum(non_alt_marks) / len(non_alt_marks), 2) if non_alt_marks else None
    tot_marks = round(sum(non_alt_marks), 2) if non_alt_marks else None

    appearances = []
    for q, yr, atype, term, exam_id, doc_title, doc_url in q_rows:
        membership = q.memberships[0] if getattr(q, "memberships", None) else None
        m_type = membership.match_type if membership else (fam.repetition_type or "singleton")
        appearances.append({
            "question_id": q.id,
            "question_number": q.question_number,
            "year": yr,
            "assessment_type": atype,
            "term": term,
            "exam_id": exam_id,
            "marks": float(q.marks) if q.marks is not None else None,
            "is_alternative": q.is_alternative,
            "original_text": q.original_text,
            "normalized_text": q.normalized_text,
            "repetition_type": m_type,
            "source_document_title": doc_title,
            "source_document_url": doc_url,
        })

    fam_timeline = [
        {
            "year": y,
            "exam_exists": True,
            "topic_present": False,
            "family_present": y in years_set,
            "present": y in years_set,
            "status": "FAMILY_PRESENT" if (y in years_set) else "FAMILY_ABSENT",
        }
        for y in course_exam_years
    ]

    return {
        "course_id": course.id,
        "course_name": course.name,
        "family_id": fam.id,
        "canonical_name": fam.canonical_name,
        "repetition_type": fam.repetition_type or "singleton",
        "occurrence_count": len(q_rows),
        "distinct_paper_count": len(distinct_exam_ids),
        "total_papers_analyzed": total_papers,
        "paper_coverage": round(len(distinct_exam_ids) / total_papers, 4) if total_papers > 0 else 0.0,
        "first_seen_year": min(years_set) if years_set else fam.first_seen_year,
        "last_seen_year": max(years_set) if years_set else fam.latest_seen_year,
        "observed_years": sorted(list(years_set)),
        "assessment_history": sorted(list(assessments_set)),
        "average_marks": avg_marks,
        "total_marks_observed": tot_marks,
        "appearances": appearances,
        "timeline": fam_timeline,
    }


@router.get("/{course_id}/questions/repeated")
def get_repeated_questions_breakdown(
    course_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Distinguishes:
    1. EXACT_REPEAT: questions sharing identical normalized text across exams
    2. FAMILY_REPEAT: questions grouped by QuestionFamily with near-clone or parameter variations
    3. RELATED_VARIANT: questions mapped to identical concept/topic pairs
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    questions = (
        db.query(Question, Exam.year, Exam.assessment_type)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
        .order_by(Exam.year.asc().nullslast(), Question.id.asc())
        .all()
    )

    # 1. Exact repeat detection via normalized_text
    norm_groups: Dict[str, List[Any]] = {}
    for q, yr, atype in questions:
        if q.normalized_text and len(q.normalized_text.strip()) > 15:
            norm_key = q.normalized_text.strip().lower()
            norm_groups.setdefault(norm_key, []).append((q, yr, atype))

    exact_repeats = []
    for norm_key, q_list in norm_groups.items():
        if len(q_list) >= 2:
            years = sorted(list({r[1] for r in q_list if r[1] is not None}))
            q_items = [
                {
                    "id": q[0].id,
                    "question_number": q[0].question_number,
                    "year": q[1],
                    "assessment_type": q[2],
                    "marks": q[0].marks,
                    "original_text": q[0].original_text,
                }
                for q in q_list
            ]
            exact_repeats.append({
                "type": "EXACT_REPEAT",
                "repetition_type": "EXACT_REPEAT",
                "repeat_count": len(q_list),
                "years": years,
                "canonical_text": q_list[0][0].original_text,
                "questions": q_items,
                "instances": q_items,
            })

    # 2. Family repeat detection
    fam_groups: Dict[int, List[Any]] = {}
    for q, yr, atype in questions:
        if q.family_id is not None:
            fam_groups.setdefault(q.family_id, []).append((q, yr, atype))

    family_repeats = []
    for fam_id, q_list in fam_groups.items():
        if len(q_list) >= 2:
            q_list = sorted(q_list, key=lambda r: (r[1] or 9999, r[0].id))
            family_obj = db.query(QuestionFamily).filter(QuestionFamily.id == fam_id).first()
            years = sorted(list({r[1] for r in q_list if r[1] is not None}))
            fam_items = [
                {
                    "id": q[0].id,
                    "question_number": q[0].question_number,
                    "year": q[1],
                    "assessment_type": q[2],
                    "marks": q[0].marks,
                    "original_text": q[0].original_text,
                }
                for q in q_list
            ]
            family_repeats.append({
                "type": "FAMILY_REPEAT",
                "repetition_type": "FAMILY_REPEAT",
                "family_id": fam_id,
                "family_name": family_obj.canonical_name if family_obj else f"Family #{fam_id}",
                "sub_type": family_obj.repetition_type if family_obj else "near_clone",
                "repeat_count": len(q_list),
                "years": years,
                "questions": fam_items,
                "variants": fam_items,
            })

    exact_repeats.sort(key=lambda x: x["repeat_count"], reverse=True)
    family_repeats.sort(key=lambda x: x["repeat_count"], reverse=True)

    return {
        "course_id": course.id,
        "course_name": course.name,
        "exact_repeats_count": len(exact_repeats),
        "family_repeats_count": len(family_repeats),
        "exact_repeats": exact_repeats,
        "family_repeats": family_repeats,
    }


@router.get("/{course_id}/evolution")
@router.get("/{course_id}/exam-evolution")
def get_exam_evolution(
    course_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Timeline showing how examination topics and marks change across academic years.
    Identifies newly introduced vs discontinued curriculum areas.
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    exams = (
        db.query(Exam)
        .filter(Exam.course_id == course.id, Exam.year != None)
        .order_by(Exam.year.asc())
        .all()
    )

    years_map: Dict[int, List[Exam]] = {}
    for e in exams:
        years_map.setdefault(e.year, []).append(e)

    sorted_years = sorted(years_map.keys())
    seen_topics_before: set = set()
    evolution_timeline = []

    for yr in sorted_years:
        yr_exams = years_map[yr]
        exam_ids = [e.id for e in yr_exams]
        atypes = sorted(list({e.assessment_type for e in yr_exams if e.assessment_type}))

        # Query topics for this year's exams
        topic_rows = (
            db.query(
                Topic.name,
                func.count(Question.id),
                func.sum(func.coalesce(Question.marks, 0.0))
            )
            .join(question_topic, Topic.id == question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .filter(Section.exam_id.in_(exam_ids), Question.is_alternative == False)
            .group_by(Topic.name)
            .order_by(desc(func.sum(func.coalesce(Question.marks, 0.0))))
            .all()
        )

        current_topics_set = {r[0] for r in topic_rows}
        new_topics = [t for t in current_topics_set if t not in seen_topics_before]
        discontinued_topics = [t for t in seen_topics_before if t not in current_topics_set]

        total_marks_yr = sum(float(r[2] or 0.0) for r in topic_rows)
        total_questions_yr = sum(r[1] for r in topic_rows)

        topic_breakdown = [
            {
                "name": r[0],
                "question_count": r[1],
                "marks": round(float(r[2] or 0.0), 1),
                "is_new": r[0] in new_topics,
            }
            for r in topic_rows
        ]

        evolution_timeline.append({
            "year": yr,
            "exam_exists": True,
            "gap": False,
            "papers_count": len(yr_exams),
            "paper_count": len(yr_exams),
            "assessment_types": atypes,
            "total_questions": total_questions_yr,
            "total_marks": round(total_marks_yr, 1),
            "topics": topic_breakdown,
            "active_topics": topic_breakdown,
            "new_topics_introduced": new_topics,
            "discontinued_topics": discontinued_topics if seen_topics_before else [],
        })

        seen_topics_before.update(current_topics_set)

    all_span_years = list(range(sorted_years[0], sorted_years[-1] + 1)) if sorted_years else []
    unobserved_years = [y for y in all_span_years if y not in sorted_years]

    gap_entries = [
        {
            "year": y,
            "exam_exists": False,
            "gap": True,
            "status": "NO_EXAM_RECORDED",
            "papers_count": 0,
            "paper_count": 0,
            "assessment_types": [],
            "total_questions": 0,
            "total_marks": 0.0,
            "topics": [],
            "active_topics": [],
            "new_topics_introduced": [],
            "discontinued_topics": [],
            "description": f"No verified examination papers archived for {course.name} in {y}.",
        }
        for y in unobserved_years
    ]

    return {
        "course_id": course.id,
        "course_name": course.name,
        "timeline_years": sorted_years,
        "observed_years": sorted_years,
        "unobserved_years": unobserved_years,
        "gap_years": unobserved_years,
        "gap_entries": gap_entries,
        "timeline": evolution_timeline,
    }


@router.get("/{course_id}/marks")
def get_marks_analytics(
    course_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Factual marks weight and question distribution analysis.
    Preserves alternative-question rules (excludes duplicates).
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    questions = (
        db.query(Question, Exam.assessment_type)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id, Question.marks != None, Question.is_alternative == False)
        .all()
    )

    if not questions:
        return {
            "course_id": course.id,
            "course_name": course.name,
            "total_questions_analyzed": 0,
            "total_marks": 0.0,
            "common_marks": [],
            "marks_by_assessment_type": {},
            "topic_mark_shares": [],
        }

    total_marks = sum(float(q[0].marks or 0.0) for q in questions)
    total_q = len(questions)

    # 1. Common marks buckets
    mark_counts: Dict[float, int] = {}
    for q, _ in questions:
        m = float(q.marks)
        mark_counts[m] = mark_counts.get(m, 0) + 1

    common_marks = [
        {
            "marks": m,
            "question_count": cnt,
            "percentage_of_questions": round((cnt / total_q) * 100, 1),
            "cumulative_marks": round(m * cnt, 1),
        }
        for m, cnt in sorted(mark_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # 2. Marks by assessment type
    by_atype: Dict[str, Dict[str, Any]] = {}
    for q, atype in questions:
        at_key = atype or "UNKNOWN"
        if at_key not in by_atype:
            by_atype[at_key] = {"question_count": 0, "total_marks": 0.0}
        by_atype[at_key]["question_count"] += 1
        by_atype[at_key]["total_marks"] += float(q.marks)

    marks_by_assessment = {
        k: {
            "question_count": v["question_count"],
            "total_marks": round(v["total_marks"], 1),
            "avg_marks_per_question": round(v["total_marks"] / v["question_count"], 2) if v["question_count"] > 0 else 0.0
        }
        for k, v in by_atype.items()
    }

    # 3. Topic mark shares
    topic_marks_rows = (
        db.query(
            Topic.id,
            Topic.name,
            func.sum(Question.marks),
            func.count(Question.id)
        )
        .join(question_topic, Topic.id == question_topic.c.topic_id)
        .join(Question, question_topic.c.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id, Question.marks != None, Question.is_alternative == False)
        .group_by(Topic.id, Topic.name)
        .order_by(desc(func.sum(Question.marks)))
        .all()
    )

    topic_mark_shares = [
        {
            "topic_id": r[0],
            "topic_name": r[1],
            "total_marks": round(float(r[2] or 0.0), 1),
            "question_count": r[3],
            "mark_share_percentage": round((float(r[2] or 0.0) / total_marks) * 100, 1) if total_marks > 0 else 0.0,
        }
        for r in topic_marks_rows
    ]

    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_questions_analyzed": total_q,
        "total_marks": round(total_marks, 1),
        "avg_question_marks": round(total_marks / total_q, 2) if total_q > 0 else 0.0,
        "common_marks": common_marks,
        "marks_by_assessment_type": marks_by_assessment,
        "topic_mark_shares": topic_mark_shares,
    }


@router.get("/{course_id}/assessment-comparison")
def get_assessment_comparison(
    course_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Compares topic appearance and mark density across assessment types
    (e.g., CT1, CT2, END_SEM). Normalizes by paper count to handle unequal sample sizes.
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    exams = db.query(Exam).filter(Exam.course_id == course.id).all()
    if not exams:
        return {
            "course_id": course.id,
            "course_name": course.name,
            "assessment_types": [],
            "topics": []
        }

    # Group papers by assessment type
    papers_by_at: Dict[str, List[int]] = {}
    for e in exams:
        at_key = (e.assessment_type or "UNKNOWN").upper()
        papers_by_at.setdefault(at_key, []).append(e.id)

    # Syllabus topics
    syllabus_topics = (
        db.query(Topic, Unit.name, Unit.number)
        .join(Unit, Topic.unit_id == Unit.id)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == course.id)
        .all()
    )

    # Questions per topic and exam
    q_rows = (
        db.query(
            question_topic.c.topic_id,
            Exam.id.label("exam_id"),
            Exam.assessment_type,
            Question.marks,
            Question.is_alternative
        )
        .join(Question, question_topic.c.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Exam.course_id == course.id)
        .all()
    )

    topic_at_data: Dict[int, Dict[str, Dict[str, Any]]] = {}
    for row in q_rows:
        tid = row.topic_id
        at_key = (row.assessment_type or "UNKNOWN").upper()
        if tid not in topic_at_data:
            topic_at_data[tid] = {}
        if at_key not in topic_at_data[tid]:
            topic_at_data[tid][at_key] = {"exams": set(), "marks": 0.0, "q_count": 0}
        
        entry = topic_at_data[tid][at_key]
        entry["exams"].add(row.exam_id)
        entry["q_count"] += 1
        if not row.is_alternative:
            entry["marks"] += float(row.marks or 0.0)

    comparison_results = []
    at_names = sorted(papers_by_at.keys())

    for t_obj, u_name, u_num in syllabus_topics:
        tid = t_obj.id
        t_data = topic_at_data.get(tid, {})

        breakdown = {}
        frequencies = {}
        for at in at_names:
            at_papers_total = len(papers_by_at[at])
            at_data = t_data.get(at, {"exams": set(), "marks": 0.0, "q_count": 0})
            papers_present = len(at_data["exams"])
            freq = round(papers_present / at_papers_total, 3) if at_papers_total > 0 else 0.0
            frequencies[at] = freq
            breakdown[at] = {
                "papers_present": papers_present,
                "total_papers": at_papers_total,
                "paper_frequency": freq,
                "question_count": at_data["q_count"],
                "total_marks": round(at_data["marks"], 1)
            }

        # Determine bias
        ct_freq = max([frequencies.get(k, 0.0) for k in frequencies if "CT" in k] or [0.0])
        end_freq = frequencies.get("END_SEM", 0.0)

        if ct_freq >= 0.4 and end_freq < 0.2:
            bias = "CLASS_TEST_LEANING"
        elif end_freq >= 0.4 and ct_freq < 0.2:
            bias = "END_SEM_LEANING"
        elif ct_freq >= 0.3 and end_freq >= 0.3:
            bias = "UNIVERSAL"
        elif any(f > 0 for f in frequencies.values()):
            bias = "BALANCED"
        else:
            bias = "UNEXAMINED"

        comparison_results.append({
            "topic_id": tid,
            "topic_name": t_obj.name,
            "unit_name": u_name,
            "unit_number": u_num,
            "assessment_breakdown": breakdown,
            "bias": bias,
            "is_universal": bias == "UNIVERSAL",
        })

    comparison_results.sort(
        key=lambda x: max([b["paper_frequency"] for b in x["assessment_breakdown"].values()] or [0.0]),
        reverse=True
    )

    return {
        "course_id": course.id,
        "course_name": course.name,
        "assessment_types": [
            {"type": at, "paper_count": len(papers_by_at[at])}
            for at in at_names
        ],
        "total_papers": len(exams),
        "topics": comparison_results
    }


@router.get("/{course_id}/topics/{topic_id}/intelligence")
def get_topic_intelligence(
    course_id: str,
    topic_id: str,
    student_id: Optional[str] = Query("default_student"),
    language: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Comprehensive Topic Intelligence drilldown linking:
    - Syllabus unit and context
    - Historical occurrence, distinct paper coverage, and marks weight
    - Question families and exact repeat member questions with LaTeX math
    - MintAI forecast (probability, confidence, rationale)
    - Student personalization (mastery status, practice stats, action) with strict isolation
    """
    course = _find_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    active_track = _resolve_track(course, language)

    topic_query = (
        db.query(Topic, Unit.name, Unit.number)
        .join(Unit, Topic.unit_id == Unit.id)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == course.id)
    )
    if active_track:
        topic_query = topic_query.filter(Syllabus.track_id == active_track.id)
    if str(topic_id).isdigit():
        topic = topic_query.filter(Topic.id == int(topic_id)).first()
    else:
        topic = topic_query.filter(func.lower(Topic.name) == str(topic_id).lower()).first()

    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found in course syllabus")

    topic_obj, unit_name, unit_number = topic

    # All course exams
    exams_query = db.query(Exam).filter(Exam.course_id == course.id)
    if active_track:
        exams_query = exams_query.filter(Exam.track_id == active_track.id)
    all_exams = exams_query.all()
    total_papers = len(all_exams)
    papers_with_qs = [
        e for e in all_exams 
        if db.query(Question).join(Section).filter(Section.exam_id == e.id).count() > 0
    ]
    total_active_papers = len(papers_with_qs) if papers_with_qs else total_papers

    # Questions for this topic
    q_rows_query = (
        db.query(
            Question,
            Exam.id.label("exam_id"),
            Exam.year,
            Exam.assessment_type,
            Exam.term
        )
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .join(question_topic, question_topic.c.question_id == Question.id)
        .filter(Exam.course_id == course.id, question_topic.c.topic_id == topic_obj.id)
    )
    if active_track:
        q_rows_query = q_rows_query.filter(Exam.track_id == active_track.id)
    q_rows = (
        q_rows_query
        .order_by(Exam.year.desc().nullslast(), Question.id.desc())
        .all()
    )

    distinct_exam_ids = {r.exam_id for r in q_rows}
    paper_count = len(distinct_exam_ids)
    paper_coverage = round(paper_count / total_active_papers, 4) if total_active_papers > 0 else 0.0

    # Marks statistics
    non_alt_marks = [float(r[0].marks or 0.0) for r in q_rows if not r[0].is_alternative and r[0].marks is not None]
    total_marks = round(sum(non_alt_marks), 1)
    avg_marks = round(total_marks / paper_count, 2) if paper_count > 0 else 0.0
    max_marks = max([float(r[0].marks or 0.0) for r in q_rows if r[0].marks is not None] or [0.0])

    years_seen = sorted(list({r.year for r in q_rows if r.year is not None}))
    first_seen = years_seen[0] if years_seen else None
    last_seen = years_seen[-1] if years_seen else None

    # Assessment distribution
    at_counts: Dict[str, int] = {}
    for r in q_rows:
        at_key = r.assessment_type or "UNKNOWN"
        at_counts[at_key] = at_counts.get(at_key, 0) + 1

    # Question families for this topic
    family_ids = {r[0].family_id for r in q_rows if r[0].family_id is not None}
    families_list = []
    if family_ids:
        fams = db.query(QuestionFamily).filter(QuestionFamily.id.in_(family_ids)).all()
        for f in fams:
            fam_qs = [r for r in q_rows if r[0].family_id == f.id]
            families_list.append({
                "family_id": f.id,
                "canonical_name": f.canonical_name,
                "repetition_type": f.repetition_type or "singleton",
                "question_count": len(fam_qs),
                "years": sorted(list({r.year for r in fam_qs if r.year is not None}))
            })

    # Detailed past questions
    past_questions = [
        {
            "id": r[0].id,
            "question_number": r[0].question_number,
            "year": r.year,
            "assessment_type": r.assessment_type or r.term or "UNKNOWN",
            "marks": float(r[0].marks) if r[0].marks is not None else None,
            "is_alternative": r[0].is_alternative,
            "original_text": r[0].original_text,
            "difficulty": r[0].difficulty,
            "family_id": r[0].family_id,
            "family_name": r[0].family.canonical_name if r[0].family else None,
            "repeat_type": (
                "EXACT_REPEAT" if (r[0].family and r[0].family.repetition_type == "exact_repeat")
                else ("FAMILY_REPEAT" if (r[0].family and r[0].family.repetition_type == "family_repeat")
                else "SINGLETON")
            )
        }
        for r in q_rows
    ]

    # MintAI Forecast calculation via DNA + Model
    hist_exams_query = (
        db.query(Exam)
        .filter(Exam.course_id == course.id, Exam.year != None)
    )
    if active_track:
        hist_exams_query = hist_exams_query.filter(Exam.track_id == active_track.id)
    hist_exams = hist_exams_query.order_by(Exam.year.asc()).all()
    hist_payloads = _build_historical_exam_payloads(hist_exams)
    analyzer = DNAAnalyzerService()
    dna = analyzer.analyze(hist_payloads)
    engine = ExamScopeCombinedModel(dna)
    topic_preds = engine.predict(PredictionTarget.TOPIC)
    
    match_pred = next((p for p in topic_preds if p.name == topic_obj.name), None)
    if match_pred:
        forecast_prob = round(match_pred.probability * 100, 1)
        forecast_conf = match_pred.confidence
        reason_codes = match_pred.reason_codes or ["HISTORICAL_RECURRENCE"]
        rationale = match_pred.explanation or f"Appears in {paper_count} of {total_active_papers} analyzed papers ({round(paper_coverage * 100, 1)}% coverage)."
    else:
        forecast_prob = round(min(95.0, max(10.0, paper_coverage * 100)), 1)
        forecast_conf = "HIGH" if paper_count >= 4 else ("MEDIUM" if paper_count >= 2 else "LOW")
        reason_codes = ["EMPIRICAL_FREQUENCY"] if paper_count > 0 else ["UNEXAMINED_IN_SAMPLE"]
        rationale = f"Observed in {paper_count} of {total_active_papers} past examination papers."

    # Student progress & priority isolation
    progress = (
        db.query(StudentTopicProgress)
        .filter(
            StudentTopicProgress.student_id == student_id,
            StudentTopicProgress.topic_id == topic_obj.id
        )
        .first()
    )
    status = progress.status if progress else "NOT_STARTED"
    practice_attempted = progress.practice_attempted if progress else 0
    practice_correct = progress.practice_correct if progress else 0

    # Calculate personalized priority: priority = probability * need factor
    need_factor = 0.2 if status == "MASTERED" else (0.6 if status == "IN_PROGRESS" else 1.0)
    priority_score = round((forecast_prob / 100.0) * need_factor * 100, 1)

    if status == "MASTERED":
        recommended_action = "Topic mastered! Do a quick formula review 2 days before the exam."
    elif status == "IN_PROGRESS":
        recommended_action = f"Practiced {practice_attempted} problems. Solve 2 more high-mark past questions to achieve full mastery."
    elif forecast_prob >= 65:
        recommended_action = "CRITICAL HIGH YIELD: High exam probability. Solve the recurring question families below first."
    else:
        recommended_action = "Recommended: Review key definitions and formulas from the syllabus unit."

    course_exam_years = sorted(list({e.year for e in all_exams if e.year is not None}))
    all_span_years = list(range(course_exam_years[0], course_exam_years[-1] + 1)) if course_exam_years else []
    gap_years = [y for y in all_span_years if y not in course_exam_years]

    topic_timeline = [
        {
            "year": y,
            "exam_exists": True,
            "topic_present": y in years_seen,
            "family_present": any(y in (f.get("years") or []) for f in families_list),
            "present": y in years_seen,
            "status": "TOPIC_PRESENT" if (y in years_seen) else "TOPIC_ABSENT",
        }
        for y in course_exam_years
    ]

    return {
        "course_id": course.id,
        "course_name": course.name,
        "topic_id": topic_obj.id,
        "topic_name": topic_obj.name,
        "unit": {
            "name": unit_name,
            "number": unit_number,
        },
        "repetition_metrics": {
            "paper_count": paper_count,
            "total_papers": total_active_papers,
            "paper_coverage": paper_coverage,
            "question_count": len(q_rows),
            "total_marks": total_marks,
            "average_marks": avg_marks,
            "max_marks": max_marks,
            "first_seen_year": first_seen,
            "last_seen_year": last_seen,
            "assessment_distribution": at_counts,
            "timeline": topic_timeline,
            "observed_years": course_exam_years,
            "unobserved_years": gap_years,
            "gap_years": gap_years,
        },
        "timeline": topic_timeline,
        "observed_years": course_exam_years,
        "unobserved_years": gap_years,
        "gap_years": gap_years,
        "question_families": families_list,
        "past_questions": past_questions,
        "forecast": {
            "probability": forecast_prob,
            "confidence": forecast_conf,
            "reason_codes": reason_codes,
            "rationale": rationale,
            "historical_years": years_seen,
        },
        "personalization": {
            "student_id": student_id,
            "status": status,
            "practice_attempted": practice_attempted,
            "practice_correct": practice_correct,
            "priority_score": priority_score,
            "recommended_action": recommended_action,
        }
    }
