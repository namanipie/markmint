import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from backend.core.database import SessionLocal, get_db
from backend.models.core import Course, Exam, Section, Question, QuestionFamily, Topic, question_topic
from backend.services.assessment_cycle import normalize_assessment_cycle, filter_exams_by_cycle
from backend.api.endpoints.predictions import _find_course

router = APIRouter()


class PracticeQuestionItem(BaseModel):
    id: int
    question_number: str
    text: str
    marks: Optional[float] = None
    year: Optional[int] = None
    difficulty: Optional[float] = None
    cognitive_level: Optional[str] = None


class PredictionPracticeResponse(BaseModel):
    family_id: int
    family_name: str
    repetition_type: Optional[str] = None
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    assessment_cycle: str = "ALL"
    canonical_topic: Optional[str] = None
    questions: List[PracticeQuestionItem] = []


@router.get("/practice/from-prediction/{family_id}", response_model=PredictionPracticeResponse)
def get_practice_from_prediction(
    family_id: int,
    course_id: Optional[str] = Query(None),
    assessment_cycle: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve verified historical practice questions belonging to a Question Family.
    Preserves course, language-track, and assessment-cycle isolation.
    """
    # 1. Verify QuestionFamily exists
    family = db.query(QuestionFamily).filter(QuestionFamily.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Question family not found")

    # 2. Resolve course if course_id is supplied, or fallback to family.subject
    course = None
    if course_id:
        course = _find_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
    elif family.subject:
        course = _find_course(db, family.subject)

    # 3. Track resolution for multi-track courses
    active_track = None
    if course and course.tracks and language:
        lang_low = language.strip().lower()
        active_track = next(
            (t for t in course.tracks if t.track_key.lower() == lang_low or t.track_name.lower() == lang_low or str(t.id) == lang_low),
            None
        )
        if not active_track:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language track '{language}'. Available: {[t.track_key for t in course.tracks]}"
            )

    # 4. Assessment cycle normalization
    norm_cycle = normalize_assessment_cycle(assessment_cycle)

    # 5. Build query: official historical exam questions only
    query = (
        db.query(Question, Exam.year)
        .select_from(Question)
        .options(selectinload(Question.topics))
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .filter(Question.family_id == family.id)
    )

    if course:
        query = query.filter(Exam.course_id == course.id)

    if active_track:
        query = query.filter(Exam.track_id == active_track.id)

    if norm_cycle and norm_cycle != "ALL":
        query = filter_exams_by_cycle(query, Exam.assessment_type, norm_cycle, course_id=course.id if course else None)

    # 6. Deterministic ordering: latest year first, highest marks, stable question id
    query = query.order_by(Exam.year.desc().nullslast(), Question.marks.desc().nullslast(), Question.id.asc())

    if limit is not None and limit > 0:
        query = query.limit(limit)

    results = query.all()

    # 7. Format questions and aggregate topics for canonical topic resolution
    formatted_questions: List[PracticeQuestionItem] = []
    topic_counts: Dict[str, int] = {}

    for q, year in results:
        formatted_questions.append(
            PracticeQuestionItem(
                id=q.id,
                question_number=q.question_number,
                text=q.original_text,
                marks=q.marks,
                year=year,
                difficulty=q.difficulty,
                cognitive_level=q.cognitive_level,
            )
        )
        for t in q.topics:
            if t.name:
                topic_counts[t.name] = topic_counts.get(t.name, 0) + 1

    # 8. Resolve canonical topic
    canonical_topic = None
    if topic_counts:
        # Deterministic: highest frequency, then alphabetical name
        canonical_topic = sorted(topic_counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
    elif course:
        # If the limited result set had no topic mappings, check all family questions for this course
        fallback_topics = (
            db.query(Topic.name)
            .join(question_topic, Topic.id == question_topic.c.topic_id)
            .join(Question, Question.id == question_topic.c.question_id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Question.family_id == family.id, Exam.course_id == course.id)
            .all()
        )
        if fallback_topics:
            fb_counts: Dict[str, int] = {}
            for t_row in fallback_topics:
                if t_row[0]:
                    fb_counts[t_row[0]] = fb_counts.get(t_row[0], 0) + 1
            if fb_counts:
                canonical_topic = sorted(fb_counts.items(), key=lambda x: (-x[1], x[0]))[0][0]

    # Resolve course info for response
    resolved_course_id = course.id if course else (results[0][0].section.exam.course_id if results and results[0][0].section and results[0][0].section.exam else None)
    resolved_course_name = course.name if course else (results[0][0].section.exam.course.name if results and results[0][0].section and results[0][0].section.exam and results[0][0].section.exam.course else family.subject)

    return PredictionPracticeResponse(
        family_id=family.id,
        family_name=family.canonical_name,
        repetition_type=family.repetition_type,
        course_id=resolved_course_id,
        course_name=resolved_course_name,
        assessment_cycle=norm_cycle or "ALL",
        canonical_topic=canonical_topic,
        questions=formatted_questions,
    )


@router.get("/practice/{subject}")
def get_practice_questions(
    subject: str,
    limit: int = 20,
    assessment_cycle: Optional[str] = Query(None),
    language: Optional[str] = Query(None)
):
    db = SessionLocal()
    try:
        from backend.api.endpoints.predictions import _find_course
        course = _find_course(db, subject)
        if not course:
            raise HTTPException(status_code=404, detail="Subject not found")

        active_track = None
        if course and course.tracks:
            if not (isinstance(language, str) and language.strip()):
                raise HTTPException(
                    status_code=400,
                    detail="TRACK_SELECTION_REQUIRED: Language selection is required for Foreign Languages."
                )
            lang_low = language.strip().lower()
            active_track = next(
                (t for t in course.tracks if t.track_key.lower() == lang_low or t.track_name.lower() == lang_low or str(t.id) == lang_low),
                None
            )
            if not active_track:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid language track '{language}'. Available: {[t.track_key for t in course.tracks]}"
                )

        norm_cycle = normalize_assessment_cycle(assessment_cycle)

        # Fetch recent historical questions
        query = (
            db.query(Question, Exam.year)
            .select_from(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == course.id)
        )
        if active_track:
            query = query.filter(Exam.track_id == active_track.id)

        scope = None
        if norm_cycle and norm_cycle != "ALL":
            from backend.services.assessment_plan_registry import get_course_assessment_scope
            scope = get_course_assessment_scope(
                course.id,
                norm_cycle,
                db=db,
                track_id=active_track.id if active_track else None
            )
            query = filter_exams_by_cycle(query, Exam.assessment_type, norm_cycle, course_id=course.id)

        questions = (
            query
            .order_by(Exam.year.desc().nullslast(), Question.id.asc())
            .limit(limit)
            .all()
        )

        formatted_questions = []
        for q, year in questions:
            formatted_questions.append({
                "id": q.id,
                "text": q.original_text,
                "year": year,
                "marks": q.marks,
                "family": q.family.canonical_name if q.family else None
            })

        return {
            "subject": subject,
            "assessment_cycle": norm_cycle or "ALL",
            "assessment_component": scope.component_code if scope else (norm_cycle or "ALL"),
            "assessment_label": scope.component_label if scope else (norm_cycle or "All Assessments"),
            "evidence_status": scope.evidence_status if scope else "ALL_SCOPE",
            "intended_scope": scope.intended_scope if scope else None,
            "observed_scope": scope.observed_scope if scope else None,
            "assessment_scope": {
                "student_cycle": norm_cycle or "ALL",
                "component_code": scope.component_code,
                "component_label": scope.component_label,
                "student_label": scope.student_label,
                "role": scope.role,
                "marks": scope.marks,
                "evidence_status": scope.evidence_status,
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "unit_numbers": sorted(list(scope.in_scope_unit_numbers)),
            } if scope else None,
            "questions": formatted_questions
        }
    finally:
        db.close()


@router.get("/practice/topic-questions")
def get_topic_historical_questions(
    topic_name: str = Query(..., description="Name of the syllabus topic"),
    course_id: Optional[int] = Query(None, description="Course ID filter"),
    course_code: Optional[str] = Query(None, description="Course code filter"),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve verified authentic past examination questions mapped to a specific syllabus topic.
    Returns provenance including exam year, assessment term, marks, and question family repetition type.
    """
    from sqlalchemy import func
    from backend.api.endpoints.predictions import _find_course

    query = (
        db.query(Question, Exam, Section, QuestionFamily)
        .select_from(Question)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .outerjoin(QuestionFamily, Question.family_id == QuestionFamily.id)
        .join(question_topic, Question.id == question_topic.c.question_id)
        .join(Topic, question_topic.c.topic_id == Topic.id)
        .filter(func.lower(Topic.name) == topic_name.strip().lower())
    )

    if course_id:
        query = query.filter(Exam.course_id == course_id)
    elif course_code:
        course = _find_course(db, course_code)
        if course:
            query = query.filter(Exam.course_id == course.id)

    results = (
        query
        .order_by(
            Exam.year.desc().nullslast(),
            Question.marks.desc().nullslast(),
            Question.id.asc()
        )
        .limit(limit)
        .all()
    )

    items = []
    for q, exam, sec, fam in results:
        items.append({
            "id": q.id,
            "question_number": q.question_number,
            "original_text": q.original_text,
            "marks": q.marks,
            "year": exam.year,
            "term": exam.term,
            "assessment_type": exam.assessment_type,
            "section_name": sec.name,
            "family_id": fam.id if fam else None,
            "family_name": fam.canonical_name if fam else None,
            "repetition_type": fam.repetition_type if fam else "singleton",
            "difficulty": q.difficulty,
            "cognitive_level": q.cognitive_level
        })

    return {
        "topic": topic_name,
        "total_questions": len(items),
        "questions": items
    }


CT_QUESTIONS_PATH = Path(__file__).resolve().parents[3] / "data" / "extracted_cycle_test_questions.json"
_ct_questions_cache = None

def _load_ct_questions(force_reload: bool = False):
    global _ct_questions_cache
    if (_ct_questions_cache is None or force_reload) and CT_QUESTIONS_PATH.exists():
        try:
            with open(CT_QUESTIONS_PATH, "r", encoding="utf-8") as f:
                _ct_questions_cache = json.load(f)
        except Exception:
            _ct_questions_cache = []
    return _ct_questions_cache or []


@router.get("/practice/cycle-tests/{subject}")
def get_cycle_test_questions(
    subject: str,
    cycle: Optional[str] = Query(None),
    category: Optional[str] = Query("all", description="all | descriptive | mcq"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Retrieve authentic past Cycle Test questions extracted directly from SRMIST CT papers.
    Supports filtering by subject name/slug (or 'ALL' for universal archive), assessment cycle,
    and question category (all | descriptive | mcq) to ensure MCQs and normal questions
    are never mixed up.
    """
    all_qs = _load_ct_questions()
    s_clean = re.sub(r"[^a-z0-9]+", " ", subject.lower()).strip()
    is_universal = s_clean in ["all", "any", "all subjects", "universal", "*"]

    matched_for_cycle = []
    for q in all_qs:
        q_subj = re.sub(r"[^a-z0-9]+", " ", q.get("subject", "").lower()).strip()
        if is_universal or s_clean in q_subj or q_subj in s_clean:
            if cycle and cycle.upper() != "ALL":
                c_up = cycle.upper()
                q_cyc = q.get("cycle", "CT").upper()
                if c_up not in q_cyc and q_cyc != "CT":
                    continue
            matched_for_cycle.append(q)

    # Calculate overall counts before category filter
    total_mcqs = sum(1 for q in matched_for_cycle if q.get("is_mcq") is True or q.get("q_type") == "MCQ")
    total_descriptive = len(matched_for_cycle) - total_mcqs

    cat_clean = (category or "all").lower().strip()
    if cat_clean == "mcq":
        matched = [q for q in matched_for_cycle if q.get("is_mcq") is True or q.get("q_type") == "MCQ"]
    elif cat_clean in ["descriptive", "normal"]:
        matched = [q for q in matched_for_cycle if not (q.get("is_mcq") is True or q.get("q_type") == "MCQ")]
    else:
        matched = matched_for_cycle

    # Sort so questions with verified answer keys come first
    def _parse_qnum(val):
        try:
            cleaned = re.sub(r"[^0-9]", "", str(val))
            return int(cleaned) if cleaned else 999
        except Exception:
            return 999

    matched.sort(key=lambda x: (x.get("answer_key") is None, _parse_qnum(x.get("q_num"))))

    from collections import Counter
    sub_counts = Counter(q.get("subject") for q in all_qs if q.get("subject"))
    available_subjects = [{"subject": k, "count": v} for k, v in sub_counts.most_common()]

    return {
        "subject": "All Subjects" if is_universal else subject,
        "cycle": cycle or "ALL",
        "category": cat_clean,
        "total_available": len(matched),
        "total_descriptive": total_descriptive,
        "total_mcqs": total_mcqs,
        "available_subjects": available_subjects,
        "questions": matched[:limit]
    }
