"""
Paper-Derived Assessment Scope & Coverage Service for MarkMint.

Core Invariants:
1. Canonical Syllabus Unit != Observed Exam Paper Coverage
2. The Syllabus defines what Units/Topics exist (N is variable, not fixed to 5).
3. The Exam Paper defines what was actually examined (derived strictly from question -> topic -> unit mappings).
4. No unit is ever inferred from question numbering or topic numbering.
5. Intended Scope (institutional plan) and Observed Scope (paper evidence) are kept separate.
6. Assessment identity is resolved using strongest evidence with source provenance.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus, Document
from backend.services.assessment_cycle import AssessmentCycle, normalize_assessment_cycle
from backend.services.assessment_plan_registry import (
    get_course_assessment_plan,
    normalize_course_assessment_type,
    get_course_raw_types_for_cycle,
    ComponentDefinition,
)


@dataclass
class AssessmentIdentity:
    normalized_code: str          # e.g. "CT1", "CT2", "ENDSEM", "MODEL", "UNKNOWN"
    raw_type: Optional[str]       # exact raw Exam.assessment_type
    identification_source: str    # "metadata" | "document_metadata" | "document_title" | "filename" | "fallback"
    confidence: float             # 1.0 (metadata), 0.9 (doc title), 0.85 (filename), 0.3 (fallback)
    student_cycle: str            # "CT1" | "CT2" | "ENDSEM" | "ALL"
    evidence_text: Optional[str] = None


@dataclass
class QuestionObservedLineage:
    question_id: int
    question_number: str
    marks: Optional[float]
    is_alternative: bool
    topic_ids: List[int]
    topic_names: List[str]
    unit_numbers: List[int]
    unit_names: List[str]
    is_mapped: bool


@dataclass
class PaperObservedCoverage:
    exam_id: int
    year: Optional[int]
    course_id: int
    assessment_identity: AssessmentIdentity
    total_questions: int
    mapped_questions_count: int
    unmapped_questions_count: int
    observed_unit_numbers: List[int]
    observed_topic_ids: List[int]
    observed_topic_names: List[str]
    question_count_by_unit: Dict[int, int]
    marks_by_unit: Dict[int, float]
    document_title: Optional[str] = None
    document_source: Optional[str] = None
    question_lineage: List[QuestionObservedLineage] = field(default_factory=list)


@dataclass
class CycleObservedCoverage:
    course_id: int
    student_cycle: str
    paper_count: int
    total_questions: int
    mapped_questions_count: int
    unmapped_questions_count: int
    observed_unit_numbers: List[int]
    observed_topic_ids: List[int]
    observed_topic_names: List[str]
    question_count_by_unit: Dict[int, int]
    marks_by_unit: Dict[int, float]
    papers: List[Dict[str, Any]] = field(default_factory=list)


def identify_exam_assessment(exam: Exam, course_id: int) -> AssessmentIdentity:
    """
    Determine the assessment identity of an exam paper using the strongest available evidence in strict order:
    1. Explicit stored metadata on Exam (exam.assessment_type)
    2. Document metadata (doc.exam_type)
    3. Document title / header
    4. Filename / path indicators
    5. Fallback

    Retains source provenance and confidence. Never mutates raw data.
    """
    raw_type = (exam.assessment_type or "").strip()
    plan = get_course_assessment_plan(course_id)

    # 1. Stored Exam.assessment_type metadata (Highest confidence if present and informative)
    if raw_type and raw_type.upper() not in ("UNKNOWN", "NONE", "NULL", ""):
        # Check course-specific assessment plan first
        if plan:
            norm_code = normalize_course_assessment_type(course_id, raw_type)
            if norm_code:
                student_cycle = "ALL"
                for comp in plan.components:
                    if comp.code == norm_code:
                        norm_label = normalize_assessment_cycle(comp.student_label)
                        student_cycle = norm_label if norm_label else comp.student_label
                        break
                return AssessmentIdentity(
                    normalized_code=norm_code,
                    raw_type=raw_type,
                    identification_source="metadata",
                    confidence=1.0,
                    student_cycle=student_cycle,
                    evidence_text=f"Exam.assessment_type='{raw_type}' matched course plan component '{norm_code}'",
                )

        # Fallback to general cycle normalization
        gen_cycle = normalize_assessment_cycle(raw_type)
        if gen_cycle and gen_cycle != AssessmentCycle.ALL.value:
            return AssessmentIdentity(
                normalized_code=gen_cycle,
                raw_type=raw_type,
                identification_source="metadata",
                confidence=0.95,
                student_cycle=gen_cycle,
                evidence_text=f"Exam.assessment_type='{raw_type}' normalized to '{gen_cycle}'",
            )

        return AssessmentIdentity(
            normalized_code=raw_type,
            raw_type=raw_type,
            identification_source="metadata",
            confidence=0.8,
            student_cycle="ALL",
            evidence_text=f"Exam.assessment_type='{raw_type}' preserved as raw label",
        )

    # 2. Document metadata
    doc = getattr(exam, "document", None)
    if doc and doc.exam_type and doc.exam_type.strip().upper() not in ("UNKNOWN", "NONE", ""):
        doc_exam_type = doc.exam_type.strip()
        norm_code = normalize_course_assessment_type(course_id, doc_exam_type) if plan else normalize_assessment_cycle(doc_exam_type)
        if norm_code:
            return AssessmentIdentity(
                normalized_code=norm_code,
                raw_type=raw_type or None,
                identification_source="document_metadata",
                confidence=0.9,
                student_cycle=norm_code,
                evidence_text=f"Document.exam_type='{doc_exam_type}'",
            )

    # 3. Document Title / Header
    if doc and doc.title:
        title_upper = doc.title.upper()
        if any(w in title_upper for w in ["CT1", "CT-1", "CYCLE TEST 1", "CLA-1", "CLA1"]):
            return AssessmentIdentity(
                normalized_code="CT1",
                raw_type=raw_type or None,
                identification_source="document_title",
                confidence=0.9,
                student_cycle="CT1",
                evidence_text=f"Document title '{doc.title}' contains CT1 indicator",
            )
        if any(w in title_upper for w in ["CT2", "CT-2", "CYCLE TEST 2", "CLA-2", "CLA2"]):
            return AssessmentIdentity(
                normalized_code="CT2",
                raw_type=raw_type or None,
                identification_source="document_title",
                confidence=0.9,
                student_cycle="CT2",
                evidence_text=f"Document title '{doc.title}' contains CT2 indicator",
            )
        if any(w in title_upper for w in ["END_SEM", "ENDSEM", "DEGREE EXAMINATION", "SEMESTER EXAMINATION", "END SEMESTER"]):
            return AssessmentIdentity(
                normalized_code="ENDSEM",
                raw_type=raw_type or None,
                identification_source="document_title",
                confidence=0.9,
                student_cycle="ENDSEM",
                evidence_text=f"Document title '{doc.title}' contains EndSem indicator",
            )

    # 4. Filename / Path Indicators
    if doc and (doc.source or doc.original_url):
        path_str = f"{doc.source or ''} {doc.original_url or ''}".upper()
        if any(w in path_str for w in ["CT1", "CT-1", "CYCLE_TEST_1", "CLA1"]):
            return AssessmentIdentity(
                normalized_code="CT1",
                raw_type=raw_type or None,
                identification_source="filename",
                confidence=0.85,
                student_cycle="CT1",
                evidence_text="File path contains CT1 indicator",
            )
        if any(w in path_str for w in ["CT2", "CT-2", "CYCLE_TEST_2", "CLA2"]):
            return AssessmentIdentity(
                normalized_code="CT2",
                raw_type=raw_type or None,
                identification_source="filename",
                confidence=0.85,
                student_cycle="CT2",
                evidence_text="File path contains CT2 indicator",
            )
        if any(w in path_str for w in ["ENDSEM", "END_SEM", "DEGREE", "UNIVERSITY", "UES"]):
            return AssessmentIdentity(
                normalized_code="ENDSEM",
                raw_type=raw_type or None,
                identification_source="filename",
                confidence=0.85,
                student_cycle="ENDSEM",
                evidence_text="File path contains EndSem indicator",
            )

    # 5. Fallback
    return AssessmentIdentity(
        normalized_code="UNKNOWN",
        raw_type=raw_type or None,
        identification_source="fallback",
        confidence=0.3,
        student_cycle="ALL",
        evidence_text="No conclusive assessment indicators found; default to UNKNOWN",
    )


def compute_paper_observed_coverage(exam: Exam) -> PaperObservedCoverage:
    """
    Derives the actual examined syllabus scope for a single exam paper.
    
    Lineage: Question -> mapped Topics -> canonical Units.
    Never assumes question number = unit number.
    Never assumes topic number = unit number.
    """
    assessment_identity = identify_exam_assessment(exam, exam.course_id)
    doc = getattr(exam, "document", None)

    observed_unit_numbers_set: Set[int] = set()
    observed_topic_ids_set: Set[int] = set()
    observed_topic_names_set: Set[str] = set()
    question_count_by_unit: Dict[int, int] = {}
    marks_by_unit: Dict[int, float] = {}

    total_questions = 0
    mapped_questions_count = 0
    unmapped_questions_count = 0
    question_lineage: List[QuestionObservedLineage] = []

    sections = getattr(exam, "sections", []) or []
    for sec in sections:
        questions = getattr(sec, "questions", []) or []
        for q in questions:
            total_questions += 1
            q_topics = getattr(q, "topics", []) or []
            
            t_ids = [t.id for t in q_topics]
            t_names = [t.name for t in q_topics]
            
            q_units: List[Unit] = []
            for t in q_topics:
                u = getattr(t, "unit", None)
                if u and u not in q_units:
                    q_units.append(u)

            u_numbers = sorted(list({u.number for u in q_units}))
            u_names = [u.name for u in q_units]

            is_mapped = len(q_topics) > 0 and len(u_numbers) > 0
            if is_mapped:
                mapped_questions_count += 1
                observed_topic_ids_set.update(t_ids)
                observed_topic_names_set.update(t_names)
                for un in u_numbers:
                    observed_unit_numbers_set.add(un)
                    question_count_by_unit[un] = question_count_by_unit.get(un, 0) + 1
                    if q.marks and not q.is_alternative:
                        marks_by_unit[un] = round(marks_by_unit.get(un, 0.0) + float(q.marks), 2)
            else:
                unmapped_questions_count += 1

            question_lineage.append(
                QuestionObservedLineage(
                    question_id=q.id,
                    question_number=str(q.question_number),
                    marks=q.marks,
                    is_alternative=q.is_alternative,
                    topic_ids=t_ids,
                    topic_names=t_names,
                    unit_numbers=u_numbers,
                    unit_names=u_names,
                    is_mapped=is_mapped,
                )
            )

    return PaperObservedCoverage(
        exam_id=exam.id,
        year=exam.year,
        course_id=exam.course_id,
        assessment_identity=assessment_identity,
        total_questions=total_questions,
        mapped_questions_count=mapped_questions_count,
        unmapped_questions_count=unmapped_questions_count,
        observed_unit_numbers=sorted(list(observed_unit_numbers_set)),
        observed_topic_ids=sorted(list(observed_topic_ids_set)),
        observed_topic_names=sorted(list(observed_topic_names_set)),
        question_count_by_unit=dict(sorted(question_count_by_unit.items())),
        marks_by_unit=dict(sorted(marks_by_unit.items())),
        document_title=doc.title if doc else None,
        document_source=doc.source if doc else None,
        question_lineage=question_lineage,
    )


def compute_cycle_observed_coverage(
    course_id: int,
    student_cycle: str,
    exams: List[Exam],
) -> CycleObservedCoverage:
    """
    Aggregates paper-level observed coverage across all historical exams belonging to a cycle.
    Preserves paper-level evidence breakdowns.
    """
    is_all = not student_cycle or student_cycle.strip().upper() == "ALL"
    cycle_clean = "ALL" if is_all else student_cycle.strip().upper()

    all_observed_units: Set[int] = set()
    all_observed_topic_ids: Set[int] = set()
    all_observed_topic_names: Set[str] = set()
    total_q_count_by_unit: Dict[int, int] = {}
    total_marks_by_unit: Dict[int, float] = {}

    total_questions = 0
    mapped_questions = 0
    unmapped_questions = 0
    paper_summaries: List[Dict[str, Any]] = []

    for exam in exams:
        paper_cov = compute_paper_observed_coverage(exam)
        total_questions += paper_cov.total_questions
        mapped_questions += paper_cov.mapped_questions_count
        unmapped_questions += paper_cov.unmapped_questions_count

        all_observed_units.update(paper_cov.observed_unit_numbers)
        all_observed_topic_ids.update(paper_cov.observed_topic_ids)
        all_observed_topic_names.update(paper_cov.observed_topic_names)

        for un, cnt in paper_cov.question_count_by_unit.items():
            total_q_count_by_unit[un] = total_q_count_by_unit.get(un, 0) + cnt
        for un, m in paper_cov.marks_by_unit.items():
            total_marks_by_unit[un] = round(total_marks_by_unit.get(un, 0.0) + m, 2)

        paper_summaries.append({
            "exam_id": exam.id,
            "year": exam.year,
            "raw_assessment_type": exam.assessment_type,
            "normalized_code": paper_cov.assessment_identity.normalized_code,
            "identification_source": paper_cov.assessment_identity.identification_source,
            "identification_confidence": paper_cov.assessment_identity.confidence,
            "document_title": paper_cov.document_title,
            "total_questions": paper_cov.total_questions,
            "mapped_questions": paper_cov.mapped_questions_count,
            "unmapped_questions": paper_cov.unmapped_questions_count,
            "observed_units": paper_cov.observed_unit_numbers,
            "question_count_by_unit": paper_cov.question_count_by_unit,
            "marks_by_unit": paper_cov.marks_by_unit,
        })

    return CycleObservedCoverage(
        course_id=course_id,
        student_cycle=cycle_clean,
        paper_count=len(exams),
        total_questions=total_questions,
        mapped_questions_count=mapped_questions,
        unmapped_questions_count=unmapped_questions,
        observed_unit_numbers=sorted(list(all_observed_units)),
        observed_topic_ids=sorted(list(all_observed_topic_ids)),
        observed_topic_names=sorted(list(all_observed_topic_names)),
        question_count_by_unit=dict(sorted(total_q_count_by_unit.items())),
        marks_by_unit=dict(sorted(total_marks_by_unit.items())),
        papers=paper_summaries,
    )


def build_coverage_audit_chain(course_id: int, exam_id: int, db: Session) -> Dict[str, Any]:
    """
    Returns an auditable, end-to-end trace:
    Exam -> Question -> Question Topic -> Canonical Topic -> Canonical Unit -> Assessment Identity -> Observed Coverage.
    """
    exam = (
        db.query(Exam)
        .options(
            selectinload(Exam.document),
            selectinload(Exam.sections)
            .selectinload(Section.questions)
            .selectinload(Question.topics)
            .selectinload(Topic.unit),
        )
        .filter(Exam.id == exam_id, Exam.course_id == course_id)
        .first()
    )
    if not exam:
        return {"error": f"Exam id={exam_id} not found for course_id={course_id}"}

    paper_cov = compute_paper_observed_coverage(exam)

    audit_questions = []
    for item in paper_cov.question_lineage:
        audit_questions.append({
            "question_id": item.question_id,
            "question_number": item.question_number,
            "marks": item.marks,
            "is_alternative": item.is_alternative,
            "is_mapped": item.is_mapped,
            "mapped_topics": [
                {"id": tid, "name": tname}
                for tid, tname in zip(item.topic_ids, item.topic_names)
            ],
            "canonical_units": [
                {"number": un, "title": uname}
                for un, uname in zip(item.unit_numbers, item.unit_names)
            ],
        })

    return {
        "course_id": course_id,
        "exam_id": exam.id,
        "year": exam.year,
        "raw_assessment_type": exam.assessment_type,
        "assessment_identity": {
            "normalized_code": paper_cov.assessment_identity.normalized_code,
            "raw_type": paper_cov.assessment_identity.raw_type,
            "source": paper_cov.assessment_identity.identification_source,
            "confidence": paper_cov.assessment_identity.confidence,
            "evidence": paper_cov.assessment_identity.evidence_text,
        },
        "document": {
            "title": paper_cov.document_title,
            "source": paper_cov.document_source,
        },
        "metrics": {
            "total_questions": paper_cov.total_questions,
            "mapped_questions": paper_cov.mapped_questions_count,
            "unmapped_questions": paper_cov.unmapped_questions_count,
        },
        "observed_units": paper_cov.observed_unit_numbers,
        "observed_topics": paper_cov.observed_topic_names,
        "question_count_by_unit": paper_cov.question_count_by_unit,
        "marks_by_unit": paper_cov.marks_by_unit,
        "question_lineage": audit_questions,
    }
