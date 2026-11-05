from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from backend.services.prediction.engine import ExamScopeCombinedModel
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.context import HistoricalContext, PredictionTarget, resolve_target_year
from backend.services.prediction.repository import HistoricalRepository
from backend.core.database import get_db
from backend.models.core import Course, Exam, Topic, Unit, Syllabus, Question, Section
from backend.services.assessment_cycle import normalize_assessment_cycle, AssessmentCycle
from backend.services.assessment_plan_registry import get_course_assessment_scope
import re
from typing import Any, Optional

router = APIRouter()


import threading

_course_resolution_cache: dict[str, int] = {}
_course_cache_lock = threading.Lock()


def clear_course_resolution_cache():
    """Clear in-memory course resolution cache."""
    with _course_cache_lock:
        _course_resolution_cache.clear()


def _remember_course(course: Optional[Course]):
    if not course:
        return
    cid = course.id
    with _course_cache_lock:
        _course_resolution_cache[str(cid)] = cid
        if course.canonical_code:
            cc = course.canonical_code.strip().lower()
            _course_resolution_cache[cc] = cid
            _course_resolution_cache[re.sub(r'[^a-zA-Z0-9]', '', cc)] = cid
        if course.code:
            code = course.code.strip().lower()
            _course_resolution_cache[code] = cid
            _course_resolution_cache[re.sub(r'[^a-zA-Z0-9]', '', code)] = cid
        if course.name:
            name = course.name.strip().lower()
            _course_resolution_cache[name] = cid
            _course_resolution_cache[re.sub(r'[^a-zA-Z0-9]', '', name)] = cid


def warm_course_resolution_cache(db: Session):
    """Pre-warm course resolution cache with all courses, codes, and canonical aliases."""
    courses = db.query(Course).all()
    for c in courses:
        _remember_course(c)


def _find_course(db: Session, identifier: str) -> Optional[Course]:
    """Generically resolve a course by exact name, case-insensitive name, code, canonical code, ID, or alphanumeric string."""
    if not identifier:
        return None

    norm_key = str(identifier).strip().lower()
    clean_alpha = re.sub(r'[^a-zA-Z0-9]', '', norm_key)

    with _course_cache_lock:
        cached_id = _course_resolution_cache.get(norm_key) or _course_resolution_cache.get(clean_alpha)
    if cached_id is not None:
        course = db.query(Course).options(joinedload(Course.tracks)).filter(Course.id == cached_id).first()
        if course:
            return course

    # 1. Numeric ID match (fastest if numeric ID passed)
    if str(identifier).isdigit():
        course = db.query(Course).options(joinedload(Course.tracks)).filter(Course.id == int(identifier)).first()
        if course:
            _remember_course(course)
            return course

    # 2. Canonical code match (e.g. 21MAB101T)
    course = db.query(Course).options(joinedload(Course.tracks)).filter(func.lower(Course.canonical_code) == identifier.lower()).first()
    if course:
        _remember_course(course)
        return course

    # 3. Exact or case-insensitive name match
    course = db.query(Course).options(joinedload(Course.tracks)).filter(func.lower(Course.name) == identifier.lower()).first()
    if course:
        _remember_course(course)
        return course

    # 4. Case-insensitive code match (e.g. SEM1-CALC)
    course = db.query(Course).options(joinedload(Course.tracks)).filter(func.lower(Course.code) == identifier.lower()).first()
    if course:
        _remember_course(course)
        return course

    # 5. Normalized alphanumeric match (ignores spaces, punctuation, case)
    if clean_alpha:
        all_courses = db.query(Course).all()
        for c in all_courses:
            if c.canonical_code and re.sub(r'[^a-zA-Z0-9]', '', c.canonical_code).lower() == clean_alpha:
                course = db.query(Course).options(joinedload(Course.tracks)).filter(Course.id == c.id).first()
                _remember_course(course)
                return course
            if re.sub(r'[^a-zA-Z0-9]', '', c.name).lower() == clean_alpha:
                course = db.query(Course).options(joinedload(Course.tracks)).filter(Course.id == c.id).first()
                _remember_course(course)
                return course
            if re.sub(r'[^a-zA-Z0-9]', '', c.code).lower() == clean_alpha:
                course = db.query(Course).options(joinedload(Course.tracks)).filter(Course.id == c.id).first()
                _remember_course(course)
                return course

        # 6. Prefix / substring match for course names (e.g. 'Calculus' -> 'Calculus And Linear Algebra')
        for c in all_courses:
            if clean_alpha in re.sub(r'[^a-zA-Z0-9]', '', c.name).lower():
                course = db.query(Course).options(joinedload(Course.tracks)).filter(Course.id == c.id).first()
                _remember_course(course)
                return course

    return None


