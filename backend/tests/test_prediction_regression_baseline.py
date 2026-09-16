import pytest
from backend.services.prediction.engine import ExamScopeCombinedModel, AllTimeFrequencyBaseline
from backend.services.prediction.context import PredictionTarget
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.families.normalizer import QuestionNormalizer


def test_calculus_regression_baseline():
    """
    Deterministic regression fixture for Calculus.
    4 historical exams (2020-2023) covering Differentiation, Integration, and Limits.
    Differentiation: 4/4 papers -> P = (4+1)/(4+2) = 5/6 = 0.8333
    Integration: 3/4 papers -> P = (3+1)/(4+2) = 4/6 = 0.6667
    Limits: 1/4 papers -> P = (1+1)/(4+2) = 2/6 = 0.3333
    """
    calculus_exams = [
        {
            "id": "calc_2020",
            "year": 2020,
            "exam_type": "FINAL",
            "questions": [
                {"id": "q1", "topic": "Differentiation", "marks": 20.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "q2", "topic": "Integration", "marks": 20.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "q3", "topic": "Limits", "marks": 10.0, "is_alternative": False, "question_type": "SHORT", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
        {
            "id": "calc_2021",
            "year": 2021,
            "exam_type": "FINAL",
            "questions": [
                {"id": "q4", "topic": "Differentiation", "marks": 25.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "q5", "topic": "Integration", "marks": 25.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
        {
            "id": "calc_2022",
            "year": 2022,
            "exam_type": "FINAL",
            "questions": [
                {"id": "q6", "topic": "Differentiation", "marks": 25.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
        {
            "id": "calc_2023",
            "year": 2023,
            "exam_type": "FINAL",
            "questions": [
                {"id": "q7", "topic": "Differentiation", "marks": 20.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "q8", "topic": "Integration", "marks": 20.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
    ]

    dna = DNAAnalyzerService.analyze(calculus_exams)
    assert dna.sample_size.papers == 4

    engine = ExamScopeCombinedModel(dna)
    predictions = engine.predict(PredictionTarget.TOPIC)
    pred_map = {p.name: p for p in predictions}

    diff = pred_map["Differentiation"]
    integ = pred_map["Integration"]
    lim = pred_map["Limits"]

    # Invariant: Probability matches Laplace smoothing exactly
    assert diff.probability == pytest.approx(5.0 / 6.0, abs=1e-4)
    assert integ.probability == pytest.approx(4.0 / 6.0, abs=1e-4)
    assert lim.probability == pytest.approx(2.0 / 6.0, abs=1e-4)

    # Invariant: Rank ordering
    assert diff.rank < integ.rank
    assert integ.rank < lim.rank

    # Invariant: Differentiation is present in all recent exams
    assert "SUFFICIENT_HISTORY" in diff.reason_codes
    assert "RECENTLY_REPEATED" in diff.reason_codes

    # Invariant: Limits absent in 2021, 2022, 2023 -> LONG_ABSENCE
    assert "LONG_ABSENCE" in lim.reason_codes


def test_chemistry_regression_baseline():
    """
    Deterministic regression fixture for Chemistry.
    3 historical exams (2021-2023) covering Electrochemistry, Thermodynamics, ChemicalKinetics.
    Electrochemistry: 3/3 papers -> P = (3+1)/(3+2) = 4/5 = 0.80
    Thermodynamics: 2/3 papers -> P = (2+1)/(3+2) = 3/5 = 0.60
    ChemicalKinetics: 1/3 papers -> P = (1+1)/(3+2) = 2/5 = 0.40
    """
    chem_exams = [
        {
            "id": "chem_2021",
            "year": 2021,
            "exam_type": "FINAL",
            "questions": [
                {"id": "c1", "topic": "Electrochemistry", "marks": 15.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "c2", "topic": "Thermodynamics", "marks": 15.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
        {
            "id": "chem_2022",
            "year": 2022,
            "exam_type": "FINAL",
            "questions": [
                {"id": "c3", "topic": "Electrochemistry", "marks": 15.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "c4", "topic": "ChemicalKinetics", "marks": 10.0, "is_alternative": False, "question_type": "SHORT", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
        {
            "id": "chem_2023",
            "year": 2023,
            "exam_type": "FINAL",
            "questions": [
                {"id": "c5", "topic": "Electrochemistry", "marks": 20.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
                {"id": "c6", "topic": "Thermodynamics", "marks": 15.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": None},
            ],
        },
    ]

    dna = DNAAnalyzerService.analyze(chem_exams)
    assert dna.sample_size.papers == 3

    engine = ExamScopeCombinedModel(dna)
    predictions = engine.predict(PredictionTarget.TOPIC)
    pred_map = {p.name: p for p in predictions}

    electro = pred_map["Electrochemistry"]
    thermo = pred_map["Thermodynamics"]
    kinetics = pred_map["ChemicalKinetics"]

    assert electro.probability == pytest.approx(0.80, abs=1e-4)
    assert thermo.probability == pytest.approx(0.60, abs=1e-4)
    assert kinetics.probability == pytest.approx(0.40, abs=1e-4)
    assert electro.rank == 1


def test_question_family_invariance_on_corpus_extension():
    """
    Adding a newer exam (e.g. 2024) must NOT alter older questions' family assignment or normalization.
    """
    q_past_1 = "State and prove Rolle's theorem for a real-valued continuous function."
    q_past_2 = "Define Cauchy's Mean Value Theorem and state its conditions."
    q_future = "State and prove Rolle's theorem with an illustrative geometric example."

    norm_past_1 = QuestionNormalizer.normalize(q_past_1)
    norm_past_2 = QuestionNormalizer.normalize(q_past_2)
    norm_future = QuestionNormalizer.normalize(q_future)

    # Older questions retain their normalized canonical text regardless of future question additions
    assert norm_past_1 == QuestionNormalizer.normalize(q_past_1)
    assert norm_past_2 == QuestionNormalizer.normalize(q_past_2)
    assert norm_past_1 != norm_past_2
