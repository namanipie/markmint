"""
Test suite for deterministic examination blueprint extraction, normalization, and clustering.
"""

import pytest
from backend.services.dna.blueprint import (
    BlueprintExtractor,
    SectionChoiceType,
    BlueprintStatus,
    SectionBlueprint,
    ExamBlueprint,
    BlueprintCluster
)
from backend.core.database import SessionLocal


def test_section_name_normalization():
    bpe = BlueprintExtractor

    # Part A variations
    assert bpe.normalize_section_name("PART - A") == "PART_A"
    assert bpe.normalize_section_name("PART A") == "PART_A"
    assert bpe.normalize_section_name("Part - A") == "PART_A"
    assert bpe.normalize_section_name("Part-A") == "PART_A"
    assert bpe.normalize_section_name("Section A") == "PART_A"
    assert bpe.normalize_section_name("PART - A (20 x 1 = 20 Marks)") == "PART_A"

    # Part B variations
    assert bpe.normalize_section_name("PART - B") == "PART_B"
    assert bpe.normalize_section_name("PART B") == "PART_B"
    assert bpe.normalize_section_name("Part-B") == "PART_B"
    assert bpe.normalize_section_name("Section B") == "PART_B"

    # Part C variations
    assert bpe.normalize_section_name("PART - C") == "PART_C"
    assert bpe.normalize_section_name("PART C") == "PART_C"
    assert bpe.normalize_section_name("Section C") == "PART_C"

    # Modules
    assert bpe.normalize_section_name("Module I") == "MODULE_1"
    assert bpe.normalize_section_name("MODULE-1") == "MODULE_1"
    assert bpe.normalize_section_name("Module II") == "MODULE_2"
    assert bpe.normalize_section_name("Module V") == "MODULE_5"

    # Default / unsegmented
    assert bpe.normalize_section_name("Default") == "DEFAULT"
    assert bpe.normalize_section_name("MAIN") == "DEFAULT"
    assert bpe.normalize_section_name(None) == "DEFAULT"


def test_choice_parsing_strictly_evidence_based():
    bpe = BlueprintExtractor

    # Compulsory
    t, d = bpe.parse_choice_type("Answer ALL Questions")
    assert t == SectionChoiceType.COMPULSORY.value
    t, d = bpe.parse_choice_type("Answer all the questions")
    assert t == SectionChoiceType.COMPULSORY.value

    # Unitary choice
    t, d = bpe.parse_choice_type("Answer ANY ONE Question")
    assert t == SectionChoiceType.UNITARY_CHOICE.value
    t, d = bpe.parse_choice_type("Answer any 1 Questions")
    assert t == SectionChoiceType.UNITARY_CHOICE.value

    # Selective choice
    t, d = bpe.parse_choice_type("Answer ANY FIVE Questions")
    assert t == SectionChoiceType.SELECTIVE_CHOICE.value
    assert "5" in d
    t, d = bpe.parse_choice_type("Answer any 4 Questions")
    assert t == SectionChoiceType.SELECTIVE_CHOICE.value
    assert "4" in d

    # Unspecified / None (never guessed)
    t, d = bpe.parse_choice_type(None)
    assert t == SectionChoiceType.UNSPECIFIED.value
    assert d is None
    t, d = bpe.parse_choice_type("Instructions regarding OMR sheet only.")
    assert t == SectionChoiceType.UNSPECIFIED.value


def test_section_blueprint_extraction_invariants():
    bpe = BlueprintExtractor

    questions = [
        {"id": 1, "question_number": "1", "marks": 1.0, "is_alternative": False, "question_type": "Objective / MCQ"},
        {"id": 2, "question_number": "2", "marks": 1.0, "is_alternative": False, "question_type": "Objective / MCQ"},
        {"id": 3, "question_number": "3", "marks": None, "is_alternative": False, "question_type": "Objective / MCQ"},  # unscored
        {"id": 4, "question_number": "4", "marks": 8.0, "is_alternative": False, "question_type": "Explanation / Descriptive"},
        {"id": 5, "question_number": "4 (OR)", "marks": 8.0, "is_alternative": True, "question_type": "Explanation / Descriptive"},  # internal choice
    ]

    sec_bp = bpe.extract_section_blueprint(
        section_id=10,
        raw_name="Part - A",
        instructions="Answer ALL Questions",
        questions=questions,
        sequence=1
    )

    assert sec_bp.name == "PART_A"
    assert sec_bp.sequence == 1
    assert sec_bp.total_questions == 5
    assert sec_bp.primary_questions_count == 4
    assert sec_bp.alternative_questions_count == 1
    assert sec_bp.has_internal_choice is True
    assert sec_bp.internal_choice_pairs == 1
    assert sec_bp.question_number_range == "1-4"
    assert sec_bp.has_unscored_questions is True
    assert sec_bp.unscored_questions_count == 1
    assert sec_bp.marks_per_question == [1.0, 8.0]
    # Scored marks sum (primary only with non-null marks: 1.0 + 1.0 + 8.0 = 10.0)
    assert sec_bp.scored_marks_sum == 10.0
    # Total offered marks (all non-null: 1.0 + 1.0 + 8.0 + 8.0 = 18.0)
    assert sec_bp.total_offered_marks == 18.0
    assert sec_bp.question_types["Objective / MCQ"] == 3
    assert sec_bp.question_types["Explanation / Descriptive"] == 2


