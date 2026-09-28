"""
Deterministic Examination Blueprint Extraction & Normalization Layer for MintAI.

Discovers recurring structural examination templates strictly from empirical corpus evidence.
Represents observed paper architecture (sections, question counts, marks, choice evidence),
without probabilistic speculation or inferred institutional intent.
"""

from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, ConfigDict

from backend.services.assessment_cycle import normalize_assessment_cycle
from backend.services.cognitive_demand_classifier import DeterministicCognitiveDemandClassifier


class SectionChoiceType(str, Enum):
    COMPULSORY = "COMPULSORY"
    UNITARY_CHOICE = "UNITARY_CHOICE"
    SELECTIVE_CHOICE = "SELECTIVE_CHOICE"
    UNSPECIFIED = "UNSPECIFIED"


class BlueprintStatus(str, Enum):
    DOMINANT_STRUCTURE = "DOMINANT_STRUCTURE"
    RECURRING_STRUCTURE = "RECURRING_STRUCTURE"
    SINGLE_OBSERVED_STRUCTURE = "SINGLE_OBSERVED_STRUCTURE"
    STRUCTURAL_VARIANT = "STRUCTURAL_VARIANT"


class SectionBlueprint(BaseModel):
    model_config = ConfigDict(extra="ignore")

    section_id: Optional[Any] = None
    raw_name: str
    name: str  # Normalized canonical name: PART_A, PART_B, PART_C, MODULE_N, DEFAULT
    sequence: int  # 1-indexed relative section order
    instructions: Optional[str] = None
    choice_type: str = SectionChoiceType.UNSPECIFIED.value
    choice_detail: Optional[str] = None
    total_questions: int
    primary_questions_count: int
    alternative_questions_count: int
    has_internal_choice: bool
    internal_choice_pairs: int
    question_number_range: Optional[str] = None
    marks_per_question: List[float] = Field(default_factory=list)
    scored_marks_sum: float
    total_offered_marks: float
    has_unscored_questions: bool
    unscored_questions_count: int
    question_types: Dict[str, int] = Field(default_factory=dict)
    unit_distribution: Dict[str, int] = Field(default_factory=dict)
    cognitive_demand_distribution: Dict[str, int] = Field(default_factory=dict)


class ExamBlueprint(BaseModel):
    model_config = ConfigDict(extra="ignore")

    exam_id: Any
    course_id: Any
    year: Optional[int] = None
    assessment_cycle: str  # ENDSEM, CT1, CT2, ALL, etc.
    raw_assessment_type: Optional[str] = None
    section_count: int
    total_questions: int
    primary_questions: int
    alternative_questions: int
    total_scored_marks: float
    total_offered_marks: float
    has_unscored_questions: bool
    sections: List[SectionBlueprint] = Field(default_factory=list)
    structural_signature: str


class BlueprintCluster(BaseModel):
    model_config = ConfigDict(extra="ignore")

    signature: str
    label: str
    matching_paper_count: int
    percentage_of_cycle: float
    years_observed: List[int] = Field(default_factory=list)
    assessment_cycles_observed: List[str] = Field(default_factory=list)
    first_observed_year: Optional[int] = None
    latest_observed_year: Optional[int] = None
    exam_ids: List[Any] = Field(default_factory=list)
    status: str
    is_dominant: bool
    is_sparse: bool
    representative_blueprint: ExamBlueprint


class CycleAssessmentBlueprints(BaseModel):
    model_config = ConfigDict(extra="ignore")

    course_id: int
    assessment_cycle: str
    total_cycle_papers: int
    unique_blueprints_count: int
    dominant_signature: Optional[str] = None
    clusters: List[BlueprintCluster] = Field(default_factory=list)


class CourseAssessmentBlueprints(BaseModel):
    model_config = ConfigDict(extra="ignore")

    course_id: int
    course_name: Optional[str] = None
    total_papers_analyzed: int
    cycles: Dict[str, CycleAssessmentBlueprints] = Field(default_factory=dict)


