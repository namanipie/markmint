"""
Tests for MintAI Historical Cognitive Demand Signals integration in Exam DNA.

Verifies:
1. Question count and percentage reconciliation: sum(counts) == total_questions, sum(percentages) == 1.0.
2. Marks reliability gating: marks weighting computed only when unscored <= 15%.
3. Breakdowns: assessment cycle, verified year (temporal), unit, section.
4. Cross-tabulation: Demand x QuestionType.
5. Blueprint Section demand integration.
6. Temporal evolution: missing years not interpolated, sparse years flagged.
7. Unclassified evidence transparency.
8. Course boundary and temporal cutoff isolation.
9. Duplicate exam invariance.
10. Empty DNA safety.
11. End-to-end integration across canonical courses against production_corpus.db.
"""

import pytest
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.cognitive_demand_classifier import CognitiveDemand
from backend.schemas import ExamDNA, CognitiveDemandDistributionDNA
from backend.core.database import SessionLocal
from backend.api.endpoints.analysis import _get_exams_as_dicts, _resolve_course


# ---------------------------------------------------------------------------
# Synthetic Unit Tests
# ---------------------------------------------------------------------------

def test_empty_exams_cognitive_demand():
    """Empty exam list must return safely initialized cognitive demand structures."""
    dna = DNAAnalyzerService.analyze([])
    assert dna.cognitive_demand_distribution is not None
    assert dna.cognitive_demand_distribution.total_questions == 0
    assert dna.cognitive_demand_distribution.items == []
    assert dna.cognitive_demand_distribution.is_marks_reliable is False
    assert dna.temporal_cognitive_demand == []
    assert dna.section_cognitive_profiles == []
    assert dna.demand_question_type_cross_tabulation == {}


