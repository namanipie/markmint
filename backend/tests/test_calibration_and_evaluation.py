import pytest
from backend.services.prediction.engine import ExamScopeCombinedModel, PredictionResult
from backend.services.prediction.context import PredictionTarget
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.prediction.backtester import BacktestEvaluator
from backend.core.version import (
    MODEL_VERSION,
    CALIBRATION_METHOD,
    SCORE_SEMANTICS
)


def test_laplace_probability_calibration():
    # 3 exams: Topic A appears in all 3, Topic B appears in 1, Topic C appears in 0
    exams = [
        {
            "id": "e1", "year": 2021, "exam_type": "FINAL",
            "questions": [
                {"id": "q1", "topic": "Topic A", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5},
                {"id": "q2", "topic": "Topic B", "marks": 5.0, "is_alternative": False, "question_type": "SHORT", "repetition_type": "singleton", "family_name": None, "difficulty": 0.3},
            ]
        },
        {
            "id": "e2", "year": 2022, "exam_type": "FINAL",
            "questions": [
                {"id": "q3", "topic": "Topic A", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5},
            ]
        },
        {
            "id": "e3", "year": 2023, "exam_type": "FINAL",
            "questions": [
                {"id": "q4", "topic": "Topic A", "marks": 10.0, "is_alternative": False, "question_type": "LONG", "repetition_type": "singleton", "family_name": None, "difficulty": 0.5},
            ]
        }
    ]

    dna = DNAAnalyzerService.analyze(exams)
    engine = ExamScopeCombinedModel(dna)
    preds = engine.predict(PredictionTarget.TOPIC)

    pred_map = {p.name: p for p in preds}

    # Topic A: appeared in 3 of 3 papers -> (3 + 1) / (3 + 2) = 4/5 = 0.8
    assert "Topic A" in pred_map
    top_a = pred_map["Topic A"]
    assert top_a.probability == 0.8
    assert top_a.papers_analyzed == 3
    assert top_a.papers_with_topic == 3
    assert top_a.score_semantics == SCORE_SEMANTICS
    assert top_a.calibration_method == CALIBRATION_METHOD

    # Topic B: appeared in 1 of 3 papers -> (1 + 1) / (3 + 2) = 2/5 = 0.4
    assert "Topic B" in pred_map
    top_b = pred_map["Topic B"]
    assert top_b.probability == 0.4
    assert top_b.papers_analyzed == 3
    assert top_b.papers_with_topic == 1


def test_backtest_evaluator_k_values_and_metrics():
    predictions = [
        PredictionResult(target="topic", name="Trees", rank=1, score=0.9, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Graphs", rank=2, score=0.8, confidence="HIGH", evidence={}),
        PredictionResult(target="topic", name="Sorting", rank=3, score=0.7, confidence="MEDIUM", evidence={}),
        PredictionResult(target="topic", name="Hashing", rank=4, score=0.6, confidence="MEDIUM", evidence={}),
        PredictionResult(target="topic", name="DP", rank=5, score=0.5, confidence="LOW", evidence={}),
    ]

    target_items = [
        {"name": "Trees", "marks": 20.0, "count": 2},
        {"name": "Graphs", "marks": 15.0, "count": 1},
        {"name": "Greedy", "marks": 10.0, "count": 1},
    ]

    eval_result = BacktestEvaluator.evaluate(predictions, target_items, k_values=[3, 5, 10])

    # Should evaluate top_3, top_5, top_10 with precision, recall, marks coverage, question coverage
    assert "Precision@3" in eval_result
    assert "Recall@3" in eval_result
    assert "Marks_Coverage@3" in eval_result
    assert "Question_Coverage@3" in eval_result

    assert "Precision@5" in eval_result
    assert "Precision@10" in eval_result

    # At top_3: hits are Trees and Graphs (2 out of 3 predictions, 2 out of 3 target items)
    assert eval_result["Precision@3"] == 0.6667
    assert eval_result["Recall@3"] == 0.6667
    # Marks coverage: (20 + 15) / 45 = 35 / 45 = 0.7778
    assert eval_result["Marks_Coverage@3"] == 0.7778
    # Question coverage: (2 + 1) / 4 = 3 / 4 = 0.75
    assert eval_result["Question_Coverage@3"] == 0.75
