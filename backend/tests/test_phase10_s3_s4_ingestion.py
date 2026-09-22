"""
Test suite for Phase 10: Semester 3 and Semester 4 Core CSE Corpus Ingestion.
Validates:
1. Declarative taxonomy registry integrity across all 5 courses (DSA, OS, COA, DAA, DBMS).
2. Database persistence of courses, syllabuses, units, topics, and exams.
3. Ingestion of genuine exam papers with SHA-256 deduplication and non-empty question text.
4. Zero cross-course leakage across all mapped question_topic pairs.
5. Assessment plan structure, components, and unit coverage.
6. Deterministic classifier accuracy on core syllabus concepts.
"""
import pytest
from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Exam, Section, Question, CurriculumMapping, question_topic
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
from backend.services.taxonomy_registry import get_taxonomy_registry, reset_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_taxonomy_registry_s3_s4_integrity():
    """Verify Courses 24-28 declarative taxonomy definitions in the registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    expected_courses = {
        24: ("21CSC201J", "Data Structures and Algorithms", 27, 737, 763),
        25: ("21CSC202J", "Operating Systems", 27, 764, 790),
        26: ("21CSS201T", "Computer Organization and Architecture", 25, 791, 815),
        27: ("21CSC204J", "Design and Analysis of Algorithms", 25, 816, 840),
        28: ("21CSC205P", "Database Management Systems", 25, 841, 865),
    }

    all_topic_ids = set()

    for cid, (code, name, topic_count, min_tid, max_tid) in expected_courses.items():
        assert registry.has_course(cid), f"Course {cid} ({name}) must be registered."
        entry = registry.get_course(cid)
        assert entry.course.id == cid
        assert entry.course.canonical_code == code
        assert entry.course.name == name
        assert len(entry.units) == 5, f"Course {cid} must have exactly 5 units."

        rules = registry.get_topic_rules(cid)
        assert len(rules) == topic_count, f"Course {cid} must have {topic_count} rules."

        tids = [r.topic_id for r in rules]
        assert min(tids) == min_tid, f"Course {cid} min topic id should be {min_tid}"
        assert max(tids) == max_tid, f"Course {cid} max topic id should be {max_tid}"

        # Invariant: No overlapping topic IDs across courses
        for tid in tids:
            assert tid not in all_topic_ids, f"Duplicate topic ID {tid} detected!"
            all_topic_ids.add(tid)


def test_database_courses_and_syllabuses(db):
    """Verify database records for Courses 24-28."""
    course_ids = [24, 25, 26, 27, 28]
    courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    assert len(courses) == 5, "All 5 S3/S4 courses must exist in DB."

    for c in courses:
        assert c.canonical_code is not None
        assert c.regulation_year == 2021
        syllabuses = db.query(Syllabus).filter(Syllabus.course_id == c.id).all()
        assert len(syllabuses) >= 1, f"Course {c.id} must have a Syllabus record."
        syl = syllabuses[0]
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).all()
        assert len(units) == 5, f"Course {c.id} syllabus must have 5 units."


def test_database_exam_corpus_ingestion(db):
    """Verify that all 29 genuine exam papers were ingested with non-empty questions."""
    course_ids = [24, 25, 26, 27, 28]
    exams = db.query(Exam).filter(Exam.course_id.in_(course_ids)).all()
    assert len(exams) == 29, f"Expected 29 exam papers, found {len(exams)}"

    # Check breakdown per course
    counts = {}
    for e in exams:
        counts[e.course_id] = counts.get(e.course_id, 0) + 1
    assert counts[24] == 7, "DSA must have 7 papers"
    assert counts[25] == 6, "OS must have 6 papers"
    assert counts[26] == 4, "COA must have 4 papers"
    assert counts[27] == 8, "DAA must have 8 papers"
    assert counts[28] == 4, "DBMS must have 4 papers"

    # Verify questions and sections exist and have text
    total_q = 0
    for e in exams:
        sections = db.query(Section).filter(Section.exam_id == e.id).all()
        assert len(sections) >= 2, f"Exam {e.id} must have at least 2 sections"
        for s in sections:
            questions = db.query(Question).filter(Question.section_id == s.id).all()
            for q in questions:
                total_q += 1
                assert len(q.original_text.strip()) > 5, f"Question {q.id} has empty text!"
                assert q.extraction_method == "VISION_GEMINI"

    assert total_q >= 900, f"Expected >= 900 questions across 29 exams, found {total_q}"


def test_zero_cross_course_leakage(db):
    """Verify that question_topic mappings for Courses 24-28 strictly reference that course's topics."""
    course_ids = [24, 25, 26, 27, 28]
    
    for cid in course_ids:
        mappings = (
            db.query(Question.id, Topic.id, Unit.id)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .all()
        )

        assert len(mappings) > 0, f"Course {cid} must have mapped questions."
        
        for qid, tid, uid in mappings:
            unit_course_id = (
                db.query(Course.id)
                .join(Syllabus, Course.id == Syllabus.course_id)
                .join(Unit, Syllabus.id == Unit.syllabus_id)
                .filter(Unit.id == uid)
                .scalar()
            )
            assert unit_course_id == cid, (
                f"CROSS-COURSE LEAKAGE DETECTED! Question {qid} from Course {cid} "
                f"mapped to Topic {tid} (Unit {uid}) which belongs to Course {unit_course_id}!"
            )


