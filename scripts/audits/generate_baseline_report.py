"""
Corpus Health & Model Baseline Generation Script.
Implements:
- Section 17: Corpus Health Report
- Section 18: Model Baseline Report with MRR, Hit Rates, Brier Score, and Baseline Comparisons
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

from sqlalchemy import func
from backend.core.database import SessionLocal
from backend.core.version import (
    MODEL_VERSION, ENGINE_VERSION, CORPUS_VERSION, TAXONOMY_VERSION, CALIBRATION_METHOD
)
from backend.models.core import (
    Course, Exam, Question, Topic, QuestionFamily, QuestionFamilyMembership,
    Document, CurriculumMapping
)
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.prediction.engine import (
    ExamScopeCombinedModel, AllTimeFrequencyBaseline, RecentFrequencyBaseline,
    RecencyWeightedBaseline, MarksWeightedBaseline
)
from backend.services.prediction.backtester import BacktestEvaluator
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.api.endpoints.predictions import _build_historical_exam_payloads


def generate_corpus_health(db) -> Dict[str, Any]:
    print("\n" + "=" * 60)
    print("  MARKMINT CORPUS HEALTH AUDIT")
    print("=" * 60)

    # 1. Total indexed courses
    courses_count = db.query(func.count(Course.id)).scalar() or 0

    # 2. Total exams with verified year vs unverified year
    verified_year_exams = db.query(func.count(Exam.id)).filter(Exam.year != None, Exam.year > 0).scalar() or 0
    unverified_year_exams = db.query(func.count(Exam.id)).filter((Exam.year == None) | (Exam.year <= 0)).scalar() or 0
    total_exams = verified_year_exams + unverified_year_exams

    # 3. Questions mapped to topics vs unmapped
    total_questions = db.query(func.count(Question.id)).scalar() or 0
    # Questions with at least one topic
    mapped_questions = (
        db.query(func.count(func.distinct(Question.id)))
        .join(Question.topics)
        .scalar() or 0
    )
    unmapped_questions = total_questions - mapped_questions

    # 4. Question families >=2 occurrences vs singletons
    family_counts = (
        db.query(Question.family_id, func.count(Question.id))
        .filter(Question.family_id != None)
        .group_by(Question.family_id)
        .all()
    )
    multi_occurrence_families = sum(1 for f_id, count in family_counts if count >= 2)
    singleton_families = sum(1 for f_id, count in family_counts if count == 1)
    total_families = db.query(func.count(QuestionFamily.id)).scalar() or 0

    # 5. Extraction failures & retry candidates
    doc_stats = (
        db.query(Document.extraction_status, func.count(Document.id))
        .group_by(Document.extraction_status)
        .all()
    )
    doc_breakdown = {status or "UNKNOWN": count for status, count in doc_stats}
    extraction_failures = doc_breakdown.get("FAILED", 0)
    extraction_successes = doc_breakdown.get("COMPLETED", 0) + doc_breakdown.get("SUCCESS", 0)
    total_documents = sum(doc_breakdown.values())

    # 6. Canonical curriculum reconciliation summary
    curr_stats = (
        db.query(CurriculumMapping.status, func.count(CurriculumMapping.id))
        .group_by(CurriculumMapping.status)
        .all()
    )
    curr_breakdown = {status: count for status, count in curr_stats}
    total_curriculum_entries = sum(curr_breakdown.values())

    report = {
        "status": "HEALTHY",
        "generated_at": datetime.utcnow().isoformat(),
        "versions": {
            "model_version": MODEL_VERSION,
            "engine_version": ENGINE_VERSION,
            "corpus_version": CORPUS_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
        },
        "courses": {
            "total_indexed": courses_count,
        },
        "exams": {
            "total": total_exams,
            "verified_year": verified_year_exams,
            "unverified_year": unverified_year_exams,
            "verification_rate": round(verified_year_exams / total_exams, 4) if total_exams > 0 else 0,
        },
        "questions": {
            "total": total_questions,
            "mapped_to_topics": mapped_questions,
            "unmapped_questions": unmapped_questions,
            "topic_mapping_rate": round(mapped_questions / total_questions, 4) if total_questions > 0 else 0,
        },
        "question_families": {
            "total_defined": total_families,
            "multi_occurrence_ge_2": multi_occurrence_families,
            "singletons": singleton_families,
            "recurrence_ratio": round(multi_occurrence_families / total_families, 4) if total_families > 0 else 0,
        },
        "documents_and_ingestion": {
            "total_documents": total_documents,
            "extraction_successes": extraction_successes,
            "extraction_failures": extraction_failures,
            "breakdown": doc_breakdown,
        },
        "curriculum_reconciliation": {
            "total_entries": total_curriculum_entries,
            "matched": curr_breakdown.get("MATCHED", 0),
            "ambiguous": curr_breakdown.get("AMBIGUOUS", 0),
            "unmatched": curr_breakdown.get("UNMATCHED", 0),
        }
    }

    print(f"Courses Indexed:        {courses_count}")
    print(f"Exams Total:            {total_exams} (Verified: {verified_year_exams}, Unverified: {unverified_year_exams})")
    print(f"Questions Total:        {total_questions} (Mapped to Topics: {mapped_questions}, Unmapped: {unmapped_questions})")
    print(f"Question Families:      {total_families} (>=2 Recurrences: {multi_occurrence_families}, Singletons: {singleton_families})")
    print(f"Curriculum Entries:     {total_curriculum_entries} (Matched: {curr_breakdown.get('MATCHED', 0)}, Ambiguous: {curr_breakdown.get('AMBIGUOUS', 0)}, Unmatched: {curr_breakdown.get('UNMATCHED', 0)})")
    print(f"Extraction Pipeline:    {extraction_successes} Success, {extraction_failures} Failed out of {total_documents} Docs")

    os.makedirs(os.path.join(BASE_DIR, "data", "reports"), exist_ok=True)
    report_path = os.path.join(BASE_DIR, "data", "reports", "corpus_health.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Saved] Corpus Health Report -> {report_path}")

    return report


def calculate_mrr(predictions: List[Any], target_names: set) -> float:
    """Mean Reciprocal Rank: reciprocal of the rank of the first relevant prediction."""
    for rank, pred in enumerate(predictions, start=1):
        if pred.name in target_names:
            return 1.0 / rank
    return 0.0


def calculate_brier_score(predictions: List[Any], target_names: set) -> float:
    """Brier score for probabilistic calibration: mean squared error of predicted probabilities vs binary ground truth."""
    if not predictions:
        return 0.0
    squared_errors = []
    for pred in predictions:
        p_val = getattr(pred, "probability", None)
        if p_val is None:
            p_val = getattr(pred, "recurrence_probability", 0.5)
        if isinstance(p_val, str):
            try:
                p_val = float(p_val)
            except ValueError:
                p_val = 0.5
        y = 1.0 if pred.name in target_names else 0.0
        squared_errors.append((float(p_val) - y) ** 2)
    return round(sum(squared_errors) / len(squared_errors), 4)


def generate_model_baseline(db) -> Dict[str, Any]:
    print("\n" + "=" * 60)
    print("  MARKMINT WALK-FORWARD MODEL BASELINE BENCHMARK")
    print("=" * 60)

    courses = db.query(Course).all()
    evaluations = []
    
    # Model tracking aggregates
    model_aggregates: Dict[str, Dict[str, List[float]]] = {
        "ExamScopeCombined": {"hit@3": [], "hit@5": [], "hit@10": [], "mrr": [], "brier": [], "recall@5": []},
        "AllTimeFrequency": {"hit@3": [], "hit@5": [], "hit@10": [], "mrr": [], "brier": [], "recall@5": []},
        "RecentFrequency": {"hit@3": [], "hit@5": [], "hit@10": [], "mrr": [], "brier": [], "recall@5": []},
        "RecencyWeighted": {"hit@3": [], "hit@5": [], "hit@10": [], "mrr": [], "brier": [], "recall@5": []},
        "MarksWeighted": {"hit@3": [], "hit@5": [], "hit@10": [], "mrr": [], "brier": [], "recall@5": []},
    }

    total_target_year_evaluations = 0

    for course in courses:
        years = (
            db.query(Exam.year)
            .filter(Exam.course_id == course.id, Exam.year != None)
            .distinct()
            .order_by(Exam.year.asc())
            .all()
        )
        usable_years = [y[0] for y in years]
        if len(usable_years) < 2:
            continue

        for target_year in usable_years[1:]:
            context = HistoricalContext(course_id=course.id, cutoff_year=target_year)
            repo = HistoricalRepository(db, context)

            hist_exams_orm = repo.get_historical_exams()
            if not hist_exams_orm:
                continue

            hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)
            analyzer = DNAAnalyzerService()
            dna = analyzer.analyze(hist_exams_dicts)

            target_exams_orm = repo.get_target_exams()
            target_topics: Dict[str, Dict[str, Any]] = {}
            for exam in target_exams_orm:
                for sec in exam.sections:
                    for q in sec.questions:
                        m = q.marks or 0.0
                        for top in q.topics:
                            t = target_topics.setdefault(top.name, {"name": top.name, "count": 0, "marks": 0.0})
                            t["count"] += 1
                            if not q.is_alternative:
                                t["marks"] += m

            target_items = list(target_topics.values())
            if not target_items:
                continue

            total_target_year_evaluations += 1
            target_names = {t["name"] for t in target_items}

            models = {
                "ExamScopeCombined": ExamScopeCombinedModel(dna),
                "AllTimeFrequency": AllTimeFrequencyBaseline(dna),
                "RecentFrequency": RecentFrequencyBaseline(dna),
                "RecencyWeighted": RecencyWeightedBaseline(dna),
                "MarksWeighted": MarksWeightedBaseline(dna),
            }

            for model_name, model in models.items():
                preds = model.predict(PredictionTarget.TOPIC)
                metrics = BacktestEvaluator.evaluate(preds, target_items, k_values=[3, 5, 10])
                
                # Hit rate: 1 if at least one hit in top-K else 0
                hit_3 = 1.0 if any(p.name in target_names for p in preds[:3]) else 0.0
                hit_5 = 1.0 if any(p.name in target_names for p in preds[:5]) else 0.0
                hit_10 = 1.0 if any(p.name in target_names for p in preds[:10]) else 0.0
                mrr = calculate_mrr(preds, target_names)
                brier = calculate_brier_score(preds, target_names)

                model_aggregates[model_name]["hit@3"].append(hit_3)
                model_aggregates[model_name]["hit@5"].append(hit_5)
                model_aggregates[model_name]["hit@10"].append(hit_10)
                model_aggregates[model_name]["mrr"].append(mrr)
                model_aggregates[model_name]["brier"].append(brier)
                model_aggregates[model_name]["recall@5"].append(metrics.get("Recall@5", 0.0))

                evaluations.append({
                    "course_name": course.name,
                    "target_year": target_year,
                    "model": model_name,
                    "historical_papers": len(hist_exams_orm),
                    "target_papers": len(target_exams_orm),
                    "hit@3": hit_3,
                    "hit@5": hit_5,
                    "hit@10": hit_10,
                    "mrr": round(mrr, 4),
                    "brier": brier,
                    "metrics": metrics,
                })

    # Summary table across models
    summary_comparison = {}
    for m_name, vals in model_aggregates.items():
        n = len(vals["hit@5"])
        if n > 0:
            summary_comparison[m_name] = {
                "evaluations_count": n,
                "hit_rate@3": round(sum(vals["hit@3"]) / n, 4),
                "hit_rate@5": round(sum(vals["hit@5"]) / n, 4),
                "hit_rate@10": round(sum(vals["hit@10"]) / n, 4),
                "mean_reciprocal_rank": round(sum(vals["mrr"]) / n, 4),
                "brier_score": round(sum(vals["brier"]) / n, 4),
                "avg_recall@5": round(sum(vals["recall@5"]) / n, 4),
            }

    report = {
        "status": "COMPLETED",
        "generated_at": datetime.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "engine_version": ENGINE_VERSION,
        "calibration_method": CALIBRATION_METHOD,
        "reproduction_command": "python scripts/generate_baseline_report.py",
        "target_year_evaluations_completed": total_target_year_evaluations,
        "model_summary_comparison": summary_comparison,
        "evaluations": evaluations,
    }

    print(f"\nCompleted {total_target_year_evaluations} walk-forward cutoff evaluations.")
    print("\nModel Baseline Performance Comparison:")
    print(f"{'Model':<24} | {'Hit@3':<8} | {'Hit@5':<8} | {'Hit@10':<8} | {'MRR':<8} | {'Brier':<8} | {'Recall@5':<8}")
    print("-" * 85)
    for m_name, s in summary_comparison.items():
        print(f"{m_name:<24} | {s['hit_rate@3']:<8.4f} | {s['hit_rate@5']:<8.4f} | {s['hit_rate@10']:<8.4f} | {s['mean_reciprocal_rank']:<8.4f} | {s['brier_score']:<8.4f} | {s['avg_recall@5']:<8.4f}")

    report_path = os.path.join(BASE_DIR, "data", "reports", "model_baseline.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Saved] Model Baseline Report -> {report_path}")

    return report


def main():
    db = SessionLocal()
    try:
        generate_corpus_health(db)
        generate_model_baseline(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