class BlueprintExtractor:
    """Deterministic extractor and normalizer of historical exam blueprints."""

    @classmethod
    def normalize_section_name(cls, raw_name: Optional[str]) -> str:
        """
        Deterministically map raw section names to canonical identifiers:
        PART_A, PART_B, PART_C, MODULE_1..MODULE_N, or DEFAULT.
        """
        if not raw_name:
            return "DEFAULT"
        n = raw_name.upper().strip()

        # Part A patterns
        if re.search(r'\bPART\s*[-–—_]?\s*A\b|\bSECTION\s*A\b', n):
            return "PART_A"
        # Part B patterns
        if re.search(r'\bPART\s*[-–—_]?\s*B\b|\bSECTION\s*B\b', n):
            return "PART_B"
        # Part C patterns
        if re.search(r'\bPART\s*[-–—_]?\s*C\b|\bSECTION\s*C\b', n):
            return "PART_C"

        # Module patterns
        m_roman = re.search(r'\b(?:MODULE|UNIT)\s*[-–—_]?\s*(I|II|III|IV|V|VI|VII|VIII|IX|X)\b', n)
        if m_roman:
            roman_to_int = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
            val = roman_to_int.get(m_roman.group(1), 1)
            return f"MODULE_{val}"

        m_num = re.search(r'\b(?:MODULE|UNIT)\s*[-–—_]?\s*([0-9]+)\b', n)
        if m_num:
            return f"MODULE_{m_num.group(1)}"

        # Default / Main / Single unsegmented paper
        if any(token in n for token in ["DEFAULT", "MAIN", "SECTION"]):
            return "DEFAULT"

        # Fallback to cleaned alphanumeric token
        cleaned = re.sub(r'[^A-Z0-9_]', '_', n).strip('_')
        return cleaned or "DEFAULT"

    @classmethod
    def parse_choice_type(cls, instructions: Optional[str]) -> Tuple[str, Optional[str]]:
        """
        Parse explicit choice directives strictly from instruction text.
        Never infers choice type if instructions are absent.
        """
        if not instructions or not instructions.strip():
            return SectionChoiceType.UNSPECIFIED.value, None

        text = instructions.upper().strip()

        # Compulsory: "Answer ALL Questions", "Answer all the questions"
        if re.search(r'\b(?:ANSWER\s+ALL|ANSWER\s+ALL\s+THE\s+QUESTIONS|ANSWER\s+ALL\s+QUESTIONS)\b', text):
            return SectionChoiceType.COMPULSORY.value, "Answer ALL Questions"

        # Unitary choice: "Answer ANY ONE Question", "Answer any 1 Questions"
        if re.search(r'\b(?:ANSWER\s+ANY\s+ONE|ANSWER\s+ANY\s+1)\b', text):
            return SectionChoiceType.UNITARY_CHOICE.value, "Answer ANY ONE Question"

        # Selective choice: "Answer ANY FIVE Questions", "Answer any 4 Questions"
        m_sel = re.search(r'\bANSWER\s+ANY\s+([0-9]+|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT)\b', text)
        if m_sel:
            num_word = m_sel.group(1)
            word_map = {"TWO": "2", "THREE": "3", "FOUR": "4", "FIVE": "5", "SIX": "6", "SEVEN": "7", "EIGHT": "8"}
            num_clean = word_map.get(num_word, num_word)
            return SectionChoiceType.SELECTIVE_CHOICE.value, f"Answer ANY {num_clean} Questions"

        return SectionChoiceType.UNSPECIFIED.value, None

    @classmethod
    def extract_section_blueprint(
        cls,
        section_id: Optional[int],
        raw_name: str,
        instructions: Optional[str],
        questions: List[Dict[str, Any]],
        sequence: int
    ) -> SectionBlueprint:
        """
        Extract normalized structural representation of a single examination section.
        """
        norm_name = cls.normalize_section_name(raw_name)
        choice_type, choice_detail = cls.parse_choice_type(instructions)

        total_q = len(questions)
        primary_qs: List[Dict[str, Any]] = []
        alt_qs: List[Dict[str, Any]] = []

        q_num_ints: List[int] = []
        q_num_strs: List[str] = []
        number_collisions = Counter()

        for q in questions:
            is_alt = bool(q.get("is_alternative"))
            if is_alt:
                alt_qs.append(q)
            else:
                primary_qs.append(q)

            raw_num = q.get("question_number")
            if raw_num is not None:
                s_num = str(raw_num).strip()
                q_num_strs.append(s_num)
                # match integer part
                m = re.match(r'^([0-9]+)', s_num)
                if m:
                    base_int = int(m.group(1))
                    q_num_ints.append(base_int)
                    number_collisions[base_int] += 1

        # Internal choice detection: explicit alternative flags OR duplicate question numbers
        duplicate_pairs_count = sum(1 for cnt in number_collisions.values() if cnt > 1)
        alt_count = len(alt_qs)
        has_internal_choice = alt_count > 0 or duplicate_pairs_count > 0
        internal_choice_pairs = max(alt_count, duplicate_pairs_count)

        if has_internal_choice and choice_type == SectionChoiceType.UNSPECIFIED.value:
            choice_type = SectionChoiceType.COMPULSORY.value
            choice_detail = f"{internal_choice_pairs} pairs with internal choice"
        elif has_internal_choice and choice_type == SectionChoiceType.COMPULSORY.value:
            choice_detail = f"Answer ALL ({internal_choice_pairs} internal choice pairs)"

        # Question Number Range
        q_range = None
        if q_num_ints:
            min_num = min(q_num_ints)
            max_num = max(q_num_ints)
            q_range = f"{min_num}-{max_num}" if min_num != max_num else str(min_num)
        elif q_num_strs:
            q_range = f"{q_num_strs[0]}-{q_num_strs[-1]}" if len(q_num_strs) > 1 else q_num_strs[0]

        # Marks Accounting
        unscored_count = 0
        marks_set: Set[float] = set()
        scored_marks_sum = 0.0
        total_offered_marks = 0.0

        for q in questions:
            m = q.get("marks")
            if m is None:
                unscored_count += 1
            else:
                m_val = float(m)
                total_offered_marks += m_val
                if not q.get("is_alternative"):
                    scored_marks_sum += m_val
                    marks_set.add(m_val)

        has_unscored = unscored_count > 0
        marks_per_q = sorted(list(marks_set))

        # Question Types Distribution
        qtypes: Dict[str, int] = defaultdict(int)
        for q in questions:
            qt = q.get("question_type") or "Other / Unclassified"
            qtypes[qt] += 1

        # Unit Distribution
        units_dist: Dict[str, int] = defaultdict(int)
        for q in questions:
            # Check unit_objects or unit
            u_name = None
            if q.get("unit_objects"):
                u_name = q["unit_objects"][0].get("name")
            elif q.get("unit"):
                u_name = str(q["unit"])
            elif q.get("units"):
                u_name = str(q["units"][0])

            label = u_name if u_name else "Unmapped / Unknown"
            units_dist[label] += 1

        # Cognitive Demand Distribution
        demand_dist: Dict[str, int] = defaultdict(int)
        for q in questions:
            q_txt = q.get("original_text") or q.get("text") or q.get("normalized_text") or ""
            res = DeterministicCognitiveDemandClassifier.classify(
                text=q_txt,
                question_type=q.get("question_type"),
                structured_content=q.get("structured_content"),
                marks=q.get("marks")
            )
            demand_dist[res.demand.value] += 1

        return SectionBlueprint(
            section_id=section_id,
            raw_name=raw_name,
            name=norm_name,
            sequence=sequence,
            instructions=instructions,
            choice_type=choice_type,
            choice_detail=choice_detail,
            total_questions=total_q,
            primary_questions_count=len(primary_qs),
            alternative_questions_count=alt_count,
            has_internal_choice=has_internal_choice,
            internal_choice_pairs=internal_choice_pairs,
            question_number_range=q_range,
            marks_per_question=marks_per_q,
            scored_marks_sum=round(scored_marks_sum, 2),
            total_offered_marks=round(total_offered_marks, 2),
            has_unscored_questions=has_unscored,
            unscored_questions_count=unscored_count,
            question_types=dict(qtypes),
            unit_distribution=dict(units_dist),
            cognitive_demand_distribution=dict(demand_dist)
        )

    @classmethod
    def extract_exam_blueprint(
        cls,
        exam_id: int,
        course_id: int,
        year: Optional[int],
        raw_assessment_type: Optional[str],
        sections_data: List[Dict[str, Any]]
    ) -> ExamBlueprint:
        """
        Extract the structural blueprint for a single examination paper.
        """
        cycle = normalize_assessment_cycle(raw_assessment_type) or "ALL"

        sec_blueprints: List[SectionBlueprint] = []
        for idx, sec in enumerate(sections_data, start=1):
            s_bp = cls.extract_section_blueprint(
                section_id=sec.get("id"),
                raw_name=sec.get("name") or f"Section {idx}",
                instructions=sec.get("instructions"),
                questions=sec.get("questions", []),
                sequence=idx
            )
            sec_blueprints.append(s_bp)

        total_questions = sum(s.total_questions for s in sec_blueprints)
        primary_questions = sum(s.primary_questions_count for s in sec_blueprints)
        alternative_questions = sum(s.alternative_questions_count for s in sec_blueprints)
        total_scored_marks = sum(s.scored_marks_sum for s in sec_blueprints)
        total_offered_marks = sum(s.total_offered_marks for s in sec_blueprints)
        has_unscored = any(s.has_unscored_questions for s in sec_blueprints)

        # Structural Signature Construction: encodes ONLY structural features
        # Format: {NAME}({total_q}Q,alts={alts},m={marks},choice={choice})
        sig_parts = []
        for s in sec_blueprints:
            m_str = "/".join(str(m) for m in s.marks_per_question) if s.marks_per_question else "unscored"
            sig_parts.append(
                f"{s.name}({s.total_questions}Q,alts={s.alternative_questions_count},m={m_str},choice={s.choice_type})"
            )
        signature = " + ".join(sig_parts) if sig_parts else "NO_SECTIONS"

        return ExamBlueprint(
            exam_id=exam_id,
            course_id=course_id,
            year=year,
            assessment_cycle=cycle,
            raw_assessment_type=raw_assessment_type,
            section_count=len(sec_blueprints),
            total_questions=total_questions,
            primary_questions=primary_questions,
            alternative_questions=alternative_questions,
            total_scored_marks=round(total_scored_marks, 2),
            total_offered_marks=round(total_offered_marks, 2),
            has_unscored_questions=has_unscored,
            sections=sec_blueprints,
            structural_signature=signature
        )

    @classmethod
    def generate_human_label(cls, blueprint: ExamBlueprint) -> str:
        """
        Generate a clear, human-readable structural summary of the blueprint.
        e.g., '3-Section Template: Part A (20x1m), Part B (5 pairs x 8m), Part C (2x15m)'
        """
        if not blueprint.sections:
            return "Unstructured / No Sections Recorded"

        sec_labels = []
        for s in blueprint.sections:
            m_str = f"{s.marks_per_question[0]}m" if len(s.marks_per_question) == 1 else (
                f"{'/'.join(str(m) for m in s.marks_per_question)}m" if s.marks_per_question else "unscored"
            )

            if s.has_internal_choice and s.internal_choice_pairs > 0:
                sec_desc = f"{s.name.replace('_', ' ')}: {s.internal_choice_pairs} choice pairs ({s.total_questions}Q × {m_str})"
            else:
                sec_desc = f"{s.name.replace('_', ' ')}: {s.total_questions}Q × {m_str}"
            sec_labels.append(sec_desc)

        return f"{blueprint.section_count}-Section Structure: " + ", ".join(sec_labels)

    @classmethod
    def cluster_blueprints(
        cls,
        blueprints: List[ExamBlueprint]
    ) -> List[BlueprintCluster]:
        """
        Group individual exam blueprints by identical structural signatures.
        Classifies status as DOMINANT, RECURRING, SINGLE, or VARIANT.
        """
        if not blueprints:
            return []

        sig_groups: Dict[str, List[ExamBlueprint]] = defaultdict(list)
        for bp in blueprints:
            sig_groups[bp.structural_signature].append(bp)

        total_papers = len(blueprints)
        clusters: List[BlueprintCluster] = []

        # Find maximum count to identify dominant structure
        max_count = max(len(bps) for bps in sig_groups.values()) if sig_groups else 0

        for sig, bps in sig_groups.items():
            count = len(bps)
            pct = round((count / total_papers) * 100.0, 2)
            years = sorted(list(set(b.year for b in bps if b.year is not None)))
            cycles = sorted(list(set(b.assessment_cycle for b in bps if b.assessment_cycle)))
            first_y = min(years) if years else None
            latest_y = max(years) if years else None
            exam_ids = [b.exam_id for b in bps]

            is_dominant = (count == max_count and count >= 2)
            is_sparse = (count == 1)

            if is_dominant:
                status = BlueprintStatus.DOMINANT_STRUCTURE.value
            elif count >= 2:
                status = BlueprintStatus.RECURRING_STRUCTURE.value
            elif max_count >= 2:
                status = BlueprintStatus.STRUCTURAL_VARIANT.value
            else:
                status = BlueprintStatus.SINGLE_OBSERVED_STRUCTURE.value

            rep_bp = bps[0]
            label = cls.generate_human_label(rep_bp)

            clusters.append(
                BlueprintCluster(
                    signature=sig,
                    label=label,
                    matching_paper_count=count,
                    percentage_of_cycle=pct,
                    years_observed=years,
                    assessment_cycles_observed=cycles,
                    first_observed_year=first_y,
                    latest_observed_year=latest_y,
                    exam_ids=exam_ids,
                    status=status,
                    is_dominant=is_dominant,
                    is_sparse=is_sparse,
                    representative_blueprint=rep_bp
                )
            )

        # Sort clusters: dominant first, then by matching paper count desc, then signature
        clusters.sort(key=lambda c: (-c.matching_paper_count, c.signature))
        return clusters

    @classmethod
    def extract_from_exam_model(cls, exam: Any, course_id: int) -> ExamBlueprint:
        """
        Extract blueprint directly from a SQLAlchemy Exam ORM model.
        """
        sections_data: List[Dict[str, Any]] = []
        for sec in getattr(exam, "sections", []):
            q_list: List[Dict[str, Any]] = []
            for q in getattr(sec, "questions", []):
                q_dict = {
                    "id": q.id,
                    "question_number": q.question_number,
                    "marks": q.marks,
                    "is_alternative": q.is_alternative,
                    "question_type": getattr(q, "question_type", "Other / Unclassified"),
                    "unit": None,
                    "units": [],
                    "unit_objects": []
                }
                if getattr(q, "topics", None):
                    units_seen = []
                    for t in q.topics:
                        if getattr(t, "unit", None) and t.unit.name:
                            units_seen.append({
                                "id": t.unit.id,
                                "name": t.unit.name,
                                "number": t.unit.number
                            })
                    q_dict["unit_objects"] = units_seen
                q_list.append(q_dict)

            sections_data.append({
                "id": sec.id,
                "name": sec.name,
                "instructions": sec.instructions,
                "questions": q_list
            })

        return cls.extract_exam_blueprint(
            exam_id=exam.id,
            course_id=course_id,
            year=exam.year,
            raw_assessment_type=exam.assessment_type,
            sections_data=sections_data
        )

    @classmethod
    def extract_course_blueprints_from_db(
        cls,
        course_id: int,
        db: Any,
        cutoff_year: Optional[int] = None,
        track_id: Optional[int] = None
    ) -> CourseAssessmentBlueprints:
        """
        Load all exams for a course and extract multi-cycle blueprint intelligence.
        """
        from sqlalchemy.orm import selectinload
        from backend.models.core import Exam, Section, Question, Topic, Course

        course_obj = db.get(Course, course_id) if hasattr(db, "get") else db.query(Course).get(course_id)
        course_name = course_obj.name if course_obj else f"Course {course_id}"

        query = (
            db.query(Exam)
            .options(
                selectinload(Exam.sections)
                .selectinload(Section.questions)
                .selectinload(Question.topics)
                .selectinload(Topic.unit)
            )
            .filter(Exam.course_id == course_id)
        )
        if track_id is not None:
            query = query.filter(Exam.track_id == track_id)
        if cutoff_year is not None:
            query = query.filter(Exam.year < cutoff_year)

        exams = query.order_by(Exam.year.asc(), Exam.id.asc()).all()

        # Group by assessment cycle
        cycle_bps: Dict[str, List[ExamBlueprint]] = defaultdict(list)
        for ex in exams:
            bp = cls.extract_from_exam_model(ex, course_id=course_id)
            cycle_bps[bp.assessment_cycle].append(bp)

        cycles_result: Dict[str, CycleAssessmentBlueprints] = {}
        for cycle, bps in cycle_bps.items():
            clusters = cls.cluster_blueprints(bps)
            dom_sig = clusters[0].signature if (clusters and clusters[0].is_dominant) else None
            cycles_result[cycle] = CycleAssessmentBlueprints(
                course_id=course_id,
                assessment_cycle=cycle,
                total_cycle_papers=len(bps),
                unique_blueprints_count=len(clusters),
                dominant_signature=dom_sig,
                clusters=clusters
            )

        return CourseAssessmentBlueprints(
            course_id=course_id,
            course_name=course_name,
            total_papers_analyzed=len(exams),
            cycles=cycles_result
        )
