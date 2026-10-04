"""
MintAI Question Generator Service.
Provides syllabus-grounded and historical-evidence-grounded exam practice questions.

Guarantees:
1. Strict Provenance Distinguishability:
   Historical questions (from verified SRM past papers) and synthetic fallback questions
   are always strictly distinguished with unambiguous provenance metadata.
2. Temporal Isolation:
   If cutoff_year is specified, only exams strictly prior to cutoff_year are eligible.
3. Course and Track Isolation:
   Historical retrieval respects course_id and track_id boundaries without leakage.
4. Truthful Representation:
   Synthetic questions are NEVER marked as historical PYQs and include explicit disclaimers.
"""

import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from backend.models.core import Course, Exam, Section, Question, Topic, QuestionFamily, question_topic
from backend.services.assessment_cycle import normalize_assessment_cycle, filter_exams_by_cycle


class GeneratedQuestionItem(BaseModel):
    type: str  # "MCQ" | "SHORT" | "LONG" | "SPLIT"
    marks: str
    text: str
    options: Optional[List[str]] = None
    provenance: str  # "HISTORICAL_EVIDENCE" | "SYNTHETIC_SYLLABUS_FALLBACK"
    is_synthetic: bool
    exam_year: Optional[int] = None
    source_label: str


class QuestionGenerationResponse(BaseModel):
    topic: str
    course_id: Optional[int] = None
    track_id: Optional[int] = None
    provenance: str  # "HISTORICAL_EVIDENCE" | "SYNTHETIC_SYLLABUS_FALLBACK"
    is_synthetic: bool
    evidence_count: int
    questions: List[GeneratedQuestionItem]
    disclaimer: Optional[str] = None


