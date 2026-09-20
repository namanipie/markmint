"""
Rigorous Historical Prediction Backtesting Engine for MarkMint (Phase 11).

Guarantees:
1. Strict Temporal Isolation: For every target exam at year T, HistoricalRepository
   and HistoricalContext only admit evidence strictly from Exam.year < T.
2. Target Exam Secrecy: Target exam questions, topics, families, and documents
   are held-out and never visible to the prediction engine.
3. Assessment Scoping: Evaluates by specific assessment cycle (ENDSEM, CT1, CT2, ALL)
   without conflating fundamentally different assessment contexts.
4. Separate Mapping QC from Prediction Quality: Unmapped target questions are recorded
   in mapping QC (mapping rate) and do not penalize model question/marks coverage.
5. Sample Size Guardrails: Evaluates and flags SUFFICIENT_HISTORY, LIMITED_HISTORY,
   and INSUFFICIENT_HISTORY explicitly.
6. Empirical Probability Calibration: Verifies Laplace-smoothed empirical recurrence
   probabilities: P = (papers_with_topic + 1) / (sample_papers + 2).
7. Topic and Question Family Modes: Evaluates both topic and question-family predictions.
   Reports INSUFFICIENT_EVIDENCE when families are absent or insufficient.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import Session, selectinload
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Document
from backend.services.prediction.context import HistoricalContext, PredictionTarget
from backend.services.prediction.repository import HistoricalRepository
from backend.services.dna.analyzer import DNAAnalyzerService
from backend.services.observed_assessment_coverage import identify_exam_assessment
from backend.api.endpoints.predictions import _build_historical_exam_payloads
from backend.services.prediction.engine import (
    AllTimeFrequencyBaseline,
    RecentFrequencyBaseline,
    RecencyWeightedBaseline,
    MarksWeightedBaseline,
    FamilyRecurrenceBaseline,
    ExamScopeCombinedModel,
    PredictionResult
)


class EvidenceSufficiencyState:
    SUFFICIENT_HISTORY = "SUFFICIENT_HISTORY"  # >= 3 papers and >= 20 questions
    LIMITED_HISTORY = "LIMITED_HISTORY"        # 1-2 papers or 5-19 questions
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY" # 0 papers or < 5 questions


class BacktestEvaluator:
    @staticmethod
    def evaluate(predictions: list, target_items: list, k_values: list = [3, 5, 10]) -> dict:
        """
        Evaluates predictions against target items.
        predictions: list of PredictionResult
        target_items: list of dicts with 'name', 'marks', 'count' for the target exam
        """
        results = {}
        target_names = {t['name'] for t in target_items if t.get('name')}
        total_target_unique = len(target_names)
        total_target_questions = sum(t.get('count', 0) for t in target_items)
        total_target_marks = sum(t.get('marks', 0.0) for t in target_items)
        
        for k in k_values:
            top_k = predictions[:k]
            top_k_names = {p.name for p in top_k if p.name}
            
            # Intersection (True Positives)
            hits = top_k_names.intersection(target_names)
            
            # Metrics
            precision = len(hits) / k if k > 0 else 0.0
            recall = len(hits) / total_target_unique if total_target_unique > 0 else 0.0
            
            # Coverage
            covered_questions = sum(t.get('count', 0) for t in target_items if t.get('name') in top_k_names)
            covered_marks = sum(t.get('marks', 0.0) for t in target_items if t.get('name') in top_k_names)
            
            q_coverage = covered_questions / total_target_questions if total_target_questions > 0 else 0.0
            m_coverage = covered_marks / total_target_marks if total_target_marks > 0 else 0.0
            
            # Formally named metrics
            results[f"Precision@{k}"] = round(precision, 4)
            results[f"Recall@{k}"] = round(recall, 4)
            results[f"Marks_Coverage@{k}"] = round(m_coverage, 4)
            results[f"Question_Coverage@{k}"] = round(q_coverage, 4)

            # Shorthand for backward compatibility
            results[f"P@{k}"] = round(precision, 4)
            results[f"R@{k}"] = round(recall, 4)
            results[f"Q_Cov@{k}"] = round(q_coverage, 4)
            results[f"M_Cov@{k}"] = round(m_coverage, 4)
            
        return results

    @staticmethod
    def verify_probability_calibration(predictions: List[PredictionResult], sample_papers: int) -> bool:
        """
        Verifies Laplace-smoothed empirical recurrence probability:
        P = (papers_with_topic + 1) / (sample_papers + 2)
        """
        if sample_papers <= 0:
            return True
        for p in predictions:
            expected_p = round((p.papers_with_topic + 1.0) / (sample_papers + 2.0), 4)
            if abs(p.probability - expected_p) > 1e-3:
                return False
        return True


class BacktestHarness:
    def __init__(self, db: Optional[Session] = None):
        self._owned_session = db is None
        self.db = db if db is not None else SessionLocal()

    def close(self):
        if self._owned_session:
            self.db.close()

    @staticmethod
    def classify_evidence_sufficiency(hist_papers: int, hist_questions: int) -> str:
        """Categorize historical evidence volume into strict non-misleading tiers."""
        if hist_papers >= 3 and hist_questions >= 20:
            return EvidenceSufficiencyState.SUFFICIENT_HISTORY
        elif hist_papers >= 1 and hist_questions >= 5:
            return EvidenceSufficiencyState.LIMITED_HISTORY
        else:
            return EvidenceSufficiencyState.INSUFFICIENT_HISTORY

    def extract_target_exam_data(self, target_exam: Exam) -> Dict[str, Any]:
        """
        Extract ground truth from target exam, strictly separating mapped and unmapped questions.
        Unmapped questions are tracked in QC metadata and do NOT penalize prediction metrics.
        """
        topics_dict: Dict[str, Dict[str, Any]] = {}
        units_dict: Dict[str, Dict[str, Any]] = {}
        families_dict: Dict[str, Dict[str, Any]] = {}

        total_questions = 0
        mapped_questions = 0
        unmapped_questions = 0
        total_marks = 0.0
        mapped_marks = 0.0
        unmapped_marks = 0.0

        for section in (target_exam.sections or []):
            for q in (section.questions or []):
                total_questions += 1
                m = float(q.marks or 0.0)
                if not q.is_alternative:
                    total_marks += m

                q_topics = getattr(q, "topics", []) or []
                if len(q_topics) > 0:
                    mapped_questions += 1
                    if not q.is_alternative:
                        mapped_marks += m
                    for top in q_topics:
                        t = topics_dict.setdefault(top.name, {"name": top.name, "count": 0, "marks": 0.0})
                        t["count"] += 1
                        if not q.is_alternative:
                            t["marks"] += m

                        if getattr(top, "unit", None):
                            u_name = top.unit.name
                            u = units_dict.setdefault(u_name, {"name": u_name, "count": 0, "marks": 0.0})
                            u["count"] += 1
                            if not q.is_alternative:
                                u["marks"] += m
                else:
                    unmapped_questions += 1
                    if not q.is_alternative:
                        unmapped_marks += m

                if q.family_id:
                    fam_name = q.family.canonical_name if q.family else str(q.family_id)
                    f = families_dict.setdefault(fam_name, {"name": fam_name, "count": 0, "marks": 0.0})
                    f["count"] += 1
                    if not q.is_alternative:
                        f["marks"] += m

        mapping_rate = round(mapped_questions / total_questions, 4) if total_questions > 0 else 0.0

        return {
            "qc": {
                "target_question_count": total_questions,
                "mapped_question_count": mapped_questions,
                "unmapped_question_count": unmapped_questions,
                "mapping_rate": mapping_rate,
                "total_marks": round(total_marks, 2),
                "mapped_marks": round(mapped_marks, 2),
                "unmapped_marks": round(unmapped_marks, 2),
            },
            PredictionTarget.TOPIC: list(topics_dict.values()),
            PredictionTarget.UNIT: list(units_dict.values()),
            PredictionTarget.FAMILY: list(families_dict.values()),
        }

    def run(self, course_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Executes rigorous backtesting across all eligible courses and historical target exams.
        """
        query = self.db.query(Course)
        if course_ids:
            query = query.filter(Course.id.in_(course_ids))
        courses = query.order_by(Course.id).all()

        detailed_evaluations: List[Dict[str, Any]] = []
        sparse_cases: List[Dict[str, Any]] = []

        total_courses_count = len(courses)
        evaluated_target_exams = 0
        total_predictions_run = 0

        for course in courses:
            # Fetch all candidate exams with valid non-null years
            all_exams = (
                self.db.query(Exam)
                .options(
                    selectinload(Exam.sections)
                    .selectinload(Section.questions)
                    .selectinload(Question.topics)
                    .selectinload(Topic.unit),
                    selectinload(Exam.sections)
                    .selectinload(Section.questions)
                    .selectinload(Question.family),
                    selectinload(Exam.sections)
                    .selectinload(Section.questions)
                    .selectinload(Question.memberships),
                    selectinload(Exam.document),
                )
                .filter(Exam.course_id == course.id, Exam.year != None)
                .order_by(Exam.year.asc(), Exam.id.asc())
                .all()
            )

            if len(all_exams) < 2:
                sparse_cases.append({
                    "course_id": course.id,
                    "canonical_code": course.canonical_code,
                    "course_name": course.name,
                    "reason": "Course has fewer than 2 dated exam papers in corpus",
                    "total_dated_exams": len(all_exams)
                })
                continue

            # Candidate target exams: exams that can be evaluated against prior history
            for target_exam in all_exams:
                ident = identify_exam_assessment(target_exam, course.id)
                cycle = ident.student_cycle or "ENDSEM"
                target_year = target_exam.year
                doc_title = target_exam.document.title if target_exam.document else f"Exam {target_exam.id}"

                # 1. Scoped Historical Repository for this target exam's cycle
                context_cycle = HistoricalContext(
                    course_id=course.id,
                    cutoff_year=target_year,
                    assessment_cycle=cycle,
                    track_id=target_exam.track_id
                )
                repo_cycle = HistoricalRepository(self.db, context_cycle)
                hist_exams_orm = repo_cycle.get_historical_exams()

                # If no historical exams in this specific cycle, check cycle="ALL"
                used_cycle = cycle
                if len(hist_exams_orm) == 0:
                    context_all = HistoricalContext(
                        course_id=course.id,
                        cutoff_year=target_year,
                        assessment_cycle="ALL",
                        track_id=target_exam.track_id
                    )
                    repo_all = HistoricalRepository(self.db, context_all)
                    hist_exams_orm_all = repo_all.get_historical_exams()
                    if len(hist_exams_orm_all) > 0:
                        hist_exams_orm = hist_exams_orm_all
                        used_cycle = "ALL"

                hist_exam_count = len(hist_exams_orm)
                hist_question_count = sum(
                    len(q) for e in hist_exams_orm for s in (e.sections or []) for q in [s.questions]
                )

                # Classify sample size sufficiency
                sufficiency = self.classify_evidence_sufficiency(hist_exam_count, hist_question_count)

                # Extract ground truth from target exam
                target_data = self.extract_target_exam_data(target_exam)
                qc_meta = target_data["qc"]

                # If insufficient history, record as explicit INSUFFICIENT_HISTORY case without fabricating metrics
                if sufficiency == EvidenceSufficiencyState.INSUFFICIENT_HISTORY:
                    sparse_cases.append({
                        "course_id": course.id,
                        "canonical_code": course.canonical_code,
                        "course_name": course.name,
                        "target_exam_id": target_exam.id,
                        "target_year": target_year,
                        "assessment_cycle": cycle,
                        "evidence_sufficiency": sufficiency,
                        "historical_exam_count": hist_exam_count,
                        "historical_question_count": hist_question_count,
                        "reason": "Zero or fewer than 5 historical questions available prior to target exam"
                    })
                    continue

                evaluated_target_exams += 1

                # 2. Build DNA from Frozen Historical State
                hist_exams_dicts = _build_historical_exam_payloads(hist_exams_orm)
                analyzer = DNAAnalyzerService()
                dna = analyzer.analyze(hist_exams_dicts)

                # 3. Initialize Models
                topic_models = {
                    "AllTimeFrequencyBaseline": AllTimeFrequencyBaseline(dna),
                    "RecentFrequencyBaseline": RecentFrequencyBaseline(dna),
                    "RecencyWeightedBaseline": RecencyWeightedBaseline(dna),
                    "MarksWeightedBaseline": MarksWeightedBaseline(dna),
                    "ExamScopeCombinedModel": ExamScopeCombinedModel(dna),
                }

                family_models = {
                    "FamilyRecurrenceBaseline": FamilyRecurrenceBaseline(dna),
                    "ExamScopeCombinedModel": ExamScopeCombinedModel(dna),
                }

                # 4. Evaluate Topic Predictions
                target_topics = target_data[PredictionTarget.TOPIC]
                for model_name, model in topic_models.items():
                    preds = model.predict(PredictionTarget.TOPIC)
                    calib_ok = BacktestEvaluator.verify_probability_calibration(preds, hist_exam_count)
                    eval_metrics = BacktestEvaluator.evaluate(preds, target_topics, k_values=[3, 5, 10])
                    total_predictions_run += 1

                    detailed_evaluations.append({
                        "course": course.name,
                        "canonical_code": course.canonical_code,
                        "course_id": course.id,
                        "target_exam_id": target_exam.id,
                        "target_exam_title": doc_title,
                        "target_year": target_year,
                        "assessment_cycle": used_cycle,
                        "raw_assessment_type": target_exam.assessment_type,
                        "mode": "topic",
                        "model": model_name,
                        "status": "COMPLETED",
                        "evidence_sufficiency": sufficiency,
                        "historical_exam_count": hist_exam_count,
                        "historical_question_count": hist_question_count,
                        "probability_calibration_verified": calib_ok,
                        "qc": qc_meta,
                        "metrics": eval_metrics
                    })

                # 5. Evaluate Family Predictions
                target_families = target_data[PredictionTarget.FAMILY]
                family_supported = (len(target_families) > 0) and (len(dna.families) > 0)

                for model_name, model in family_models.items():
                    if not family_supported:
                        detailed_evaluations.append({
                            "course": course.name,
                            "canonical_code": course.canonical_code,
                            "course_id": course.id,
                            "target_exam_id": target_exam.id,
                            "target_exam_title": doc_title,
                            "target_year": target_year,
                            "assessment_cycle": used_cycle,
                            "raw_assessment_type": target_exam.assessment_type,
                            "mode": "family",
                            "model": model_name,
                            "status": "INSUFFICIENT_EVIDENCE",
                            "reason": "Target exam or historical context lacks sufficient question family memberships",
                            "evidence_sufficiency": sufficiency,
                            "historical_exam_count": hist_exam_count,
                            "historical_question_count": hist_question_count,
                            "qc": qc_meta,
                            "metrics": None
                        })
                    else:
                        preds = model.predict(PredictionTarget.FAMILY)
                        eval_metrics = BacktestEvaluator.evaluate(preds, target_families, k_values=[3, 5, 10])
                        total_predictions_run += 1

                        detailed_evaluations.append({
                            "course": course.name,
                            "canonical_code": course.canonical_code,
                            "course_id": course.id,
                            "target_exam_id": target_exam.id,
                            "target_exam_title": doc_title,
                            "target_year": target_year,
                            "assessment_cycle": used_cycle,
                            "raw_assessment_type": target_exam.assessment_type,
                            "mode": "family",
                            "model": model_name,
                            "status": "COMPLETED",
                            "evidence_sufficiency": sufficiency,
                            "historical_exam_count": hist_exam_count,
                            "historical_question_count": hist_question_count,
                            "qc": qc_meta,
                            "metrics": eval_metrics
                        })

        # 6. Aggregate Summary Statistics
        completed_topic_evals = [e for e in detailed_evaluations if e["mode"] == "topic" and e["status"] == "COMPLETED"]
        completed_family_evals = [e for e in detailed_evaluations if e["mode"] == "family" and e["status"] == "COMPLETED"]

        def calc_averages(eval_list: List[Dict[str, Any]]) -> Dict[str, float]:
            if not eval_list:
                return {}
            n = len(eval_list)
            keys = [
                "Precision@3", "Precision@5", "Precision@10",
                "Recall@3", "Recall@5", "Recall@10",
                "Marks_Coverage@3", "Marks_Coverage@5", "Marks_Coverage@10",
                "Question_Coverage@3", "Question_Coverage@5", "Question_Coverage@10"
            ]
            return {
                k: round(sum(e["metrics"][k] for e in eval_list) / n, 4)
                for k in keys
            }

        # By Model
        model_summary: Dict[str, Dict[str, Any]] = {}
        for m in ["AllTimeFrequencyBaseline", "RecentFrequencyBaseline", "RecencyWeightedBaseline", "MarksWeightedBaseline", "ExamScopeCombinedModel"]:
            m_evals = [e for e in completed_topic_evals if e["model"] == m]
            model_summary[m] = {
                "evaluation_count": len(m_evals),
                "averages": calc_averages(m_evals)
            }

        fam_m_evals = [e for e in completed_family_evals if e["model"] == "FamilyRecurrenceBaseline"]
        model_summary["FamilyRecurrenceBaseline"] = {
            "evaluation_count": len(fam_m_evals),
            "averages": calc_averages(fam_m_evals) if fam_m_evals else "INSUFFICIENT_EVIDENCE"
        }

        # By Assessment Cycle
        cycle_summary: Dict[str, Dict[str, Any]] = {}
        distinct_cycles = list(set(e["assessment_cycle"] for e in completed_topic_evals))
        for cyc in distinct_cycles:
            cyc_evals = [e for e in completed_topic_evals if e["assessment_cycle"] == cyc and e["model"] == "ExamScopeCombinedModel"]
            cycle_summary[cyc] = {
                "target_exams": len(set(e["target_exam_id"] for e in cyc_evals)),
                "averages": calc_averages(cyc_evals)
            }

        # By Sufficiency State
        sufficiency_summary: Dict[str, Dict[str, Any]] = {}
        for suff in [EvidenceSufficiencyState.SUFFICIENT_HISTORY, EvidenceSufficiencyState.LIMITED_HISTORY]:
            suff_evals = [e for e in completed_topic_evals if e["evidence_sufficiency"] == suff and e["model"] == "ExamScopeCombinedModel"]
            sufficiency_summary[suff] = {
                "evaluation_count": len(suff_evals),
                "averages": calc_averages(suff_evals)
            }

        report_payload = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "total_courses_evaluated": total_courses_count,
                "eligible_target_exams_evaluated": evaluated_target_exams,
                "total_evaluation_records": len(detailed_evaluations),
                "total_sparse_cases": len(sparse_cases),
                "k_values": [3, 5, 10],
                "probability_calibration_formula": "P = (papers_with_topic + 1) / (sample_papers + 2)"
            },
            "model_summary": model_summary,
            "cycle_summary": cycle_summary,
            "sufficiency_summary": sufficiency_summary,
            "sparse_cases": sparse_cases,
            "detailed_evaluations": detailed_evaluations
        }

        # 7. Write Persistent JSON Report
        os.makedirs("data/reports", exist_ok=True)
        report_path = "data/reports/backtest_results.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)

        print(f"Backtest complete. Evaluated {evaluated_target_exams} target exams across {total_courses_count} courses.")
        print(f"Results written to {report_path}")

        return report_payload


if __name__ == "__main__":
    harness = BacktestHarness()
    try:
        res = harness.run()
        print(f"Generated {len(res['detailed_evaluations'])} backtest records.")
    finally:
        harness.close()