def test_exam_blueprint_and_reconciliation():
    bpe = BlueprintExtractor

    sec1_questions = [
        {"id": 1, "question_number": "1", "marks": 1.0, "is_alternative": False, "question_type": "Objective / MCQ"},
        {"id": 2, "question_number": "2", "marks": 1.0, "is_alternative": False, "question_type": "Objective / MCQ"},
    ]
    sec2_questions = [
        {"id": 3, "question_number": "3", "marks": 8.0, "is_alternative": False, "question_type": "Numerical / Calculation"},
        {"id": 4, "question_number": "3", "marks": 8.0, "is_alternative": True, "question_type": "Numerical / Calculation"},
    ]

    exam_sections = [
        {"id": 101, "name": "PART - A", "instructions": "Answer ALL Questions", "questions": sec1_questions},
        {"id": 102, "name": "PART - B", "instructions": "Answer ALL Questions", "questions": sec2_questions},
    ]

    exam_bp = bpe.extract_exam_blueprint(
        exam_id=99,
        course_id=1,
        year=2023,
        raw_assessment_type="END_SEM",
        sections_data=exam_sections
    )

    assert exam_bp.exam_id == 99
    assert exam_bp.assessment_cycle == "ENDSEM"
    assert exam_bp.section_count == 2
    assert exam_bp.total_questions == 4
    assert exam_bp.primary_questions == 3
    assert exam_bp.alternative_questions == 1

    # Invariants: sum(sections) == paper
    assert exam_bp.total_scored_marks == sum(s.scored_marks_sum for s in exam_bp.sections)
    assert exam_bp.total_offered_marks == sum(s.total_offered_marks for s in exam_bp.sections)
    assert exam_bp.total_questions == sum(s.total_questions for s in exam_bp.sections)
    assert exam_bp.has_unscored_questions is False
    assert "PART_A" in exam_bp.structural_signature
    assert "PART_B" in exam_bp.structural_signature


def test_blueprint_signature_structural_invariance():
    bpe = BlueprintExtractor

    # Paper A and Paper B have IDENTICAL structure but DIFFERENT topic names / question text
    paper_a = [
        {"id": 1, "name": "PART A", "instructions": "Answer ALL", "questions": [
            {"id": 1, "question_number": "1", "marks": 1.0, "is_alternative": False, "topic": "Calculus"}
        ]}
    ]
    paper_b = [
        {"id": 2, "name": "Part-A", "instructions": "Answer ALL Questions", "questions": [
            {"id": 10, "question_number": "1", "marks": 1.0, "is_alternative": False, "topic": "Matrices"}
        ]}
    ]

    bp_a = bpe.extract_exam_blueprint(1, 1, 2023, "END_SEM", paper_a)
    bp_b = bpe.extract_exam_blueprint(2, 1, 2024, "END_SEM", paper_b)

    # Signatures must match because structure is identical
    assert bp_a.structural_signature == bp_b.structural_signature


