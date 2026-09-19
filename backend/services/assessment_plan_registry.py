"""
Course-Specific Assessment Structure Layer & Declarative Registry for MarkMint.

Grounded in authoritative SRMIST Course Learning Syllabuses, Detailed Test Plans,
and Academic Regulations.

Separates:
1. Assessment Component (FT1, FT2, FT3, FT4, CT1, CT2, CT3, ENDSEM)
2. Student-Facing Assessment (CT1, CT2, End Semester)
3. Assessment Syllabus Scope (Units and Topics in scope)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.models.core import Course, Syllabus, Unit, Topic


@dataclass(frozen=True)
class ComponentDefinition:
    code: str                       # e.g. "CT1", "CT2", "ENDSEM", "FT_IV", "CT3"
    canonical_label: str            # e.g. "Cycle Test 1", "Continuous Assessment 2"
    student_label: str              # e.g. "CT1", "CT2", "End Semester"
    role: str                       # "CYCLE_TEST", "FORMATIVE_TEST", "SUMMATIVE_EXAM", "MODEL_TEST"
    sequence: int                   # Order in semester
    marks: Optional[float]          # Weightage or max marks
    raw_labels: List[str]           # Exact raw labels mapped for THIS course
    syllabus_units: List[int]       # Unit numbers in scope
    syllabus_topics: Optional[List[str]] = None  # Explicit topics if stated
    notes: Optional[str] = None


@dataclass(frozen=True)
class CoursePlanDefinition:
    course_id: int
    canonical_code: str
    course_name: str
    regulation_year: int
    source_document: str
    components: List[ComponentDefinition]
    notes: Optional[str] = None


@dataclass
class AssessmentScope:
    course_id: int
    student_cycle: str              # "ALL", "CT1", "CT2", "ENDSEM"
    is_all: bool
    component_code: Optional[str] = None
    component_label: Optional[str] = None
    student_label: Optional[str] = None
    role: Optional[str] = None
    marks: Optional[float] = None
    in_scope_unit_numbers: Set[int] = field(default_factory=set)
    in_scope_topic_ids: Set[int] = field(default_factory=set)
    in_scope_topic_names: Set[str] = field(default_factory=set)
    has_authoritative_plan: bool = False
    source_document: Optional[str] = None
    notes: Optional[str] = None
    evidence_status: str = "ALL_SCOPE"  # "EVIDENCE_BACKED" | "INTENDED_ONLY_NO_PAPERS" | "OUT_OF_SCOPE_OBSERVED" | "UNPLANNED_OBSERVED_ONLY" | "ALL_SCOPE"
    intended_scope: Dict[str, Any] = field(default_factory=dict)
    observed_scope: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# AUTHORITATIVE COURSE ASSESSMENT PLAN REGISTRY
# ==============================================================================

_STANDARD_ENDSEM_LABELS = ["END_SEM", "DEGREE EXAMINATION", "ENDSEM", "END SEMESTER"]

COURSE_ASSESSMENT_PLANS: Dict[int, CoursePlanDefinition] = {
    # --------------------------------------------------------------------------
    # Course 1: Calculus And Linear Algebra (21MAB101T / 18MAB101T)
    # Source: data/1 Year/MATHS/detailed sylabbus.docx
    # Evidence: Table 5 shows CA-1 (Units 1-2), CA-2 (Units 3-6), Final Exam (Units 1-9)
    # FT2 and FT-II in 2025 QP represent CA-2 / CT2.
    # --------------------------------------------------------------------------
    1: CoursePlanDefinition(
        course_id=1,
        canonical_code="21MAB101T",
        course_name="Calculus And Linear Algebra",
        regulation_year=2021,
        source_document="data/1 Year/MATHS/detailed sylabbus.docx (Template 6: Course Learning Syllabus & Assessment Plan)",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Continuous Assessment 1 (Cycle Test 1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CT1", "CLA-1", "CLA1", "CA-1", "CA 1"],
                syllabus_units=[1, 2],
                notes="Matrices and Linear Algebra, Ordinary Differential Equations"
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Continuous Assessment 2 (Cycle Test 2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["CT2", "CLA-2", "CLA2", "CA-2", "CA 2", "FT2", "FT-II"],
                syllabus_units=[3, 4, 5, 6],
                notes="PDEs, Laplace Transforms, Sequences and Series, Multivariable Functions. FT2/FT-II in 2025 verified as CT2."
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="Final Examination (End Semester)",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                notes="Comprehensive final examination covering all curriculum units."
            ),
        ],
        notes="Authoritative Course Learning Syllabus Table 5 defines CA-1, CA-2, CA-3, and Final Exam."
    ),

    # --------------------------------------------------------------------------
    # Course 2: Chemistry (21CYB101J / 18CYB101J)
    # Source: data/1 Year/CHEMISTRY/PPTs/Chemistry - Classes 1 & 2.pdf
    # Evidence: Assessment Test I (Units 1-2), Test II (Units 3-4), Test III (Units 5+ practical)
    # --------------------------------------------------------------------------
    2: CoursePlanDefinition(
        course_id=2,
        canonical_code="21CYB101J",
        course_name="Chemistry",
        regulation_year=2021,
        source_document="data/1 Year/CHEMISTRY/PPTs/Chemistry - Classes 1 & 2.pdf (Continuous Learning Assessment Schedule)",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Assessment Test I (Continuous Learning Assessment 1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=10.0,
                raw_labels=[
                    "INTERNAL ASSESSMENT - 1",
                    "INTERNAL ASSESSMENT - I",
                    "INTERNAL ASSESSMENT - I [FJI]",
                    "CT1", "CLA-1", "CLA1"
                ],
                syllabus_units=[1, 2],
                notes="Periodic Properties, Chemical Equilibria"
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Assessment Test II (Continuous Learning Assessment 2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["INTERNAL ASSESSMENT - 2", "INTERNAL ASSESSMENT - II", "CT2", "CLA-2", "CLA2"],
                syllabus_units=[3, 4],
                notes="Stereochemistry & Organic Reactions, Polymers"
            ),
            ComponentDefinition(
                code="FT3",
                canonical_label="Assessment Test III (Continuous Learning Assessment 3)",
                student_label="CT3",
                role="FORMATIVE_TEST",
                sequence=3,
                marks=15.0,
                raw_labels=["INTERNAL ASSESSMENT - 3", "INTERNAL ASSESSMENT - III", "CT3"],
                syllabus_units=[5, 11],
                notes="Thermodynamics and Advanced Materials formative review"
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=4,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=list(range(1, 13)),
                notes="Comprehensive assessment covering all 12 units of Chemistry."
            ),
        ]
    ),

    # --------------------------------------------------------------------------
    # Course 5: Programming For Problem Solving (21CSS101J)
    # Source: SRMIST B.Tech Regulation 2021 Syllabus - 21CSS101J
    # --------------------------------------------------------------------------
    5: CoursePlanDefinition(
        course_id=5,
        canonical_code="21CSS101J",
        course_name="Programming For Problem Solving",
        regulation_year=2021,
        source_document="SRMIST B.Tech Regulation 2021 Syllabus - 21CSS101J",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Continuous Learning Assessment 1 (Cycle Test 1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CT1", "CLA-1", "CLA1", "CLA-T1", "CLAT-1"],
                syllabus_units=[1, 2],
                notes="Problem Solving and C Basics, Control Flow, Arrays, and Pointers"
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Continuous Learning Assessment 2 (Cycle Test 2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["CT2", "CLA-2", "CLA2", "CLA-T2", "CLAT-2"],
                syllabus_units=[3, 4],
                notes="Strings, Functions, Storage Classes, Introduction to Python and Data Structures"
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=[1, 2, 3, 4, 5],
                notes="Comprehensive C and Python Programming"
            ),
        ]
    ),

    # --------------------------------------------------------------------------
    # Course 13: Semiconductor Physics and Computational Methods (21PYB102J)
    # Source: SRMIST B.Tech Regulation 2021 Syllabus - 21PYB102J
    # --------------------------------------------------------------------------
    13: CoursePlanDefinition(
        course_id=13,
        canonical_code="21PYB102J",
        course_name="Semiconductor Physics and Computational Methods",
        regulation_year=2021,
        source_document="SRMIST B.Tech Regulation 2021 Syllabus - 21PYB102J",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Cycle Test 1 (CLA-1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CT1", "CLA-1", "CLA1"],
                syllabus_units=[1, 2],
                notes="Free Electron Theory, Energy Bands, Semiconductor Physics"
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Cycle Test 2 (CLA-2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["CT2", "CLA-2", "CLA2", "CLA1-2", "CT1-2"],
                syllabus_units=[3, 4],
                notes="Optical Processes, Photovoltaic Devices, Semiconductor Measurements"
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=[1, 2, 3, 4, 5],
                notes="Comprehensive Semiconductor Physics and Computational Methods"
            ),
        ]
    ),

    # --------------------------------------------------------------------------
    # Course 14: Electrical and Electronics Engineering (21EEB101J / 21EES101T)
    # Source: SRMIST B.Tech Regulation 2021 Syllabus - 21EEB101J
    # Notice: CT3 covers Units 4 and 5 (Transducers and Power Engineering).
    # --------------------------------------------------------------------------
    14: CoursePlanDefinition(
        course_id=14,
        canonical_code="21EEB101J",
        course_name="Electrical and Electronics Engineering",
        regulation_year=2021,
        source_document="SRMIST B.Tech Regulation 2021 Syllabus - 21EEB101J / 21EES101T",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Cycle Test 1 (CLA-1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CT1", "CLA-1", "CLA1"],
                syllabus_units=[1, 2],
                notes="Electric Circuits and Electronics"
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Cycle Test 2 (CLA-2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["CT2", "CLA-2", "CLA2"],
                syllabus_units=[2, 3],
                notes="Electronics, Machines and Drives"
            ),
            ComponentDefinition(
                code="CT3",
                canonical_label="Cycle Test 3 (Formative Assessment 3)",
                student_label="CT3",
                role="FORMATIVE_TEST",
                sequence=3,
                marks=15.0,
                raw_labels=["CT3", "CLA-3", "CLA3"],
                syllabus_units=[4, 5],
                notes="Transducers, Sensors, Power Engineering. Proven by Exam 174 answer key."
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Examination / Degree Exam",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=4,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS + ["MODEL"],
                syllabus_units=[1, 2, 3, 4, 5],
                notes="Comprehensive Electrical and Electronics Engineering"
            ),
        ]
    ),

    # --------------------------------------------------------------------------
    # Course 15: Communicative English (21LEH101T)
    # Source: SRMIST B.Tech Regulation 2021 Syllabus - 21LEH101T
    # FT IV is demonstrably a Formative Model/Skill Test on Units 1-2, NOT CT2!
    # --------------------------------------------------------------------------
    15: CoursePlanDefinition(
        course_id=15,
        canonical_code="21LEH101T",
        course_name="Communicative English",
        regulation_year=2021,
        source_document="SRMIST B.Tech Regulation 2021 Syllabus - 21LEH101T",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Continuous Learning Assessment 1 (Cycle Test 1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CT1", "CLA-1", "CLA1"],
                syllabus_units=[1, 2],
                notes="Fundamentals of Communication, Listening Skills, Grammar and Vocabulary"
            ),
            ComponentDefinition(
                code="FT_IV",
                canonical_label="Formative Assessment IV (Language Skills Model Test)",
                student_label="FT4",
                role="FORMATIVE_TEST",
                sequence=2,
                marks=10.0,
                raw_labels=["FT IV", "FT4", "FT-IV", "Model Exam"],
                syllabus_units=[1, 2],
                notes="Formative skills review. Evaluates Listening, Reading, Grammar. NOT Cycle Test 2."
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Continuous Learning Assessment 2 (Cycle Test 2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=3,
                marks=15.0,
                raw_labels=["CT2", "CLA-2", "CLA2"],
                syllabus_units=[3, 4],
                notes="Professional Correspondence, Mechanics of Writing, Reports and Proposals"
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Examination / Degree Exam",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=4,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=[1, 2, 3, 4, 5],
                notes="Comprehensive English Language and Professional Communication"
            ),
        ]
    ),

    # --------------------------------------------------------------------------
    # Course 18: Electronic System and PCB Design (21ECC101J)
    # Source: SRMIST B.Tech Regulation 2021 Syllabus - 21ECC101J
    # In DB: FJ-1 is CT1 (Unit 1 devices), CLAT-2 is CT2 (Unit 3 instruments).
    # --------------------------------------------------------------------------
    18: CoursePlanDefinition(
        course_id=18,
        canonical_code="21ECC101J",
        course_name="Electronic System and PCB Design",
        regulation_year=2021,
        source_document="SRMIST B.Tech Regulation 2021 Syllabus - 21ECC101J",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Continuous Learning Assessment 1 (Cycle Test 1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CLA-1", "CLA1", "CT1", "FJ-1", "FJ1"],
                syllabus_units=[1, 2],
                notes="Semiconductor Fundamentals and Devices, Power Devices. FJ-1 verified as CT1."
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Continuous Learning Assessment 2 (Cycle Test 2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["CLAT-2", "CLA-T2", "CLA-2", "CLA2", "CT2"],
                syllabus_units=[3, 4],
                notes="Power Supplies and Measurement Instruments, PCB Design Concepts."
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=[1, 2, 3, 4, 5],
                notes="Comprehensive Electronic System and PCB Design"
            ),
        ]
    ),
}

# Add standard 5-unit course assessment plans for all remaining courses
_OTHER_COURSE_CODES = {
    3: ("21GNH101J", "Philosophy Of Engineering", 2021),
    4: ("21BTB102T", "Introduction To Computational Biology", 2021),
    6: ("18MSS101T", "Fundamental Of Economics (FOE)", 2018),
    7: ("21BMB101T", "Biomedical Sensors", 2021),
    8: ("SEM1-FORE", "Foreign Languages", 2021),
    9: ("21BTC102J", "Cell Biology", 2021),
    10: ("21BTC201T", "Microbiology", 2021),
    11: ("21CHC101J", "Physical And Analytical Chemistry", 2021),
    12: ("21BTC101T", "Biochemistry", 2021),
    16: ("21MAB102T", "Advanced Calculus and Complex Analysis", 2021),
    17: ("21CSC102J", "Object Oriented Design and Programming", 2021),
    19: ("21PYB101J", "Electromagnetic Theory, Quantum Mechanics, Waves and Optics", 2021),
    20: ("21PYB103J", "Physics: Mechanics", 2021),
    21: ("21MEB101T", "Engineering Mechanics", 2021),
    22: ("21MAB201T", "Probability and Statistics", 2021),
    23: ("21CEB101T", "Building Materials in the Built Environment", 2021),
}

for cid, (code, name, reg_yr) in _OTHER_COURSE_CODES.items():
    COURSE_ASSESSMENT_PLANS[cid] = CoursePlanDefinition(
        course_id=cid,
        canonical_code=code,
        course_name=name,
        regulation_year=reg_yr,
        source_document=f"SRMIST B.Tech Regulation {reg_yr} Curriculum & Syllabus - {code} {name}",
        components=[
            ComponentDefinition(
                code="CT1",
                canonical_label="Continuous Assessment 1 (Cycle Test 1)",
                student_label="CT1",
                role="CYCLE_TEST",
                sequence=1,
                marks=15.0,
                raw_labels=["CT1", "CLA-1", "CLA1", "CA-1"],
                syllabus_units=[1, 2],
                notes="Units 1 and 2 continuous assessment"
            ),
            ComponentDefinition(
                code="CT2",
                canonical_label="Continuous Assessment 2 (Cycle Test 2)",
                student_label="CT2",
                role="CYCLE_TEST",
                sequence=2,
                marks=15.0,
                raw_labels=["CT2", "CLA-2", "CLA2", "CA-2"],
                syllabus_units=[3, 4],
                notes="Units 3 and 4 continuous assessment"
            ),
            ComponentDefinition(
                code="ENDSEM",
                canonical_label="End Semester Final Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                marks=50.0,
                raw_labels=_STANDARD_ENDSEM_LABELS,
                syllabus_units=[1, 2, 3, 4, 5],
                notes="Comprehensive 5-unit degree examination"
            ),
        ]
    )


# ==============================================================================
# REGISTRY QUERY & RESOLUTION HELPERS
# ==============================================================================

def get_course_assessment_plan(course_id: int) -> Optional[CoursePlanDefinition]:
    """Retrieve the authoritative CoursePlanDefinition for a course, or None."""
    return COURSE_ASSESSMENT_PLANS.get(course_id)


def normalize_course_assessment_type(course_id: int, raw_type: Optional[str]) -> Optional[str]:
    """
    Course-specific assessment type normalization.
    Maps a raw examination label (e.g. 'FT2', 'INTERNAL ASSESSMENT - I [FJI]')
    to its canonical component code ('CT1', 'CT2', 'ENDSEM', etc.) ONLY when
    the course's authoritative assessment plan establishes that relationship.
    """
    if not raw_type or not isinstance(raw_type, str):
        return None
    raw_clean = raw_type.strip().upper()
    raw_condensed = raw_clean.replace(" ", "").replace("-", "")
    plan = get_course_assessment_plan(course_id)
    if not plan:
        return None

    for comp in plan.components:
        for accepted in comp.raw_labels:
            acc_clean = accepted.strip().upper()
            if raw_clean == acc_clean:
                return comp.code
            if raw_condensed == acc_clean.replace(" ", "").replace("-", ""):
                return comp.code
    return None


def get_course_raw_types_for_cycle(course_id: int, student_cycle: str) -> Set[str]:
    """
    Return the exact set of raw assessment types recognized for this course and cycle.
    For 'ALL', returns empty set indicating no filtering.
    """
    if not student_cycle or student_cycle.upper() == "ALL":
        return set()
    norm_cycle = student_cycle.strip().upper()
    plan = get_course_assessment_plan(course_id)
    if not plan:
        return set()

    raw_matches = set()
    for comp in plan.components:
        # Match either by component code or student_label
        if comp.code.upper() == norm_cycle or comp.student_label.upper() == norm_cycle:
            raw_matches.update(comp.raw_labels)
    return raw_matches


def is_exam_in_course_cycle(course_id: int, exam_assessment_type: Optional[str], student_cycle: str) -> bool:
    """Check whether an exam with exam_assessment_type belongs to student_cycle for course_id."""
    if not student_cycle or student_cycle.upper() == "ALL":
        return True
    if not exam_assessment_type:
        return False
    raw_accepted = get_course_raw_types_for_cycle(course_id, student_cycle)
    if not raw_accepted:
        return False
    return exam_assessment_type.strip().upper() in {r.strip().upper() for r in raw_accepted}


def get_course_assessment_scope(course_id: int, student_cycle: Optional[str], db: Optional[Session] = None) -> AssessmentScope:
    """
    Computes the authoritative AssessmentScope:
    - intended_scope: syllabus units & topics from authoritative course plan
    - observed_scope: paper-derived units, topics, questions, & marks from historical exam papers
    - evidence_status: EVIDENCE_BACKED | INTENDED_ONLY_NO_PAPERS | OUT_OF_SCOPE_OBSERVED | UNPLANNED_OBSERVED_ONLY | ALL_SCOPE
    """
    is_all = not student_cycle or student_cycle.strip().upper() == "ALL"
    cycle_clean = "ALL" if is_all else student_cycle.strip().upper()

    plan = get_course_assessment_plan(course_id)
    matched_comp = None

    if not plan:
        # No registered plan; derive canonical taxonomy from syllabus if db provided
        syl_units = set()
        if db:
            syl_units = {
                row[0] for row in (
                    db.query(Unit.number)
                    .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                    .filter(Syllabus.course_id == course_id)
                    .all()
                )
            }

        scope = AssessmentScope(
            course_id=course_id,
            student_cycle=cycle_clean,
            is_all=is_all,
            student_label="All Assessments" if is_all else cycle_clean,
            component_code="ALL" if is_all else cycle_clean,
            component_label="All Assessments" if is_all else cycle_clean,
            in_scope_unit_numbers=syl_units,
            has_authoritative_plan=False,
            notes="No authoritative course assessment plan registered.",
        )
    elif is_all:
        # ALL cycle covers all units in the syllabus plan
        all_units = set()
        for comp in plan.components:
            all_units.update(comp.syllabus_units)

        scope = AssessmentScope(
            course_id=course_id,
            student_cycle="ALL",
            is_all=True,
            student_label="All Assessments",
            component_code="ALL",
            component_label="All Assessments",
            in_scope_unit_numbers=all_units,
            has_authoritative_plan=True,
            source_document=plan.source_document,
            notes=plan.notes,
        )
    else:
        # Find matching component by code or student_label
        for comp in plan.components:
            if comp.code.upper() == cycle_clean or comp.student_label.upper() == cycle_clean:
                matched_comp = comp
                break

        if not matched_comp:
            scope = AssessmentScope(
                course_id=course_id,
                student_cycle=cycle_clean,
                is_all=False,
                student_label=cycle_clean,
                component_code=cycle_clean,
                component_label=cycle_clean,
                has_authoritative_plan=True,
                notes=f"Component '{cycle_clean}' does not exist in course {course_id} assessment plan.",
            )
        else:
            scope = AssessmentScope(
                course_id=course_id,
                student_cycle=cycle_clean,
                is_all=False,
                component_code=matched_comp.code,
                component_label=matched_comp.canonical_label,
                student_label=matched_comp.student_label,
                role=matched_comp.role,
                marks=matched_comp.marks,
                in_scope_unit_numbers=set(matched_comp.syllabus_units),
                has_authoritative_plan=True,
                source_document=plan.source_document,
                notes=matched_comp.notes,
            )

    # Expand in-scope topic IDs and topic names from db if provided
    if db and scope.in_scope_unit_numbers:
        topics_query = (
            db.query(Topic.id, Topic.name)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(
                Syllabus.course_id == course_id,
                Unit.number.in_(list(scope.in_scope_unit_numbers))
            )
            .all()
        )
        scope.in_scope_topic_ids = {t_id for t_id, _ in topics_query}
        scope.in_scope_topic_names = {t_name for _, t_name in topics_query}

    # Intended Scope dictionary
    intended_units = sorted(list(scope.in_scope_unit_numbers))
    scope.intended_scope = {
        "unit_numbers": intended_units,
        "topic_names": sorted(list(scope.in_scope_topic_names)),
        "source_document": scope.source_document,
        "notes": scope.notes,
    }

    # Derive Paper-Derived Observed Scope if DB session provided
    if db:
        from backend.models.core import Exam, Section, Question
        from backend.services.observed_assessment_coverage import (
            identify_exam_assessment,
            compute_cycle_observed_coverage,
        )
        from sqlalchemy.orm import selectinload

        all_course_exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.document),
                selectinload(Exam.sections)
                .selectinload(Section.questions)
                .selectinload(Question.topics)
                .selectinload(Topic.unit),
            )
            .filter(Exam.course_id == course_id)
            .all()
        )

        if is_all:
            cycle_exams = all_course_exams
        else:
            cycle_exams = []
            for ex in all_course_exams:
                ident = identify_exam_assessment(ex, course_id)
                if ident.student_cycle == cycle_clean:
                    cycle_exams.append(ex)
                elif matched_comp and ex.assessment_type and ex.assessment_type.strip().upper() in [r.strip().upper() for r in matched_comp.raw_labels]:
                    cycle_exams.append(ex)

        cycle_cov = compute_cycle_observed_coverage(course_id, cycle_clean, cycle_exams)

        scope.observed_scope = {
            "paper_count": cycle_cov.paper_count,
            "total_questions": cycle_cov.total_questions,
            "mapped_questions_count": cycle_cov.mapped_questions_count,
            "unmapped_questions_count": cycle_cov.unmapped_questions_count,
            "questions_with_known_marks": cycle_cov.questions_with_known_marks,
            "questions_with_unknown_marks": cycle_cov.questions_with_unknown_marks,
            "known_marks_total": cycle_cov.known_marks_total,
            "mapping_rate": cycle_cov.mapping_rate,
            "unit_numbers": cycle_cov.observed_unit_numbers,
            "topic_names": cycle_cov.observed_topic_names,
            "question_count_by_unit": cycle_cov.question_count_by_unit,
            "marks_by_unit": cycle_cov.marks_by_unit,
            "papers": cycle_cov.papers,
        }

        # Compute evidence status
        if is_all:
            scope.evidence_status = "ALL_SCOPE"
        elif not scope.has_authoritative_plan:
            scope.evidence_status = "UNPLANNED_OBSERVED_ONLY"
        elif cycle_cov.paper_count == 0:
            scope.evidence_status = "INTENDED_ONLY_NO_PAPERS"
        else:
            out_of_scope = [u for u in cycle_cov.observed_unit_numbers if u not in intended_units]
            if out_of_scope:
                scope.evidence_status = "OUT_OF_SCOPE_OBSERVED"
            else:
                scope.evidence_status = "EVIDENCE_BACKED"
    else:
        scope.observed_scope = {
            "paper_count": 0,
            "total_questions": 0,
            "mapped_questions_count": 0,
            "unmapped_questions_count": 0,
            "questions_with_known_marks": 0,
            "questions_with_unknown_marks": 0,
            "known_marks_total": 0.0,
            "mapping_rate": 0.0,
            "unit_numbers": [],
            "topic_names": [],
            "question_count_by_unit": {},
            "marks_by_unit": {},
            "papers": [],
        }
        scope.evidence_status = "ALL_SCOPE" if is_all else ("INTENDED_ONLY_NO_PAPERS" if scope.has_authoritative_plan else "UNPLANNED_OBSERVED_ONLY")

    return scope
