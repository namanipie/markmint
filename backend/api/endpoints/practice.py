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