find_course = _find_course
resolve_course = _find_course


def _build_historical_exam_payloads(hist_exams_orm: list[Any]) -> list[dict[str, Any]]:
    """Map ORM exams to the stable payload consumed by ExamDNA."""
    return [
        {
            "id": exam.id,
            "year": exam.year,
            "course_id": getattr(exam, "course_id", None),
            "track_id": getattr(exam, "track_id", None),
            "exam_type": exam.assessment_type,
            "questions": [
                {
                    "id": question.id,
                    "marks": question.marks,
                    "is_alternative": question.is_alternative,
                    "topic": question.topics[0].name if question.topics else None,
                    "topics": [t.name for t in question.topics] if getattr(question, "topics", None) else [],
                    "unit": (
                        question.topics[0].unit.name
                        if (question.topics and getattr(question.topics[0], "unit", None))
                        else None
                    ),
                    "units": (
                        list(dict.fromkeys(
                            t.unit.name for t in question.topics if getattr(t, "unit", None) and t.unit.name
                        ))
                        if getattr(question, "topics", None)
                        else []
                    ),
                    "topic_mappings": [
                        {
                            "topic": t.name,
                            "unit": t.unit.name if getattr(t, "unit", None) else None
                        }
                        for t in question.topics
                    ] if getattr(question, "topics", None) else [],
                    "question_type": question.question_type,
                    "repetition_type": (
                        question.memberships[0].match_type
                        if getattr(question, "memberships", None)
                        else "singleton"
                    ),
                    "family_id": (
                        getattr(question, "family_id", None)
                        or (getattr(getattr(question, "family", None), "id", None))
                    ),
                    "family_name": (
                        (
                            getattr(question.family, "canonical_name", "").strip()
                            if getattr(question, "family", None) and getattr(question.family, "canonical_name", "").strip()
                            else f"Family {getattr(question, 'family_id', None) or getattr(getattr(question, 'family', None), 'id', '')}"
                        )
                        if (getattr(question, "family_id", None) or getattr(question, "family", None))
                        else None
                    ),
                    "difficulty": getattr(question, "difficulty", None),
                }
                for section in exam.sections
                for question in section.questions
            ],
        }
        for exam in hist_exams_orm
    ]