def test_clustering_dominant_vs_variant():
    bpe = BlueprintExtractor

    # Create 3 exams matching template 1, and 1 exam matching template 2
    template1_sections = [
        {"id": 1, "name": "PART A", "instructions": "Answer ALL", "questions": [
            {"id": 1, "question_number": "1", "marks": 1.0, "is_alternative": False}
        ]}
    ]
    template2_sections = [
        {"id": 2, "name": "PART A", "instructions": "Answer ALL", "questions": [
            {"id": 1, "question_number": "1", "marks": 5.0, "is_alternative": False}  # 5 marks instead of 1
        ]}
    ]

    bp1 = bpe.extract_exam_blueprint(1, 1, 2022, "END_SEM", template1_sections)
    bp2 = bpe.extract_exam_blueprint(2, 1, 2023, "END_SEM", template1_sections)
    bp3 = bpe.extract_exam_blueprint(3, 1, 2024, "END_SEM", template1_sections)
    bp4 = bpe.extract_exam_blueprint(4, 1, 2024, "END_SEM", template2_sections)

    clusters = bpe.cluster_blueprints([bp1, bp2, bp3, bp4])

    assert len(clusters) == 2
    dom_cluster = clusters[0]
    assert dom_cluster.is_dominant is True
    assert dom_cluster.status == BlueprintStatus.DOMINANT_STRUCTURE.value
    assert dom_cluster.matching_paper_count == 3
    assert dom_cluster.percentage_of_cycle == 75.0
    assert dom_cluster.years_observed == [2022, 2023, 2024]
    assert dom_cluster.is_sparse is False

    var_cluster = clusters[1]
    assert var_cluster.is_dominant is False
    assert var_cluster.status == BlueprintStatus.STRUCTURAL_VARIANT.value
    assert var_cluster.matching_paper_count == 1
    assert var_cluster.is_sparse is True


def test_duplicate_exam_invariance():
    bpe = BlueprintExtractor

    exam_sections = [
        {"id": 1, "name": "PART A", "instructions": "Answer ALL", "questions": [
            {"id": 1, "question_number": "1", "marks": 1.0, "is_alternative": False}
        ]}
    ]
    bp1 = bpe.extract_exam_blueprint(1, 1, 2023, "END_SEM", exam_sections)

    c1 = bpe.cluster_blueprints([bp1])
    # Duplicate input
    c2 = bpe.cluster_blueprints([bp1, bp1])

    # Signatures and labels must remain completely invariant
    assert c1[0].signature == c2[0].signature
    assert c1[0].label == c2[0].label


def test_real_canonical_courses_blueprint_extraction():
    """Verify live extraction against production database."""
    bpe = BlueprintExtractor
    db = SessionLocal()
    try:
        canonical_courses = [1, 2, 5, 28]
        for cid in canonical_courses:
            res = bpe.extract_course_blueprints_from_db(cid, db=db)
            assert res.course_id == cid
            assert res.total_papers_analyzed > 0
            assert len(res.cycles) > 0

            # Invariant check for every extracted exam
            for cycle_name, cycle_bp in res.cycles.items():
                for cluster in cycle_bp.clusters:
                    rep = cluster.representative_blueprint
                    # Section marks reconcile to paper marks
                    assert rep.total_scored_marks == pytest.approx(sum(s.scored_marks_sum for s in rep.sections), 0.01)
                    assert rep.total_offered_marks == pytest.approx(sum(s.total_offered_marks for s in rep.sections), 0.01)
                    assert rep.total_questions == sum(s.total_questions for s in rep.sections)

        # Specific check for Course 1 (Calculus)
        math_res = bpe.extract_course_blueprints_from_db(1, db=db)
        assert "ENDSEM" in math_res.cycles
        math_endsem = math_res.cycles["ENDSEM"]
        assert math_endsem.dominant_signature is not None
        dom_math = math_endsem.clusters[0]
        assert dom_math.is_dominant is True
        assert dom_math.matching_paper_count >= 4
        assert "PART_A" in dom_math.signature
        assert "PART_B" in dom_math.signature
        assert "PART_C" in dom_math.signature

        # Specific check for Course 5 (PPS) multiple assessment cycles
        pps_res = bpe.extract_course_blueprints_from_db(5, db=db)
        assert "ENDSEM" in pps_res.cycles
        assert "CT1" in pps_res.cycles
        assert "CT2" in pps_res.cycles
        # Ensure CT1 and ENDSEM were NOT merged
        assert pps_res.cycles["CT1"].clusters[0].signature != pps_res.cycles["ENDSEM"].clusters[0].signature
        # Both cycles have multiple variants with count=1, so dominant_signature is correctly None (sparse rule)
        assert pps_res.cycles["CT1"].dominant_signature is None

    finally:
        db.close()


def test_empty_course_blueprint_integration():
    """1. Empty course returns empty blueprint list without failure."""
    from backend.services.dna.analyzer import DNAAnalyzerService
    dna = DNAAnalyzerService.analyze([])
    assert dna.assessment_blueprints == []
    assert dna.sample_size.papers == 0