def test_cognitive_demand_reconciliation_and_marks_reliable():
    """Valid exams with 100% scored marks must produce reliable marks weighting and exact count reconciliation."""
    exams = [
        {
            "id": 1,
            "year": 2021,
            "exam_type": "ENDSEM",
            "sections": [
                {
                    "name": "Part A",
                    "questions": [
                        {"id": 1, "original_text": "Define eigenvalues and eigenvectors.", "marks": 2.0, "question_type": "Definition", "unit": "Unit 1"},
                        {"id": 2, "original_text": "Explain the concept of Cayley-Hamilton theorem.", "marks": 2.0, "question_type": "Definition", "unit": "Unit 1"},
                    ]
                },
                {
                    "name": "Part B",
                    "questions": [
                        {"id": 3, "original_text": "Calculate the rank and nullity of the matrix [[1, 2], [3, 4]].", "marks": 8.0, "question_type": "Numerical / Calculation", "unit": "Unit 1"},
                        {"id": 4, "original_text": "State and prove Cayley-Hamilton theorem for a 3x3 square matrix.", "marks": 8.0, "question_type": "Derivation / Proof", "unit": "Unit 2"},
                    ]
                }
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    assert dna.cognitive_demand_distribution is not None
    dist = dna.cognitive_demand_distribution

    # 1. Total questions reconciliation
    assert dist.total_questions == 4
    item_count_sum = sum(item.question_count for item in dist.items)
    assert item_count_sum == 4

    # 2. Percentage reconciliation
    item_pct_sum = sum(item.percentage for item in dist.items)
    assert abs(item_pct_sum - 1.0) < 0.001

    # 3. Marks reliability
    assert dist.is_marks_reliable is True
    assert dist.marks_completeness_pct == 100.0
    assert dist.total_scored_marks == 20.0

    items_by_demand = {item.demand: item for item in dist.items}
    assert items_by_demand[CognitiveDemand.RECALL_AND_CONCEPT.value].question_count == 2
    assert items_by_demand[CognitiveDemand.RECALL_AND_CONCEPT.value].percentage == 0.5
    assert items_by_demand[CognitiveDemand.RECALL_AND_CONCEPT.value].scored_marks == 4.0
    assert items_by_demand[CognitiveDemand.RECALL_AND_CONCEPT.value].marks_percentage == 0.2

    assert items_by_demand[CognitiveDemand.PROCEDURAL_COMPUTATION.value].question_count == 1
    assert items_by_demand[CognitiveDemand.PROCEDURAL_COMPUTATION.value].percentage == 0.25
    assert items_by_demand[CognitiveDemand.PROCEDURAL_COMPUTATION.value].scored_marks == 8.0
    assert items_by_demand[CognitiveDemand.PROCEDURAL_COMPUTATION.value].marks_percentage == 0.4

    assert items_by_demand[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value].question_count == 1
    assert items_by_demand[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value].percentage == 0.25
    assert items_by_demand[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value].scored_marks == 8.0
    assert items_by_demand[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value].marks_percentage == 0.4


def test_marks_unreliability_threshold():
    """When unscored questions exceed 15%, marks_percentage must be omitted (None)."""
    # 2 unscored out of 5 questions = 40% unscored > 15% threshold
    exams = [
        {
            "id": 1,
            "year": 2022,
            "exam_type": "ENDSEM",
            "questions": [
                {"id": 1, "original_text": "Define continuity of a function.", "marks": None, "question_type": "Definition"},
                {"id": 2, "original_text": "What is a vector space?", "marks": None, "question_type": "Definition"},
                {"id": 3, "original_text": "Find the eigenvalues of the matrix A.", "marks": 5.0, "question_type": "Numerical / Calculation"},
                {"id": 4, "original_text": "Calculate the determinant of matrix B.", "marks": 5.0, "question_type": "Numerical / Calculation"},
                {"id": 5, "original_text": "Prove that every orthogonal matrix has determinant +1 or -1.", "marks": 10.0, "question_type": "Derivation / Proof"},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    dist = dna.cognitive_demand_distribution
    assert dist.is_marks_reliable is False
    assert dist.marks_completeness_pct == 60.0  # 3 / 5 scored
    for item in dist.items:
        assert item.marks_percentage is None


def test_demand_by_assessment_cycle():
    """Assessment cycle breakdown must accurately aggregate demand across cycles."""
    exams = [
        {
            "id": 1,
            "year": 2022,
            "exam_type": "CT1",
            "questions": [
                {"id": 1, "original_text": "Define a pointer in C.", "marks": 2.0, "question_type": "Definition"},
                {"id": 2, "original_text": "What is an array index?", "marks": 2.0, "question_type": "Definition"},
            ]
        },
        {
            "id": 2,
            "year": 2022,
            "exam_type": "ENDSEM",
            "questions": [
                {"id": 3, "original_text": "Write a C program to implement bubble sort.", "marks": 10.0, "question_type": "Programming / Code Implementation"},
                {"id": 4, "original_text": "Design a relational schema for a library management system.", "marks": 10.0, "question_type": "Design / Diagrammatic"},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    dist = dna.cognitive_demand_distribution
    assert "CT1" in dist.by_assessment_cycle
    assert "ENDSEM" in dist.by_assessment_cycle

    assert dist.by_assessment_cycle["CT1"][CognitiveDemand.RECALL_AND_CONCEPT.value] == 2
    assert dist.by_assessment_cycle["ENDSEM"][CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value] == 2


def test_demand_by_unit_and_unmapped():
    """Unit profiles must track both mapped and unmapped units explicitly."""
    exams = [
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"id": 1, "original_text": "Define primary key.", "unit": "Unit 1", "unit_number": 1},
                {"id": 2, "original_text": "Calculate the 3NF decomposition.", "unit": "Unit 2", "unit_number": 2},
                {"id": 3, "original_text": "Design a relational schema for the database.", "unit": None},  # unmapped
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    unit_profiles = {u.unit: u for u in dna.cognitive_demand_distribution.by_unit}

    assert "Unit 1" in unit_profiles
    assert unit_profiles["Unit 1"].demand_counts[CognitiveDemand.RECALL_AND_CONCEPT.value] == 1
    assert unit_profiles["Unit 1"].demand_percentages[CognitiveDemand.RECALL_AND_CONCEPT.value] == 1.0

    assert "Unit 2" in unit_profiles
    assert unit_profiles["Unit 2"].demand_counts[CognitiveDemand.PROCEDURAL_COMPUTATION.value] == 1
    assert unit_profiles["Unit 2"].demand_percentages[CognitiveDemand.PROCEDURAL_COMPUTATION.value] == 1.0

    assert "Unmapped / Unknown" in unit_profiles
    assert unit_profiles["Unmapped / Unknown"].demand_counts[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value] == 1


def test_demand_by_section_and_blueprint():
    """Section profiles and blueprint sections must reflect normalized section demand."""
    exams = [
        {
            "id": 1,
            "course_id": 101,
            "year": 2022,
            "exam_type": "ENDSEM",
            "sections": [
                {
                    "name": "PART A",
                    "questions": [
                        {"id": 1, "original_text": "What is normalization?", "question_type": "Definition", "marks": 2.0},
                        {"id": 2, "original_text": "Define functional dependency.", "question_type": "Definition", "marks": 2.0},
                    ]
                },
                {
                    "name": "PART B",
                    "questions": [
                        {"id": 3, "original_text": "Derive the BCNF decomposition algorithm with proof.", "question_type": "Derivation / Proof", "marks": 10.0},
                    ]
                }
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)

    # 1. Section Cognitive Profiles in DNA
    sec_profiles = {s.section_name: s for s in dna.section_cognitive_profiles}
    assert "PART_A" in sec_profiles
    assert sec_profiles["PART_A"].demand_counts[CognitiveDemand.RECALL_AND_CONCEPT.value] == 2
    assert "PART_B" in sec_profiles
    assert sec_profiles["PART_B"].demand_counts[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value] == 1

    # 2. Demand in Blueprint Clusters
    assert dna.assessment_blueprints is not None and len(dna.assessment_blueprints) > 0
    cluster = dna.assessment_blueprints[0]
    bp_sections = {s.name: s for s in cluster.representative_blueprint.sections}
    assert "PART_A" in bp_sections
    assert bp_sections["PART_A"].cognitive_demand_distribution[CognitiveDemand.RECALL_AND_CONCEPT.value] == 2
    assert "PART_B" in bp_sections
    assert bp_sections["PART_B"].cognitive_demand_distribution[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value] == 1


def test_demand_question_type_cross_tabulation():
    """Demand x QuestionType cross-tabulation must match question distribution."""
    exams = [
        {
            "id": 1,
            "questions": [
                {"id": 1, "original_text": "Define normal distribution.", "question_type": "Definition"},
                {"id": 2, "original_text": "Explain the concept of central limit theorem.", "question_type": "Explanation / Descriptive"},
                {"id": 3, "original_text": "Evaluate the integral of x*e^x dx.", "question_type": "Numerical / Calculation"},
                {"id": 4, "original_text": "Prove that the variance is non-negative.", "question_type": "Derivation / Proof"},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    cross = dna.demand_question_type_cross_tabulation
    assert cross is not None

    assert cross[CognitiveDemand.RECALL_AND_CONCEPT.value].get("Definition") == 1
    assert cross[CognitiveDemand.RECALL_AND_CONCEPT.value].get("Explanation / Descriptive") == 1
    assert cross[CognitiveDemand.PROCEDURAL_COMPUTATION.value].get("Numerical / Calculation") == 1
    assert cross[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value].get("Derivation / Proof") == 1


def test_temporal_cognitive_demand_evolution():
    """Temporal evolution must not interpolate missing years and must flag sparse years."""
    exams = [
        # Year 2018: sparse (only 1 question)
        {
            "id": 1,
            "year": 2018,
            "questions": [
                {"id": 1, "original_text": "Define stack.", "marks": 2.0, "question_type": "Definition"}
            ]
        },
        # Year 2021: not sparse (5 questions across 2 exams)
        {
            "id": 2,
            "year": 2021,
            "questions": [
                {"id": 2, "original_text": "Define queue.", "marks": 2.0, "question_type": "Definition"},
                {"id": 3, "original_text": "Calculate shortest path using Dijkstra.", "marks": 5.0, "question_type": "Numerical / Calculation"},
                {"id": 4, "original_text": "Trace the output of the BFS algorithm.", "marks": 5.0, "question_type": "Algorithm Tracing"},
            ]
        },
        {
            "id": 3,
            "year": 2021,
            "questions": [
                {"id": 5, "original_text": "Design a relational schema for the database.", "marks": 8.0, "question_type": "Design / Diagrammatic"},
                {"id": 6, "original_text": "Prove the master theorem for divide and conquer.", "marks": 10.0, "question_type": "Derivation / Proof"},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    temp = dna.temporal_cognitive_demand
    assert len(temp) == 2  # 2018 and 2021 only, 2019 and 2020 NOT interpolated!

    y2018 = next(t for t in temp if t.year == 2018)
    assert y2018.is_sparse is True
    assert y2018.total_questions == 1
    assert y2018.demand_counts[CognitiveDemand.RECALL_AND_CONCEPT.value] == 1

    y2021 = next(t for t in temp if t.year == 2021)
    assert y2021.is_sparse is False
    assert y2021.total_questions == 5
    assert y2021.exam_count == 2
    assert y2021.demand_counts[CognitiveDemand.PROCEDURAL_COMPUTATION.value] == 2
    assert y2021.demand_counts[CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN.value] == 2


def test_course_isolation_and_deduplication():
    """Cross-course questions must be excluded and duplicate exams must not alter counts."""
    base_exam = {
        "id": 1,
        "course_id": 10,
        "year": 2020,
        "questions": [
            {"id": 1, "original_text": "Explain Newton's laws of motion.", "marks": 5.0},
            {"id": 2, "original_text": "Calculate the velocity of the particle.", "marks": 5.0},
        ]
    }
    leaked_exam = {
        "id": 2,
        "course_id": 99,  # different course
        "year": 2020,
        "questions": [
            {"id": 3, "original_text": "Derive the Navier-Stokes equations.", "marks": 10.0},
        ]
    }
    duplicate_exam = dict(base_exam)

    # With target_course_id=10, leaked_exam must be filtered out
    # Duplicate base_exam must be deduped
    dna = DNAAnalyzerService.analyze([base_exam, duplicate_exam, leaked_exam], target_course_id=10)
    assert dna.sample_size.papers == 1
    assert dna.sample_size.questions == 2
    assert dna.cognitive_demand_distribution.total_questions == 2
    assert sum(item.question_count for item in dna.cognitive_demand_distribution.items) == 2


# ---------------------------------------------------------------------------
# Corpus-Wide Integration Tests against canonical courses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("course_name", [
    "Calculus And Linear Algebra",
    "Chemistry",
    "Programming For Problem Solving",
    "Database Management Systems",
])
def test_production_corpus_cognitive_demand_reconciliation(course_name):
    """
    Validates end-to-end cognitive demand integration against production_corpus.db
    for each canonical course without mutating the database.
    """
    db = SessionLocal()
    try:
        course = _resolve_course(db, course_name)
        assert course is not None

        # Fetch historical exams
        exams_dict = _get_exams_as_dicts(
            course_id=course.id,
            db=db,
            assessment_cycle="ALL"
        )
        assert len(exams_dict) > 0

        dna = DNAAnalyzerService.analyze(exams_dict, target_course_id=course.id)

        # 1. Structure presence
        assert dna.cognitive_demand_distribution is not None
        dist = dna.cognitive_demand_distribution

        # 2. Count reconciliation: sum(items) == total_questions == sample_size.questions
        total_q = dist.total_questions
        assert total_q == dna.sample_size.questions
        item_sum = sum(item.question_count for item in dist.items)
        assert item_sum == total_q

        # 3. Percentage reconciliation
        pct_sum = sum(item.percentage for item in dist.items)
        assert abs(pct_sum - 1.0) < 0.01

        # 4. Unclassified transparency
        unclass_item = next((item for item in dist.items if item.demand == CognitiveDemand.UNCLASSIFIED.value), None)
        assert unclass_item is not None
        assert unclass_item.question_count == dist.unclassified_count
        assert unclass_item.percentage == dist.unclassified_percentage

        # 5. Marks reliability consistency
        if dist.is_marks_reliable:
            scored_m_sum = sum(item.scored_marks for item in dist.items)
            assert abs(scored_m_sum - dist.total_scored_marks) < 0.05
            for item in dist.items:
                assert item.marks_percentage is not None
        else:
            for item in dist.items:
                assert item.marks_percentage is None

        # 6. Temporal evolution integrity
        for temp_yr in dna.temporal_cognitive_demand:
            yr_sum = sum(temp_yr.demand_counts.values())
            assert yr_sum == temp_yr.total_questions
            yr_pct_sum = sum(temp_yr.demand_percentages.values())
            assert abs(yr_pct_sum - 1.0) < 0.01

        # 7. Unit breakdown integrity
        for u in dist.by_unit:
            u_sum = sum(u.demand_counts.values())
            assert u_sum == u.total_questions
            u_pct_sum = sum(u.demand_percentages.values())
            assert abs(u_pct_sum - 1.0) < 0.01

        # 8. Section breakdown integrity
        for s in dist.by_section:
            s_sum = sum(s.demand_counts.values())
            assert s_sum == s.total_questions
            s_pct_sum = sum(s.demand_percentages.values())
            assert abs(s_pct_sum - 1.0) < 0.01

        # 9. Cross-tabulation integrity
        cross = dna.demand_question_type_cross_tabulation
        assert cross is not None
        cross_total = sum(sum(types.values()) for types in cross.values())
        assert cross_total == total_q

    finally:
        db.close()


def test_historical_cutoff_temporal_isolation():
    """Validates that cutoff_year parameter strictly excludes future exams and questions."""
    db = SessionLocal()
    try:
        course = _resolve_course(db, "Calculus And Linear Algebra")
        assert course is not None

        # Analyze with cutoff_year=2021
        exams_pre_2021 = _get_exams_as_dicts(
            course_id=course.id,
            db=db,
            assessment_cycle="ALL",
            cutoff_year=2021
        )
        # All returned exams must have year < 2021
        for e in exams_pre_2021:
            assert e.get("year") is not None
            assert e.get("year") < 2021

        dna_pre_2021 = DNAAnalyzerService.analyze(exams_pre_2021, target_course_id=course.id)

        # No years >= 2021 in temporal evolution
        for entry in dna_pre_2021.temporal_cognitive_demand:
            assert entry.year < 2021

        # Unrestricted analysis
        exams_all = _get_exams_as_dicts(
            course_id=course.id,
            db=db,
            assessment_cycle="ALL"
        )
        dna_all = DNAAnalyzerService.analyze(exams_all, target_course_id=course.id)

        # Pre-2021 question count must be strictly less than or equal to unrestricted count
        assert dna_pre_2021.sample_size.questions <= dna_all.sample_size.questions

    finally:
        db.close()