@router.get("/predictions/{subject}")
def get_prediction(
    subject: str,
    target_year: Optional[int] = Query(None),
    assessment_cycle: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
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

        target_year = resolve_target_year(
            db,
            course.id,
            target_year=target_year,
            track_id=active_track.id if active_track else None,
        )

        # Temporal isolation constraint with assessment cycle scoping
        context = HistoricalContext(
            course_id=course.id,
            cutoff_year=target_year,
            assessment_cycle=norm_cycle,
            track_id=active_track.id if active_track else None
        )
        repo = HistoricalRepository(db, context)
        
        hist_exams_orm = repo.get_historical_exams()
        scope = get_course_assessment_scope(
            course.id,
            norm_cycle,
            db=db,
            track_id=active_track.id if active_track else None
        )

        from datetime import datetime, timezone
        from backend.core.version import MODEL_VERSION, TAXONOMY_VERSION, ENGINE_VERSION
        from collections import defaultdict

        # OPTION B: Syllabus-derived baseline when 0 historical papers exist for this specific exam
        if not hist_exams_orm:
            intended_units = sorted(list(scope.in_scope_unit_numbers)) if scope.in_scope_unit_numbers else []
            if not intended_units:
                if norm_cycle == "CT1":
                    intended_units = [1, 2]
                elif norm_cycle == "CT2":
                    intended_units = [3, 4]
                else:
                    intended_units = [1, 2, 3, 4, 5]

            syl_filter = [Syllabus.course_id == course.id]
            if active_track:
                syl_filter.append(Syllabus.track_id == active_track.id)

            syl_topic_rows = (
                db.query(Topic.id, Topic.name, Unit.number, Unit.name)
                .join(Unit, Topic.unit_id == Unit.id)
                .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                .filter(*syl_filter, Unit.number.in_(intended_units))
                .order_by(Unit.number.asc(), Topic.id.asc())
                .all()
            )

            cycle_label = scope.student_label or ("Cycle Test 1" if norm_cycle == "CT1" else "Cycle Test 2" if norm_cycle == "CT2" else "End Semester")

            baseline_predictions = []
            for rank_num, (t_id, t_name, u_num, u_name) in enumerate(syl_topic_rows[:12], 1):
                clean_name = t_name.strip()
                score_val = round(max(0.20, 1.0 - (rank_num * 0.06)), 2)
                baseline_predictions.append({
                    "category": "topic",
                    "name": clean_name,
                    "rank": rank_num,
                    "score": score_val,
                    "confidence": "SYLLABUS_BASELINE",
                    "prediction_score": score_val,
                    "probability": None,
                    "topic_id": t_id,
                    "unit_number": u_num,
                    "unit_name": u_name,
                    "evidence_count": 0,
                    "papers_analyzed": 0,
                    "papers_with_topic": 0,
                    "historical_occurrences": 0,
                    "total_marks_observed": 0.0,
                    "evidence_sufficiency": "BASELINE_SYLLABUS_ONLY",
                    "is_baseline_fallback": True,
                    "reason_codes": ["SYLLABUS_MANDATE", "CORE_CURRICULUM"],
                    "explanation": f"Syllabus-Derived Baseline ({cycle_label}) — 0 historical papers in archive yet. Focus on this foundational Unit {u_num} topic.",
                    "timeline": [],
                    "evidence_breakdown": {
                        "average_marks": 0.0,
                        "distinct_exam_count": 0,
                        "exam_coverage_ratio": 0.0,
                        "historical_occurrences": 0,
                        "total_marks_observed": 0.0,
                        "source_exams": [],
                        "reason_summary": f"Curriculum baseline for {cycle_label} from official SRMIST syllabus."
                    }
                })

            baseline_unit_breakdown = []
            for r_idx, u_num in enumerate(intended_units, 1):
                matching_rows = [r for r in syl_topic_rows if r[2] == u_num]
                u_title = matching_rows[0][3] if matching_rows else f"Unit {u_num}"
                equal_pct = round(100.0 / len(intended_units), 1) if intended_units else 0.0
                baseline_unit_breakdown.append({
                    "rank": r_idx,
                    "unit_number": u_num,
                    "unit_name": u_title,
                    "question_count": 0,
                    "marks": 0.0,
                    "percentage_of_marks": equal_pct,
                    "percentage_of_questions": equal_pct,
                    "paper_coverage": 0.0,
                    "is_baseline": True
                })

            assessment_scope_payload = {
                "student_cycle": norm_cycle or "ALL",
                "component_code": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
                "component_label": scope.component_label or cycle_label,
                "student_label": cycle_label,
                "role": scope.role,
                "marks": scope.marks,
                "evidence_status": "SYLLABUS_FALLBACK",
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "source_document": scope.source_document,
                "unit_numbers": intended_units,
                "total_in_scope_topics": len(syl_topic_rows),
                "observed_in_scope_topics": 0,
                "unobserved_in_scope_topics": [
                    {"name": r[1], "status": "UNOBSERVED_IN_SCOPE", "message": "In syllabus scope"}
                    for r in syl_topic_rows
                ],
                "out_of_scope_observed_topics": [],
            }

            return {
                "course_id": course.id,
                "subject": course.name,
                "target_year": target_year,
                "assessment_cycle": norm_cycle or "ALL",
                "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
                "assessment_label": cycle_label,
                "evidence_status": "SYLLABUS_FALLBACK",
                "intended_scope": scope.intended_scope,
                "observed_scope": scope.observed_scope,
                "assessment_scope": assessment_scope_payload,
                "predictions": baseline_predictions,
                "empirical_unit_breakdown": baseline_unit_breakdown,
                "observed_years": [],
                "unobserved_years": [],
                "gap_years": [],
                "evidence": f"Syllabus-derived baseline: 0 historical {cycle_label} papers available in archive yet.",
                "data_quality": f"Curriculum baseline active. Topics prioritized from official syllabus Units {', '.join(str(u) for u in intended_units)}.",
                "model_metadata": {
                    "model_version": MODEL_VERSION,
                    "taxonomy_version": TAXONOMY_VERSION,
                    "engine_version": ENGINE_VERSION,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            }

        # HISTORICAL PAPERS EXIST: Compute empirical data-driven predictions strictly for this exam
        hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)

        analyzer = DNAAnalyzerService()
        dna = analyzer.analyze(hist_exams_dicts)
        
        engine = ExamScopeCombinedModel(dna)
        all_topic_preds = engine.predict(PredictionTarget.TOPIC)
        family_preds = engine.predict(PredictionTarget.FAMILY)

        # Compute empirical unit distribution strictly from historical papers of THIS exam (NO HARDCODING)
        empirical_unit_map = defaultdict(lambda: {"q_count": 0, "marks": 0.0, "papers": set(), "name": ""})
        total_eval_q = 0
        total_eval_m = 0.0
        for ex in hist_exams_orm:
            for sec in ex.sections:
                for q in sec.questions:
                    total_eval_q += 1
                    m = float(q.marks or 0.0)
                    total_eval_m += m
                    for t in q.topics:
                        if t.unit:
                            u_num = t.unit.number
                            empirical_unit_map[u_num]["q_count"] += 1
                            empirical_unit_map[u_num]["marks"] += m
                            empirical_unit_map[u_num]["papers"].add(ex.id)
                            empirical_unit_map[u_num]["name"] = t.unit.name

        # Rank units strictly by marks & question appearances in these exam papers
        ranked_empirical_units = []
        for rank_idx, (u_num, data) in enumerate(
            sorted(empirical_unit_map.items(), key=lambda x: (x[1]["marks"], x[1]["q_count"]), reverse=True),
            1
        ):
            m_pct = round((data["marks"] / total_eval_m * 100), 1) if total_eval_m > 0 else 0.0
            q_pct = round((data["q_count"] / total_eval_q * 100), 1) if total_eval_q > 0 else 0.0
            coverage = round(len(data["papers"]) / len(hist_exams_orm), 2) if hist_exams_orm else 0.0
            ranked_empirical_units.append({
                "rank": rank_idx,
                "unit_number": u_num,
                "unit_name": data["name"],
                "question_count": data["q_count"],
                "marks": round(data["marks"], 1),
                "percentage_of_marks": m_pct,
                "percentage_of_questions": q_pct,
                "paper_coverage": coverage,
                "is_baseline": False
            })

        # All topics derived from this exam's papers are naturally valid; prioritize in-scope if scope defined
        if not scope.is_all and scope.in_scope_topic_names:
            in_scope_preds = [p for p in all_topic_preds if p.name in scope.in_scope_topic_names]
            out_of_scope_preds = [p for p in all_topic_preds if p.name not in scope.in_scope_topic_names]
            topic_preds = in_scope_preds + out_of_scope_preds
        else:
            topic_preds = all_topic_preds
            out_of_scope_preds = []

        unobserved_in_scope = (
            [
                {
                    "name": name,
                    "status": "UNOBSERVED_IN_SCOPE",
                    "message": "In syllabus scope, but no historical evidence available",
                }
                for name in sorted(list(scope.in_scope_topic_names - {p.name for p in topic_preds}))
            ]
            if (not scope.is_all and scope.in_scope_topic_names)
            else []
        )
        assessment_scope_payload = {
            "student_cycle": norm_cycle or "ALL",
            "component_code": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "component_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "student_label": scope.student_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "role": scope.role,
            "marks": scope.marks,
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "source_document": scope.source_document,
            "unit_numbers": sorted(list(scope.in_scope_unit_numbers)) if scope.in_scope_unit_numbers else [u["unit_number"] for u in ranked_empirical_units],
            "total_in_scope_topics": len(scope.in_scope_topic_names),
            "observed_in_scope_topics": len(topic_preds),
            "unobserved_in_scope_topics": unobserved_in_scope,
            "out_of_scope_observed_topics": [
                {
                    "name": p.name,
                    "status": "OUT_OF_SCOPE_OBSERVED",
                    "score": round(float(p.score or 0.0), 4),
                    "message": "Observed on historical examination papers.",
                }
                for p in out_of_scope_preds
            ],
        }

        observed_years = sorted(list({e.year for e in hist_exams_orm if e.year is not None}))

        predictions = []
        # Return top 10 empirical topic predictions with clean, recognizable names and authoritative unit tags
        for p in topic_preds[:10]:
            p_dict = p.to_dict()
            t_obj = (
                db.query(Topic)
                .join(Unit, Topic.unit_id == Unit.id)
                .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                .filter(Syllabus.course_id == course.id, Topic.name == p.name)
                .first()
            )
            if t_obj:
                p_dict["topic_id"] = t_obj.id
                if t_obj.unit:
                    p_dict["unit_number"] = t_obj.unit.number
                    p_dict["unit_name"] = t_obj.unit.name

            topic_years = {
                e.year for e in hist_exams_orm
                if e.year is not None and any(
                    any(t.name == p.name for t in q.topics)
                    for s in e.sections for q in s.questions
                )
            }
            p_dict["timeline"] = [
                {
                    "year": y,
                    "exam_exists": True,
                    "topic_present": y in topic_years,
                    "family_present": False,
                    "present": y in topic_years,
                    "status": "TOPIC_PRESENT" if y in topic_years else "TOPIC_ABSENT",
                }
                for y in observed_years
            ]
            p_dict["historical_years"] = sorted(list(topic_years))
            matching_topic_exams = [
                {
                    "exam_id": e.id,
                    "year": e.year,
                    "assessment_type": e.assessment_type,
                    "title": e.document.title if (getattr(e, "document", None) and e.document and e.document.title) else f"Exam {e.year} ({e.assessment_type or 'Main'})",
                }
                for e in hist_exams_orm
                if e.year is not None and any(
                    any(t.name == p.name for t in q.topics)
                    for s in e.sections for q in s.questions
                )
            ]
            if "evidence_breakdown" in p_dict:
                p_dict["evidence_breakdown"]["source_exams"] = matching_topic_exams
                if topic_years:
                    p_dict["evidence_breakdown"]["source_years"] = sorted(list(topic_years))
            if "explainability" in p_dict:
                p_dict["explainability"]["source_exams"] = matching_topic_exams
                if topic_years:
                    p_dict["explainability"]["source_years"] = sorted(list(topic_years))
            predictions.append(p_dict)

        # Return top recurring question families with clean recognizable labels and unit numbers
        for p in family_preds[:6]:
            p_dict = p.to_dict()
            p_dict["is_family"] = True

            # Resolve unit number for family from its questions
            fam_q = (
                db.query(Question)
                .join(Section)
                .join(Exam)
                .filter(Question.family_id == p_dict.get("family_id"), Exam.course_id == course.id)
                .first()
            )
            if fam_q and fam_q.topics and fam_q.topics[0].unit:
                p_dict["unit_number"] = fam_q.topics[0].unit.number
                p_dict["unit_name"] = fam_q.topics[0].unit.name
                p_dict["associated_topic_name"] = fam_q.topics[0].name

            fam_years = {
                e.year for e in hist_exams_orm
                if e.year is not None and any(
                    q.family and q.family.canonical_name == p.name
                    for s in e.sections for q in s.questions
                )
            }
            p_dict["timeline"] = [
                {
                    "year": y,
                    "exam_exists": True,
                    "topic_present": False,
                    "family_present": y in fam_years,
                    "present": y in fam_years,
                    "status": "FAMILY_PRESENT" if y in fam_years else "FAMILY_ABSENT",
                }
                for y in observed_years
            ]
            p_dict["historical_years"] = sorted(list(fam_years))
            matching_fam_exams = [
                {
                    "exam_id": e.id,
                    "year": e.year,
                    "assessment_type": e.assessment_type,
                    "title": e.document.title if (getattr(e, "document", None) and e.document and e.document.title) else f"Exam {e.year} ({e.assessment_type or 'Main'})",
                }
                for e in hist_exams_orm
                if e.year is not None and any(
                    q.family and q.family.canonical_name == p.name
                    for s in e.sections for q in s.questions
                )
            ]
            if "evidence_breakdown" in p_dict:
                p_dict["evidence_breakdown"]["source_exams"] = matching_fam_exams
                if fam_years:
                    p_dict["evidence_breakdown"]["source_years"] = sorted(list(fam_years))
            if "explainability" in p_dict:
                p_dict["explainability"]["source_exams"] = matching_fam_exams
                if fam_years:
                    p_dict["explainability"]["source_years"] = sorted(list(fam_years))
            predictions.append(p_dict)

        all_span = list(range(observed_years[0], observed_years[-1] + 1)) if observed_years else []
        unobserved_years = [y for y in all_span if y not in observed_years]

        return {
            "course_id": course.id,
            "subject": course.name,
            "target_year": target_year,
            "assessment_cycle": norm_cycle or "ALL",
            "assessment_component": scope.component_code or ("ALL" if scope.is_all else norm_cycle),
            "assessment_label": scope.component_label or ("All Assessments" if scope.is_all else (norm_cycle or "ALL")),
            "evidence_status": scope.evidence_status,
            "intended_scope": scope.intended_scope,
            "observed_scope": scope.observed_scope,
            "assessment_scope": assessment_scope_payload,
            "predictions": predictions,
            "empirical_unit_breakdown": ranked_empirical_units,
            "observed_years": observed_years,
            "unobserved_years": unobserved_years,
            "gap_years": unobserved_years,
            "evidence": f"Analyzed {len(hist_exams_orm)} historical {scope.student_label or norm_cycle} exams across {len(observed_years)} years.",
            "data_quality": f"Data-driven evidence base for {scope.student_label or norm_cycle} from verified examination archives.",
            "model_metadata": {
                "model_version": MODEL_VERSION,
                "taxonomy_version": TAXONOMY_VERSION,
                "engine_version": ENGINE_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        from backend.core.config import settings, Environment
        logging.getLogger("markmint").exception("Prediction calculation error for subject '%s': %s", subject, e)
        if settings.ENVIRONMENT == Environment.PRODUCTION:
            raise HTTPException(
                status_code=500,
                detail="Unable to synthesize prediction forecast due to an internal calculation error. Please try again later."
            )
        raise HTTPException(status_code=500, detail=str(e))