def test_course_isolation_blueprint():
    """2. Course isolation: exams from Course 2 are excluded when analyzing Course 1."""
    from backend.services.dna.analyzer import DNAAnalyzerService
    exam1 = {
        "id": 101,
        "course_id": 1,
        "year": 2023,
        "exam_type": "END_SEM",
        "sections": [{
            "id": 1,
            "name": "PART A",
            "instructions": "Answer ALL",
            "questions": [
                {"id": 1, "question_number": "1", "marks": 2.0, "is_alternative": False, "question_type": "Objective / MCQ"}
            ]
        }]
    }
    exam2 = {
        "id": 102,
        "course_id": 2,
        "year": 2023,
        "exam_type": "END_SEM",
        "sections": [{
            "id": 2,
            "name": "PART B",
            "instructions": "Answer ALL",
            "questions": [
                {"id": 2, "question_number": "1", "marks": 10.0, "is_alternative": False, "question_type": "Explanation / Descriptive"}
            ]
        }]
    }
    dna = DNAAnalyzerService.analyze([exam1, exam2], target_course_id=1)
    assert len(dna.assessment_blueprints) == 1
    assert dna.assessment_blueprints[0].exam_ids == [101]
    assert dna.assessment_blueprints[0].matching_paper_count == 1


def test_assessment_cycle_isolation_endpoint():
    """3. Assessment-cycle isolation: filtering by CT1 vs ENDSEM preserves separation."""
    from backend.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res_ct1 = client.get("/api/analysis/dna?course_id=5&assessment_cycle=CT1")
    assert res_ct1.status_code == 200
    data_ct1 = res_ct1.json()
    assert "assessment_blueprints" in data_ct1
    for cluster in data_ct1["assessment_blueprints"]:
        rep = cluster["representative_blueprint"]
        assert rep["assessment_cycle"] == "CT1"

    res_endsem = client.get("/api/analysis/dna?course_id=5&assessment_cycle=ENDSEM")
    assert res_endsem.status_code == 200
    data_endsem = res_endsem.json()
    assert "assessment_blueprints" in data_endsem
    for cluster in data_endsem["assessment_blueprints"]:
        rep = cluster["representative_blueprint"]
        assert rep["assessment_cycle"] == "ENDSEM"


def test_track_language_isolation():
    """4. Track/language isolation via DB query."""
    bpe = BlueprintExtractor
    db = SessionLocal()
    try:
        res = bpe.extract_course_blueprints_from_db(course_id=1, db=db, track_id=999999)
        assert res.total_papers_analyzed == 0
        assert len(res.cycles) == 0
    finally:
        db.close()


def test_cutoff_year_isolation():
    """5. Cutoff-year isolation: strictly year < cutoff_year."""
    bpe = BlueprintExtractor
    db = SessionLocal()
    try:
        res_cutoff_2024 = bpe.extract_course_blueprints_from_db(course_id=1, db=db, cutoff_year=2024)
        for cycle, cycle_bp in res_cutoff_2024.cycles.items():
            for cluster in cycle_bp.clusters:
                for y in cluster.years_observed:
                    assert y < 2024, f"Year {y} violates cutoff_year=2024"

        res_cutoff_2023 = bpe.extract_course_blueprints_from_db(course_id=1, db=db, cutoff_year=2023)
        assert res_cutoff_2023.total_papers_analyzed <= res_cutoff_2024.total_papers_analyzed
    finally:
        db.close()


def test_duplicate_exam_invariance_in_dna_analyzer():
    """6. Duplicate exam inputs do not alter blueprint clustering."""
    from backend.services.dna.analyzer import DNAAnalyzerService
    exam1 = {
        "id": 201,
        "course_id": 1,
        "year": 2023,
        "exam_type": "END_SEM",
        "sections": [{
            "id": 1,
            "name": "PART A",
            "instructions": "Answer ALL",
            "questions": [
                {"id": 1, "question_number": "1", "marks": 2.0, "is_alternative": False, "question_type": "Objective / MCQ"}
            ]
        }]
    }
    dna_single = DNAAnalyzerService.analyze([exam1], target_course_id=1)
    dna_duplicate = DNAAnalyzerService.analyze([exam1, exam1], target_course_id=1)

    assert len(dna_single.assessment_blueprints) == len(dna_duplicate.assessment_blueprints) == 1
    assert dna_single.assessment_blueprints[0].matching_paper_count == dna_duplicate.assessment_blueprints[0].matching_paper_count == 1
    assert dna_single.assessment_blueprints[0].signature == dna_duplicate.assessment_blueprints[0].signature


