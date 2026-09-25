import pytest
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.schemas import DataSufficiency

def test_data_sufficiency_insufficient():
    # 1 paper, 11 questions -> INSUFFICIENT (needs >1 paper)
    exams = [{"year": 2023, "questions": [{"marks": 5} for _ in range(11)]}]
    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.sufficiency == DataSufficiency.INSUFFICIENT
    
    # 2 papers, 9 questions -> INSUFFICIENT (needs >=10 questions)
    exams = [
        {"year": 2022, "questions": [{"marks": 5} for _ in range(5)]},
        {"year": 2023, "questions": [{"marks": 5} for _ in range(4)]}
    ]
    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.sufficiency == DataSufficiency.INSUFFICIENT

def test_data_sufficiency_moderate():
    # 5 papers, 50 questions -> MODERATE
    exams = [
        {"year": 2020 + i, "questions": [{"marks": 5} for _ in range(10)]}
        for i in range(5)
    ]
    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.sufficiency == DataSufficiency.MODERATE

def test_topic_paper_coverage():
    # 5 papers total. "Graphs" appears in 3 of them.
    exams = [
        {"id": 1, "year": 2018, "questions": [{"topic": "Graphs", "marks": 5}]},
        {"id": 2, "year": 2019, "questions": [{"topic": "Trees", "marks": 5}]},
        {"id": 3, "year": 2020, "questions": [{"topic": "Graphs", "marks": 5}]},
        {"id": 4, "year": 2021, "questions": [{"topic": "Graphs", "marks": 5}]},
        {"id": 5, "year": 2022, "questions": [{"topic": "Hashing", "marks": 5}]},
    ]
    
    dna = DNAAnalyzerService.analyze(exams)
    graph_dna = next(t for t in dna.topics if t.topic == "Graphs")
    
    assert graph_dna.paper_coverage == 0.6 # 3 / 5

def test_recurrence_interval():
    # Family appears in 2018, 2020, 2022. Intervals: 2020-2018=2, 2022-2020=2. Avg=2.0
    exams = [
        {"id": 1, "year": 2018, "questions": [{"family_name": "DFS_Traversal", "marks": 5}]},
        {"id": 2, "year": 2020, "questions": [{"family_name": "DFS_Traversal", "marks": 5}]},
        {"id": 3, "year": 2022, "questions": [{"family_name": "DFS_Traversal", "marks": 5}]},
    ]
    
    dna = DNAAnalyzerService.analyze(exams)
    fam_dna = next(f for f in dna.families if f.family_name == "DFS_Traversal")
    
    assert fam_dna.recurrence_interval_years == 2.0

def test_repetition_distinction():
    exams = [{"id": 1, "year": 2023, "questions": [
        {"repetition_type": "exact"},
        {"repetition_type": "near"},
        {"repetition_type": "near"},
        {"repetition_type": "conceptual"},
        {"repetition_type": "structural"},
        {"repetition_type": "structural"},
        {"repetition_type": "structural"}
    ]}]
    
    dna = DNAAnalyzerService.analyze(exams)
    assert dna.repetition.exact_count == 1
    assert dna.repetition.near_count == 2
    assert dna.repetition.conceptual_count == 1
    assert dna.repetition.structural_count == 3


def test_temporal_unit_question_type_breakdown():
    exams = [
        # Year 2023 - 3 exams
        {
            "id": 1,
            "year": 2023,
            "questions": [
                {"unit": "Unit 1", "question_type": "Numerical", "marks": 10},
                {"unit": "Unit 1", "question_type": "Descriptive", "marks": 5},
            ]
        },
        {
            "id": 2,
            "year": 2023,
            "questions": [
                {"unit": "Unit 1", "question_type": "Numerical", "marks": 10},
                {"unit": "Unit 1", "question_type": "Numerical", "marks": 10},
            ]
        },
        {
            "id": 3,
            "year": 2023,
            "questions": [
                {"unit": "Unit 1", "question_type": "Numerical", "marks": 10},
                {"unit": "Unit 1", "question_type": None, "marks": None},  # unclassified & unscored
            ]
        },
        # Year 2024 - 1 exam (sparse)
        {
            "id": 4,
            "year": 2024,
            "questions": [
                {"unit": "Unit 1", "question_type": "Descriptive", "marks": 15},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    temp = dna.temporal_unit_question_type_breakdown
    assert temp is not None
    assert len(temp) == 4

    # 2023: 6 questions total (Numerical: 4, Descriptive: 1, unclassified: 1)
    # Total marks: 40 (Numerical) + 5 (Descriptive) = 45 marks
    # 3 exams >= 3 and 6 questions >= 5 -> is_sparse is False
    y2023_num = next(r for r in temp if r.year == 2023 and r.question_type == "Numerical")
    assert y2023_num.question_count == 4
    assert y2023_num.total_unit_questions == 6
    assert y2023_num.question_percentage == round(4 / 6, 4)
    assert y2023_num.scored_marks == 40.0
    assert y2023_num.marks_weight_percentage == round(40 / 45, 4)
    assert y2023_num.is_sparse is False

    y2023_unclass = next(r for r in temp if r.year == 2023 and r.question_type == "unclassified")
    assert y2023_unclass.question_count == 1
    assert y2023_unclass.scored_marks == 0.0
    assert y2023_unclass.marks_weight_percentage == 0.0

    # 2024: 1 exam < 3 and 1 question < 5 -> is_sparse is True
    y2024 = next(r for r in temp if r.year == 2024)
    assert y2024.question_count == 1
    assert y2024.total_unit_questions == 1
    assert y2024.question_percentage == 1.0
    assert y2024.scored_marks == 15.0
    assert y2024.marks_weight_percentage == 1.0
    assert y2024.is_sparse is True

