import pytest
from backend.services.prediction.engine import ExamScopeCombinedModel, AllTimeFrequencyBaseline
from backend.services.prediction.context import PredictionTarget
from backend.services.dna.analyzer import DNAAnalyzerService


def test_n0_empty_exam_set():
    """Verify behavior with N=0 papers: safe handling, prior 0.5, no crashes."""
    dna = DNAAnalyzerService.analyze([])
    assert dna.sample_size.papers == 0
    assert dna.sample_size.questions == 0
    assert len(dna.topics) == 0

    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    assert len(preds) == 0


def test_n1_single_exam_behavior():
    """Verify behavior with N=1 paper: probability=(1+1)/(1+2)=0.6667, confidence=INSUFFICIENT."""
    exams = [
        {
            "id": "e1",
            "year": 2023,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": "q1",
                    "topic": "Matrices",
                    "marks": 10.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": 0.4,
                }
            ],
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.papers == 1

    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    assert len(preds) == 1

    p = preds[0]
    assert p.name == "Matrices"
    # Laplace smoothing with k=1, N=1 -> (1+1)/(1+2) = 2/3 ~ 0.6667
    assert p.probability == pytest.approx(0.6667, abs=1e-4)
    # With N=1, confidence must strictly be INSUFFICIENT
    assert p.confidence == "INSUFFICIENT"
    assert p.evidence_sufficiency == "INSUFFICIENT"
    assert "INSUFFICIENT_EVIDENCE" in p.reason_codes
    assert "LOW_EVIDENCE" in p.reason_codes


def test_n2_two_exams_behavior():
    """Verify behavior with N=2 papers: probability=(k+1)/(2+2), confidence capped (not HIGH)."""
    exams = [
        {
            "id": "e1",
            "year": 2022,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": "q1",
                    "topic": "Algebra",
                    "marks": 15.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                },
                {
                    "id": "q2",
                    "topic": "Calculus",
                    "marks": 10.0,
                    "is_alternative": False,
                    "question_type": "SHORT",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                },
            ],
        },
        {
            "id": "e2",
            "year": 2023,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": "q3",
                    "topic": "Algebra",
                    "marks": 20.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                }
            ],
        },
    ]

    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.papers == 2

    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    pred_map = {p.name: p for p in preds}

    # Algebra: present in 2/2 papers -> (2+1)/(2+2) = 3/4 = 0.75
    alg = pred_map["Algebra"]
    assert alg.papers_with_topic == 2
    assert alg.probability == pytest.approx(0.75, abs=1e-4)
    # N=2 sample is limited, confidence must NOT be HIGH
    assert alg.confidence != "HIGH"
    assert alg.evidence_sufficiency == "LIMITED"

    # Calculus: present in 1/2 papers -> (1+1)/(2+2) = 2/4 = 0.50
    calc = pred_map["Calculus"]
    assert calc.papers_with_topic == 1
    assert calc.probability == pytest.approx(0.50, abs=1e-4)


def test_n3_three_exams_behavior():
    """Verify behavior with N=3 papers: minimum statistical threshold reached."""
    exams = [
        {
            "id": "e1",
            "year": 2021,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": "q1",
                    "topic": "GraphTheory",
                    "marks": 10.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                },
                {
                    "id": "q2",
                    "topic": "NumberTheory",
                    "marks": 10.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                },
            ],
        },
        {
            "id": "e2",
            "year": 2022,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": "q3",
                    "topic": "GraphTheory",
                    "marks": 10.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                }
            ],
        },
        {
            "id": "e3",
            "year": 2023,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": "q4",
                    "topic": "GraphTheory",
                    "marks": 15.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                }
            ],
        },
    ]

    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.papers == 3

    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    pred_map = {p.name: p for p in preds}

    # GraphTheory: in 3/3 papers -> (3+1)/(3+2) = 4/5 = 0.80
    gt = pred_map["GraphTheory"]
    assert gt.papers_with_topic == 3
    assert gt.probability == pytest.approx(0.80, abs=1e-4)
    assert "SUFFICIENT_HISTORY" in gt.reason_codes
    assert gt.evidence_sufficiency == "SUFFICIENT"

    # NumberTheory: only in 2021 (absent in 2022, 2023) -> (1+1)/(3+2) = 2/5 = 0.40
    nt = pred_map["NumberTheory"]
    assert nt.papers_with_topic == 1
    assert nt.probability == pytest.approx(0.40, abs=1e-4)
    assert "LONG_ABSENCE" in nt.reason_codes