def test_partial_section_metadata():
    """7. Partial section metadata: missing raw_name or instructions default gracefully."""
    bpe = BlueprintExtractor
    exam_partial = [
        {"id": 1, "name": None, "instructions": None, "questions": [
            {"id": 1, "question_number": None, "marks": 5.0, "is_alternative": False}
        ]}
    ]
    bp = bpe.extract_exam_blueprint(301, 1, 2023, None, exam_partial)
    assert bp.section_count == 1
    sec = bp.sections[0]
    assert sec.name == "DEFAULT"
    assert sec.choice_type == SectionChoiceType.UNSPECIFIED.value
    assert sec.question_number_range is None
    assert sec.scored_marks_sum == 5.0


def test_missing_marks_in_blueprints():
    """8. Missing marks: flagged as unscored without fabricating marks."""
    bpe = BlueprintExtractor
    exam_missing_marks = [
        {"id": 1, "name": "PART A", "instructions": "Answer ALL", "questions": [
            {"id": 1, "question_number": "1", "marks": None, "is_alternative": False},
            {"id": 2, "question_number": "2", "marks": 2.0, "is_alternative": False}
        ]}
    ]
    bp = bpe.extract_exam_blueprint(401, 1, 2023, "END_SEM", exam_missing_marks)
    assert bp.has_unscored_questions is True
    sec = bp.sections[0]
    assert sec.has_unscored_questions is True
    assert sec.unscored_questions_count == 1
    assert sec.scored_marks_sum == 2.0
    assert "m=2.0" in bp.structural_signature


def test_blueprint_reconciliation_invariants():
    """9. Blueprint reconciliation: section totals equal paper totals, percentages sum to 100%."""
    bpe = BlueprintExtractor
    db = SessionLocal()
    try:
        for cid in [1, 2, 5, 28]:
            res = bpe.extract_course_blueprints_from_db(cid, db=db)
            for cycle_name, cycle_bp in res.cycles.items():
                total_cycle_pct = sum(c.percentage_of_cycle for c in cycle_bp.clusters)
                assert total_cycle_pct == pytest.approx(100.0, abs=0.1)

                for cluster in cycle_bp.clusters:
                    rep = cluster.representative_blueprint
                    assert sum(s.total_questions for s in rep.sections) == rep.total_questions
                    assert sum(s.primary_questions_count for s in rep.sections) == rep.primary_questions
                    assert sum(s.alternative_questions_count for s in rep.sections) == rep.alternative_questions
                    assert sum(s.scored_marks_sum for s in rep.sections) == pytest.approx(rep.total_scored_marks, 0.01)
                    assert sum(s.total_offered_marks for s in rep.sections) == pytest.approx(rep.total_offered_marks, 0.01)
    finally:
        db.close()


def test_backward_compatibility_existing_exam_dna_fields():
    """10. Backward compatibility: existing ExamDNA fields remain intact and populated."""
    from backend.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/analysis/dna?course_id=1")
    assert res.status_code == 200
    data = res.json()

    # Pre-existing fields
    assert "sample_size" in data
    assert "topics" in data
    assert "units" in data
    assert "question_types" in data
    assert "repetition" in data
    assert "families" in data
    assert "unit_distribution" in data
    assert "marks_distribution" in data
    assert "pattern_summary" in data
    assert "temporal_unit_question_type_breakdown" in data
    assert "temporal_unit_focus" in data
    assert "topic_historical_footprints" in data
    assert "temporal_topic_focus" in data

    # New field
    assert "assessment_blueprints" in data
    assert isinstance(data["assessment_blueprints"], list)
    assert len(data["assessment_blueprints"]) > 0

    first_cluster = data["assessment_blueprints"][0]
    assert "signature" in first_cluster
    assert "label" in first_cluster
    assert "matching_paper_count" in first_cluster
    assert "percentage_of_cycle" in first_cluster
    assert "years_observed" in first_cluster
    assert "assessment_cycles_observed" in first_cluster
    assert "status" in first_cluster
    assert "is_dominant" in first_cluster
    assert "is_sparse" in first_cluster
    assert "representative_blueprint" in first_cluster