class QuestionGeneratorService:
    @staticmethod
    def _sanitize_string(val: Optional[str], max_len: int = 256) -> str:
        if not val:
            return ""
        cleaned = re.sub(r"[\x00-\x1f\x7f]", "", str(val)).strip()
        return cleaned[:max_len]

    @classmethod
    def generate_questions(
        cls,
        db: Session,
        topic: str,
        course_id: Optional[int] = None,
        track_id: Optional[int] = None,
        cycle: Optional[str] = "ALL",
        cutoff_year: Optional[int] = None,
    ) -> QuestionGenerationResponse:
        sanitized_topic = cls._sanitize_string(topic, max_len=200)
        if not sanitized_topic:
            sanitized_topic = "General Engineering Principles"

        # 1. Attempt historical evidence retrieval if course_id is provided
        historical_questions: List[Dict[str, Any]] = []
        if course_id:
            historical_questions = cls._find_historical_questions(
                db=db,
                topic=sanitized_topic,
                course_id=course_id,
                track_id=track_id,
                cycle=cycle,
                cutoff_year=cutoff_year,
            )

        # 2. If historical evidence exists, format and return verified questions
        if historical_questions:
            formatted_qs = cls._format_historical_questions(historical_questions, sanitized_topic)
            return QuestionGenerationResponse(
                topic=sanitized_topic,
                course_id=course_id,
                track_id=track_id,
                provenance="HISTORICAL_EVIDENCE",
                is_synthetic=False,
                evidence_count=len(historical_questions),
                questions=formatted_qs,
                disclaimer="Questions retrieved directly from verified historical university examination records.",
            )

        # 3. Fallback: Generate syllabus-derived synthetic practice questions
        synthetic_qs = cls._generate_synthetic_fallback(sanitized_topic)
        return QuestionGenerationResponse(
            topic=sanitized_topic,
            course_id=course_id,
            track_id=track_id,
            provenance="SYNTHETIC_SYLLABUS_FALLBACK",
            is_synthetic=True,
            evidence_count=0,
            questions=synthetic_qs,
            disclaimer="These practice questions are AI-generated based on the syllabus taxonomy. They do not represent verified past exam papers.",
        )

    @classmethod
    def _find_historical_questions(
        cls,
        db: Session,
        topic: str,
        course_id: int,
        track_id: Optional[int] = None,
        cycle: Optional[str] = "ALL",
        cutoff_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query official historical exam questions mapped to topic or family for course."""
        query = (
            db.query(Question, Exam.year, Exam.assessment_type)
            .select_from(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == course_id)
        )

        # Temporal isolation
        if cutoff_year is not None:
            query = query.filter(Exam.year < cutoff_year, Exam.year > 0)
        else:
            query = query.filter(Exam.year > 0)

        # Track isolation
        if track_id is not None:
            query = query.filter(Exam.track_id == track_id)

        # Assessment cycle filter
        norm_cycle = normalize_assessment_cycle(cycle)
        if norm_cycle and norm_cycle != "ALL":
            query = filter_exams_by_cycle(query, Exam.assessment_type, norm_cycle, course_id=course_id)

        # Topic match via Question.topics or QuestionFamily canonical name
        topic_lower = topic.strip().lower()
        search_terms = {topic_lower}
        if topic_lower.endswith("ices"):
            search_terms.add(topic_lower[:-4] + "ix")
        elif topic_lower.endswith("ies") and len(topic_lower) > 4:
            search_terms.add(topic_lower[:-3] + "y")
        elif topic_lower.endswith("s") and len(topic_lower) > 3:
            search_terms.add(topic_lower[:-1])

        # Also include significant words from multi-word topics
        words = [w for w in re.split(r"\W+", topic_lower) if len(w) > 3]
        for w in words:
            search_terms.add(w)
            if w.endswith("ices"):
                search_terms.add(w[:-4] + "ix")
            elif w.endswith("ies") and len(w) > 4:
                search_terms.add(w[:-3] + "y")
            elif w.endswith("s") and len(w) > 3:
                search_terms.add(w[:-1])

        from sqlalchemy import or_

        topic_conditions = [Topic.name.ilike(f"%{st}%") for st in search_terms]
        topic_query = (
            query
            .join(Question.topics)
            .filter(or_(*topic_conditions))
            .order_by(Exam.year.desc(), Question.marks.desc())
            .limit(10)
            .all()
        )

        results: List[Dict[str, Any]] = []
        for q, year, a_type in topic_query:
            results.append({
                "id": q.id,
                "text": q.original_text,
                "marks": q.marks or 4.0,
                "year": year,
                "assessment_type": a_type,
                "question_type": q.question_type or "THEORETICAL",
            })

        if not results:
            # Fallback to family canonical name matching
            family_conditions = [QuestionFamily.canonical_name.ilike(f"%{st}%") for st in search_terms]
            family_query = (
                query
                .join(Question.family)
                .filter(or_(*family_conditions))
                .order_by(Exam.year.desc(), Question.marks.desc())
                .limit(10)
                .all()
            )
            for q, year, a_type in family_query:
                results.append({
                    "id": q.id,
                    "text": q.original_text,
                    "marks": q.marks or 4.0,
                    "year": year,
                    "assessment_type": a_type,
                    "question_type": q.question_type or "THEORETICAL",
                })

        return results

    @classmethod
    def _format_historical_questions(
        cls,
        raw_questions: List[Dict[str, Any]],
        topic_name: str,
    ) -> List[GeneratedQuestionItem]:
        items: List[GeneratedQuestionItem] = []
        seen_texts = set()

        for q in raw_questions:
            clean_text = q["text"].strip()
            if clean_text in seen_texts or len(clean_text) < 10:
                continue
            seen_texts.add(clean_text)

            marks_val = q["marks"]
            if marks_val <= 2:
                q_type = "MCQ"
                marks_str = f"{int(marks_val)} Mark" if marks_val == 1 else f"{int(marks_val)} Marks"
            elif marks_val <= 5:
                q_type = "SHORT"
                marks_str = f"{int(marks_val)} Marks"
            elif marks_val <= 10:
                q_type = "LONG"
                marks_str = f"{int(marks_val)} Marks"
            else:
                q_type = "SPLIT"
                marks_str = f"{int(marks_val)} Marks"

            items.append(
                GeneratedQuestionItem(
                    type=q_type,
                    marks=marks_str,
                    text=clean_text,
                    options=None,
                    provenance="HISTORICAL_EVIDENCE",
                    is_synthetic=False,
                    exam_year=q["year"],
                    source_label=f"Verified Historical SRM Exam ({q['year']})",
                )
            )
            if len(items) >= 4:
                break

        return items

    @classmethod
    def _generate_synthetic_fallback(cls, topic_name: str) -> List[GeneratedQuestionItem]:
        """
        Generate structured syllabus practice questions derived strictly from the topic title.
        Always marked with is_synthetic=True and SYNTHETIC_SYLLABUS_FALLBACK provenance.
        """
        lower = topic_name.lower()
        items: List[GeneratedQuestionItem] = []

        is_split = len(topic_name) % 2 == 0

        if any(k in lower for k in ["calculus", "math", "matrix", "eigen", "vector", "transform", "probability", "statistics"]):
            items = [
                GeneratedQuestionItem(
                    type="MCQ",
                    marks="1 Mark",
                    text=f"For a system governed by {topic_name}, which mathematical property is fundamentally preserved under linear transformation?",
                    options=["Orthogonality", "Determinant value", "Trace invariance", "All of the above depending on transformation matrix"],
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
                GeneratedQuestionItem(
                    type="SHORT",
                    marks="4 Marks",
                    text=f"State the primary definition and governing mathematical conditions for {topic_name}. Give one practical engineering scenario where it is applied.",
                    options=None,
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
                GeneratedQuestionItem(
                    type="SPLIT" if is_split else "LONG",
                    marks="13 Marks (7+6)" if is_split else "13 Marks",
                    text=(
                        f"(a) [7 Marks] Formulate the analytical derivation for {topic_name} starting from first principles.\n\n"
                        f"(b) [6 Marks] Solve the boundary value problem associated with {topic_name} under standard operational constraints."
                    ) if is_split else (
                        f"Provide a rigorous mathematical analysis of {topic_name}. Derive the governing equations and demonstrate step-by-step resolution for a standard test case."
                    ),
                    options=None,
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
            ]
        elif any(k in lower for k in ["algorithm", "data structure", "tree", "sort", "graph", "search", "complexity"]):
            items = [
                GeneratedQuestionItem(
                    type="MCQ",
                    marks="1 Mark",
                    text=f"What is the standard asymptotic time complexity for the fundamental operation in {topic_name}?",
                    options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
                GeneratedQuestionItem(
                    type="SHORT",
                    marks="4 Marks",
                    text=f"Explain the design logic and pseudocode of {topic_name}. Outline its auxiliary space requirements.",
                    options=None,
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
                GeneratedQuestionItem(
                    type="SPLIT" if is_split else "LONG",
                    marks="13 Marks (7+6)" if is_split else "13 Marks",
                    text=(
                        f"(a) [7 Marks] Compare {topic_name} against alternative approaches in terms of cache efficiency and worst-case bounds.\n\n"
                        f"(b) [6 Marks] Trace the algorithm step-by-step on a representative input and justify its correctness."
                    ) if is_split else (
                        f"Implement and analyze {topic_name} in detail. Provide complete structural implementation, discuss edge cases, and evaluate performance trade-offs."
                    ),
                    options=None,
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
            ]
        else:
            # General engineering taxonomy fallback
            items = [
                GeneratedQuestionItem(
                    type="MCQ",
                    marks="1 Mark",
                    text=f"Which fundamental principle or law directly underpins {topic_name} in modern engineering systems?",
                    options=["Conservation Law", "Constitutive Relation", "Equilibrium Principle", "System Optimization Criterion"],
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
                GeneratedQuestionItem(
                    type="SHORT",
                    marks="4 Marks",
                    text=f"Define {topic_name} concisely. List two distinct practical applications in modern industry and their key engineering constraints.",
                    options=None,
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
                GeneratedQuestionItem(
                    type="SPLIT" if is_split else "LONG",
                    marks="13 Marks (7+6)" if is_split else "13 Marks",
                    text=(
                        f"(a) [7 Marks] Explain the theoretical architecture and operating mechanism of {topic_name} with a neat, labeled diagram.\n\n"
                        f"(b) [6 Marks] Discuss key design considerations, failure modes, and mitigation strategies for {topic_name}."
                    ) if is_split else (
                        f"Conduct a comprehensive technical review of {topic_name}. Detail the foundational equations, operational workflow, and real-world system integration."
                    ),
                    options=None,
                    provenance="SYNTHETIC_SYLLABUS_FALLBACK",
                    is_synthetic=True,
                    exam_year=None,
                    source_label="Syllabus Taxonomy Practice (Synthetic)",
                ),
            ]

        return items