def test_n5_five_exams_behavior():
    """Verify behavior with N=5 papers: robust sample, confidence can reach HIGH."""
    exams = [
        {
            "id": f"e{year}",
            "year": year,
            "exam_type": "FINAL",
            "questions": [
                {
                    "id": f"q_tree_{year}",
                    "topic": "Trees",
                    "marks": 15.0,
                    "is_alternative": False,
                    "question_type": "LONG",
                    "repetition_type": "singleton",
                    "family_name": None,
                    "difficulty": None,
                }
            ]
            + (
                [
                    {
                        "id": f"q_hash_{year}",
                        "topic": "Hashing",
                        "marks": 10.0,
                        "is_alternative": False,
                        "question_type": "SHORT",
                        "repetition_type": "singleton",
                        "family_name": None,
                        "difficulty": None,
                    }
                ]
                if year in (2022, 2023)
                else []
            ),
        }
        for year in range(2019, 2024)
    ]

    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.papers == 5

    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    pred_map = {p.name: p for p in preds}

    # Trees: in 5/5 papers -> (5+1)/(5+2) = 6/7 ~ 0.8571
    tree = pred_map["Trees"]
    assert tree.papers_with_topic == 5
    assert tree.probability == pytest.approx(0.8571, abs=1e-4)
    assert tree.confidence == "HIGH"
    assert "HIGH_FREQUENCY" in tree.reason_codes
    assert "RECENTLY_REPEATED" in tree.reason_codes
    assert "SUFFICIENT_HISTORY" in tree.reason_codes

    # Hashing: in 2/5 papers -> (2+1)/(5+2) = 3/7 ~ 0.4286
    hashing = pred_map["Hashing"]
    assert hashing.papers_with_topic == 2
    assert hashing.probability == pytest.approx(0.4286, abs=1e-4)


def test_n10_ten_exams_behavior():
    """Verify behavior with N=10 papers: asymptotic Laplace convergence and probability decoupling."""
    exams = []
    for year in range(2014, 2024):
        qs = [
            {
                "id": f"q_dp_{year}",
                "topic": "DynamicProgramming",
                "marks": 20.0,
                "is_alternative": False,
                "question_type": "LONG",
                "repetition_type": "singleton",
                "family_name": None,
                "difficulty": None,
            }
        ]
        # Recursion in 5 of 10 exams (2019-2023)
        if year >= 2019:
            qs.append({
                "id": f"q_rec_{year}",
                "topic": "Recursion",
                "marks": 10.0,
                "is_alternative": False,
                "question_type": "SHORT",
                "repetition_type": "singleton",
                "family_name": None,
                "difficulty": None,
            })
        # BitManipulation in only 1 exam (2014)
        if year == 2014:
            qs.append({
                "id": f"q_bit_{year}",
                "topic": "BitManipulation",
                "marks": 5.0,
                "is_alternative": False,
                "question_type": "SHORT",
                "repetition_type": "singleton",
                "family_name": None,
                "difficulty": None,
            })
        exams.append({"id": f"e{year}", "year": year, "exam_type": "FINAL", "questions": qs})

    dna = DNAAnalyzerService.analyze(exams)
    assert dna.sample_size.papers == 10

    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)
    pred_map = {p.name: p for p in preds}

    # DynamicProgramming: in 10/10 papers -> (10+1)/(10+2) = 11/12 ~ 0.9167
    dp = pred_map["DynamicProgramming"]
    assert dp.papers_with_topic == 10
    assert dp.probability == pytest.approx(0.9167, abs=1e-4)
    assert dp.confidence == "HIGH"

    # Recursion: in 5/10 papers -> (5+1)/(10+2) = 6/12 = 0.50
    rec = pred_map["Recursion"]
    assert rec.papers_with_topic == 5
    assert rec.probability == pytest.approx(0.50, abs=1e-4)

    # BitManipulation: in 1/10 papers -> (1+1)/(10+2) = 2/12 ~ 0.1667
    bit = pred_map["BitManipulation"]
    assert bit.papers_with_topic == 1
    assert bit.probability == pytest.approx(0.1667, abs=1e-4)
    assert "LONG_ABSENCE" in bit.reason_codes
    # Decoupling: low probability does not prevent valid classification of low recurrence
    assert bit.probability < 0.20