def test_assessment_plan_and_coverage(db):
    """Verify that CourseAssessmentPlan, components, and unit coverages exist for S3/S4 courses."""
    course_ids = [24, 25, 26, 27, 28]

    for cid in course_ids:
        plans = db.query(CourseAssessmentPlan).filter(CourseAssessmentPlan.course_id == cid).all()
        assert len(plans) >= 1, f"Course {cid} must have an assessment plan."
        plan = plans[0]

        components = db.query(AssessmentComponent).filter(AssessmentComponent.plan_id == plan.id).all()
        assert len(components) == 3, f"Course {cid} plan must have 3 components (CLA1, CLA2, ENDSEM)."
        comp_codes = {c.code for c in components}
        assert comp_codes == {"CLA1", "CLA2", "ENDSEM"}

        coverages = db.query(AssessmentCoverage).filter(
            AssessmentCoverage.assessment_component_id.in_([c.id for c in components])
        ).all()
        assert len(coverages) == 10, f"Course {cid} should have 10 coverage links (2 for CLA1, 3 for CLA2, 5 for ENDSEM)."


def test_curriculum_mappings_linked(db):
    """Verify that branch semester curriculum slots are linked to Courses 24-28."""
    course_ids = [24, 25, 26, 27, 28]
    for cid in course_ids:
        linked_mappings = db.query(CurriculumMapping).filter(
            CurriculumMapping.course_id == cid,
            CurriculumMapping.status == "MATCHED"
        ).all()
        assert len(linked_mappings) >= 15, f"Course {cid} should be linked to at least 15 branch curriculum slots."


def test_classifier_accuracy_on_stem_proposals():
    """Verify deterministic classifier behavior on representative questions for each subject."""
    registry = get_taxonomy_registry()

    test_cases = [
        (24, "Perform single and double rotations to rebalance an AVL tree with balance factor.", 755), # AVL Trees
        (24, "Find the shortest path using Dijkstra's algorithm for the weighted graph.", 763), # Dijkstra's Algorithm
        (25, "Explain the working of Peterson's solution for the critical-section problem.", 770), # Critical-Section
        (25, "Apply the Banker's algorithm to determine if the system is in a safe state.", 777), # Deadlock Prevention & Avoidance
        (26, "Draw the logic circuit of a carry lookahead adder and explain CLA generate and propagate.", 802), # Adders
        (26, "Multiply signed numbers -7 and +3 using Booth's algorithm and bit-pair recoding.", 803), # Booth's Algorithm
        (27, "Solve the matrix chain multiplication problem for optimal parenthesization using dynamic programming.", 829), # DP: MCM
        (27, "State and prove Cook's theorem for boolean satisfiability.", 838), # NP-Completeness
        (28, "Define Boyce Codd Normal Form (BCNF) and explain why every relation in BCNF is also in 3NF.", 858), # 3NF & BCNF
        (28, "Explain the two-phase locking protocol (2PL) and how it prevents concurrency conflicts.", 863), # 2PL
    ]

    for cid, question_text, expected_topic_id in test_cases:
        rules = registry.get_topic_rules(cid)
        classifier = TaxonomyClassifierService(rules)
        proposal = classifier.classify(question_id=99999, original_text=question_text)

        assert proposal.confidence in ["HIGH", "MEDIUM"], (
            f"Expected confident classification for '{question_text}' in Course {cid}, got {proposal.confidence} ({proposal.method})."
        )
        assert proposal.topic_id == expected_topic_id, (
            f"Expected topic {expected_topic_id} for '{question_text}', got {proposal.topic_id} ({proposal.topic_name})."
        )
