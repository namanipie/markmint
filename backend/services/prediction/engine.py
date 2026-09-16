from typing import List, Dict, Any, Tuple, Optional
from backend.services.dna.analyzer import ExamDNA, DataSufficiency
from backend.services.prediction.context import PredictionTarget
from backend.core.version import SCORE_SEMANTICS, CALIBRATION_METHOD

class PredictionResult:
    def __init__(
        self,
        target: str,
        name: str,
        rank: int,
        score: float,
        confidence: str,
        evidence: dict,
        prediction_score: Optional[float] = None,
        probability: Optional[float] = None,
        historical_occurrences: int = 0,
        recent_occurrences: int = 0,
        last_seen_year: Optional[int] = None,
        marks_seen: float = 0.0,
        family_recurrence_score: float = 0.0,
        recent_frequency_score: float = 0.0,
        recency_score: float = 0.0,
        marks_score: float = 0.0,
        evidence_count: int = 0,
        reason_codes: Optional[List[str]] = None,
        explanation: Optional[str] = None,
        score_semantics: str = SCORE_SEMANTICS,
        calibration_method: str = CALIBRATION_METHOD,
        evidence_sufficiency: str = "SUFFICIENT",
        papers_analyzed: int = 0,
        papers_with_topic: int = 0,
        supporting_questions: Optional[List[Dict[str, Any]]] = None,
    ):
        self.target = target  # 'topic', 'unit', 'family', 'concept'
        self.name = name
        self.rank = rank
        self.score = score
        self.confidence = confidence
        self.evidence = evidence or {}

        # Structured explainability & calibration fields
        self.prediction_score = round(float(prediction_score if prediction_score is not None else score), 4)
        self.probability = round(float(probability if probability is not None else min(1.0, max(0.0, score))), 4)
        self.score_semantics = score_semantics
        self.calibration_method = calibration_method
        self.evidence_sufficiency = evidence_sufficiency
        self.papers_analyzed = int(papers_analyzed)
        self.papers_with_topic = int(papers_with_topic)
        self.supporting_questions = supporting_questions or []

        self.historical_occurrences = int(historical_occurrences or self.evidence.get("occurrences", 0))
        self.recent_occurrences = int(recent_occurrences or self.evidence.get("recent_occurrences", 0))
        self.last_seen_year = last_seen_year or (int(self.evidence["last_seen"]) if str(self.evidence.get("last_seen", "")).isdigit() else None)
        self.marks_seen = float(marks_seen or self.evidence.get("total_marks", 0.0))
        self.family_recurrence_score = round(float(family_recurrence_score or self.evidence.get("family_score", 0.0)), 4)
        self.recent_frequency_score = round(float(recent_frequency_score or self.evidence.get("recent_freq", 0.0)), 4)
        self.recency_score = round(float(recency_score or (0.7 * self.recent_frequency_score + 0.3 * self.evidence.get("hist_freq", 0.0))), 4)
        self.marks_score = round(float(marks_score or self.evidence.get("marks_weight", 0.0)), 4)
        self.evidence_count = int(evidence_count or self.historical_occurrences)
        self.reason_codes = reason_codes or self.evidence.get("reason_codes", [])
        self.explanation = explanation or self.evidence.get("explanation", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "name": self.name,
            "category": self.target,
            "score": self.score,
            "prediction_score": self.prediction_score,
            "probability": self.probability,
            "confidence": self.confidence,
            "score_semantics": self.score_semantics,
            "calibration_method": self.calibration_method,
            "evidence_sufficiency": self.evidence_sufficiency,
            "papers_analyzed": self.papers_analyzed,
            "papers_with_topic": self.papers_with_topic,
            "supporting_questions": self.supporting_questions,
            "historyCount": self.historical_occurrences,
            "historical_occurrences": self.historical_occurrences,
            "recent_occurrences": self.recent_occurrences,
            "last_seen_year": self.last_seen_year,
            "lastSeen": str(self.last_seen_year) if self.last_seen_year else "Multiple",
            "marks_seen": self.marks_seen,
            "family_recurrence_score": self.family_recurrence_score,
            "recent_frequency_score": self.recent_frequency_score,
            "recency_score": self.recency_score,
            "marks_score": self.marks_score,
            "evidence_count": self.evidence_count,
            "reason_codes": self.reason_codes,
            "explanation": self.explanation,
            "evidence_details": self.evidence,
        }

class BaseModel:
    def __init__(self, dna: ExamDNA):
        self.dna = dna

    def predict_topics(self) -> List[PredictionResult]:
        return []
        
    def predict_units(self) -> List[PredictionResult]:
        return []
        
    def predict_families(self) -> List[PredictionResult]:
        return []
        
    def predict(self, target_type: str) -> List[PredictionResult]:
        if target_type == PredictionTarget.TOPIC:
            return self.predict_topics()
        elif target_type == PredictionTarget.UNIT:
            return self.predict_units()
        elif target_type == PredictionTarget.FAMILY:
            return self.predict_families()
        return []
        
    def _rank_and_format(self, scored_items: List[Tuple[str, float, dict]], target: str) -> List[PredictionResult]:
        # Sort by score descending
        scored_items.sort(key=lambda x: x[1], reverse=True)
        results = []
        sample_papers = self.dna.sample_size.papers if (self.dna and hasattr(self.dna, "sample_size")) else 0
        total_sample_q = self.dna.sample_size.questions if (self.dna and hasattr(self.dna, "sample_size")) else 0

        for rank, (name, score, evidence) in enumerate(scored_items, start=1):
            # Derive evidence metrics
            hist_occ = int(evidence.get("occurrences", 0))
            recent_occ = int(evidence.get("recent_occurrences", 0))
            recent_f = float(evidence.get("recent_freq", 0.0))
            hist_f = float(evidence.get("hist_freq", 0.0))
            marks_w = float(evidence.get("marks_weight", 0.0))
            marks_seen = float(evidence.get("total_marks", 0.0))
            paper_cov = float(evidence.get("paper_coverage", 0.0))
            last_seen = evidence.get("last_seen")
            papers_with_topic = int(evidence.get("papers_with_topic", round(paper_cov * sample_papers)))

            # Confidence strictly reflects evidence volume, recency presence, and sample stability
            if sample_papers <= 1:
                conf = "INSUFFICIENT"
            elif target == PredictionTarget.FAMILY and evidence.get("sample_size", 0) < 3:
                conf = "INSUFFICIENT"
            elif sample_papers <= 2:
                conf = "LOW" if hist_occ >= 1 else "INSUFFICIENT"
            else:
                # sample_papers >= 3
                if recent_occ == 0 and sample_papers >= 4 and hist_occ <= 1:
                    conf = "LOW"
                elif (sample_papers >= 5 and (papers_with_topic >= 3 or hist_occ >= 4 or paper_cov >= 0.6)) or (score > 0.7 and hist_occ >= 2):
                    conf = "HIGH"
                elif score > 0.4 or papers_with_topic >= 2 or hist_occ >= 2:
                    conf = "MEDIUM"
                else:
                    conf = "LOW"
            calibrated_prob = round((papers_with_topic + 1.0) / (sample_papers + 2.0), 4) if sample_papers > 0 else 0.5
            evidence_sufficiency = "INSUFFICIENT" if sample_papers <= 1 else ("LIMITED" if sample_papers <= 2 else "SUFFICIENT")

            reason_codes = []
            if sample_papers <= 1:
                reason_codes.append("INSUFFICIENT_EVIDENCE")
            elif sample_papers >= 3 and hist_occ >= 2:
                reason_codes.append("SUFFICIENT_HISTORY")

            if hist_occ >= 4 and marks_seen >= 20.0:
                reason_codes.append("HIGH_EVIDENCE")
            elif hist_occ < 2 or sample_papers < 2:
                reason_codes.append("LOW_EVIDENCE")

            if recent_f > 0.15 or recent_occ >= 1:
                reason_codes.append("RECENTLY_REPEATED")
            if hist_f >= 0.20 or hist_occ >= 3:
                reason_codes.append("HIGH_FREQUENCY")
            if marks_w > 0.15 or evidence.get("average_marks", 0.0) >= 8.0:
                reason_codes.append("HIGH_MARK_WEIGHT")
            if target == PredictionTarget.FAMILY and hist_occ >= 2:
                reason_codes.append("QUESTION_FAMILY_RECURRING")
            if hist_occ > 0 and recent_occ == 0 and recent_f == 0.0:
                reason_codes.append("LONG_ABSENCE")
            if marks_w > 0.15 and hist_occ >= 2 and (recent_occ == 0 and recent_f == 0.0):
                reason_codes.append("CONFLICTING_SIGNALS")

            # Deterministic explanation string
            if target == PredictionTarget.FAMILY:
                explanation = f"Question family with {hist_occ} historical occurrence(s)"
                if last_seen and str(last_seen) != "Unknown":
                    explanation += f", last seen in {last_seen}."
                else:
                    explanation += "."
            elif "CONFLICTING_SIGNALS" in reason_codes:
                explanation = f"Conflicting signals: significant historical weight ({marks_seen:.0f} marks), but unrepresented in recent examinations."
            elif "LOW_EVIDENCE" in reason_codes:
                explanation = f"Appeared in {hist_occ} question(s). Limited examination history ({sample_papers} paper(s) indexed)."
            elif "LONG_ABSENCE" in reason_codes:
                explanation = f"Historically appeared in {hist_occ} question(s) ({marks_seen:.0f} marks total), but absent from recent examinations."
            elif "RECENTLY_REPEATED" in reason_codes and "HIGH_FREQUENCY" in reason_codes:
                papers_num = max(1, int(round(paper_cov * sample_papers)))
                explanation = f"Strong recurrence signal: appeared across {papers_num} of {sample_papers} papers with {hist_occ} questions and {marks_seen:.0f} marks."
            elif "HIGH_MARK_WEIGHT" in reason_codes:
                explanation = f"Carries significant historical weight ({marks_seen:.0f} marks across {hist_occ} question(s))."
            else:
                explanation = f"Appeared in {hist_occ} historical question(s) representing {marks_seen:.0f} marks."

            results.append(PredictionResult(
                target=target,
                name=name,
                rank=rank,
                score=score,
                confidence=conf,
                evidence=evidence,
                prediction_score=score,
                probability=calibrated_prob,
                historical_occurrences=hist_occ,
                recent_occurrences=recent_occ,
                last_seen_year=int(last_seen) if str(last_seen).isdigit() else None,
                marks_seen=marks_seen,
                family_recurrence_score=float(evidence.get("family_score", 0.0)),
                recent_frequency_score=recent_f,
                recency_score=(0.7 * recent_f + 0.3 * hist_f),
                marks_score=marks_w,
                evidence_count=hist_occ,
                reason_codes=reason_codes,
                explanation=explanation,
                score_semantics=SCORE_SEMANTICS,
                calibration_method=CALIBRATION_METHOD,
                evidence_sufficiency=evidence_sufficiency,
                papers_analyzed=sample_papers,
                papers_with_topic=papers_with_topic,
                supporting_questions=evidence.get("supporting_questions", []),
            ))
        return results

class AllTimeFrequencyBaseline(BaseModel):
    def predict_topics(self):
        sample_papers = self.dna.sample_size.papers if (self.dna and hasattr(self.dna, "sample_size")) else 0
        scores = [
            (
                t.topic,
                t.historical_frequency,
                {
                    "freq": t.historical_frequency,
                    "hist_freq": t.historical_frequency,
                    "occurrences": t.question_count,
                    "total_marks": t.total_marks,
                    "paper_coverage": t.paper_coverage,
                    "papers_with_topic": round(t.paper_coverage * sample_papers),
                }
            )
            for t in self.dna.topics
        ]
        return self._rank_and_format(scores, PredictionTarget.TOPIC)
        
    def predict_units(self):
        total_q = self.dna.sample_size.questions
        scores = []
        for u in self.dna.units:
            freq = (u.question_count / total_q) if total_q else 0
            scores.append((u.unit, freq, {"freq": freq}))
        return self._rank_and_format(scores, PredictionTarget.UNIT)

class RecentFrequencyBaseline(BaseModel):
    def predict_topics(self):
        sample_papers = self.dna.sample_size.papers if (self.dna and hasattr(self.dna, "sample_size")) else 0
        scores = [
            (
                t.topic,
                t.recent_frequency,
                {
                    "recent_freq": t.recent_frequency,
                    "occurrences": t.question_count,
                    "total_marks": t.total_marks,
                    "paper_coverage": t.paper_coverage,
                    "papers_with_topic": round(t.paper_coverage * sample_papers),
                }
            )
            for t in self.dna.topics
        ]
        return self._rank_and_format(scores, PredictionTarget.TOPIC)
        
    def predict_units(self):
        scores = [(u.unit, u.recent_weighting, {"recent_weight": u.recent_weighting}) for u in self.dna.units]
        return self._rank_and_format(scores, PredictionTarget.UNIT)

class RecencyWeightedBaseline(BaseModel):
    def predict_topics(self):
        sample_papers = self.dna.sample_size.papers if (self.dna and hasattr(self.dna, "sample_size")) else 0
        scores = []
        for t in self.dna.topics:
            score = (0.7 * t.recent_frequency) + (0.3 * t.historical_frequency)
            scores.append((
                t.topic,
                score,
                {
                    "recent_freq": t.recent_frequency,
                    "hist_freq": t.historical_frequency,
                    "occurrences": t.question_count,
                    "total_marks": t.total_marks,
                    "paper_coverage": t.paper_coverage,
                    "papers_with_topic": round(t.paper_coverage * sample_papers),
                }
            ))
        return self._rank_and_format(scores, PredictionTarget.TOPIC)

class MarksWeightedBaseline(BaseModel):
    def predict_topics(self):
        sample_papers = self.dna.sample_size.papers if (self.dna and hasattr(self.dna, "sample_size")) else 0
        total_marks = sum(t.total_marks for t in self.dna.topics)
        scores = []
        for t in self.dna.topics:
            weight = (t.total_marks / total_marks) if total_marks else 0
            scores.append((
                t.topic,
                weight,
                {
                    "marks_weight": weight,
                    "occurrences": t.question_count,
                    "total_marks": t.total_marks,
                    "paper_coverage": t.paper_coverage,
                    "papers_with_topic": round(t.paper_coverage * sample_papers),
                }
            ))
        return self._rank_and_format(scores, PredictionTarget.TOPIC)
        
    def predict_units(self):
        scores = [(u.unit, u.historical_weighting, {"marks_weight": u.historical_weighting}) for u in self.dna.units]
        return self._rank_and_format(scores, PredictionTarget.UNIT)

class FamilyRecurrenceBaseline(BaseModel):
    def predict_families(self):
        scores = []
        for f in self.dna.families:
            score = f.occurrences * 0.5 + f.recent_recurrence_count * 0.5
            scores.append((f.family_name, score, {"occurrences": f.occurrences, "sample_size": f.occurrences}))
        return self._rank_and_format(scores, PredictionTarget.FAMILY)

class ExamScopeCombinedModel(BaseModel):
    def predict_topics(self):
        sample_papers = self.dna.sample_size.papers if (self.dna and hasattr(self.dna, "sample_size")) else 0
        total_marks = sum(t.total_marks for t in self.dna.topics)
        scores = []
        for t in self.dna.topics:
            marks_w = (t.total_marks / total_marks) if total_marks else 0
            score = (0.4 * t.recent_frequency) + (0.3 * marks_w) + (0.3 * t.historical_frequency)
            scores.append((t.topic, score, {
                "combo": True, 
                "recent_freq": t.recent_frequency,
                "hist_freq": t.historical_frequency,
                "occurrences": t.question_count,
                "total_marks": t.total_marks,
                "paper_coverage": t.paper_coverage,
                "papers_with_topic": round(t.paper_coverage * sample_papers),
                "marks_weight": marks_w,
                "average_marks": t.average_marks,
            }))
        return self._rank_and_format(scores, PredictionTarget.TOPIC)
        
    def predict_units(self):
        scores = []
        for u in self.dna.units:
            score = (0.6 * u.recent_weighting) + (0.4 * u.historical_weighting)
            scores.append((u.unit, score, {
                "combo": True,
                "occurrences": u.question_count
            }))
        return self._rank_and_format(scores, PredictionTarget.UNIT)
        
    def predict_families(self):
        scores = []
        for f in self.dna.families:
            score = (f.occurrences * 0.4) + (f.recent_recurrence_count * 0.6)
            last_seen = str(max(f.years)) if f.years else "Unknown"
            scores.append((f.family_name, score, {
                "occurrences": f.occurrences, 
                "sample_size": f.occurrences, 
                "interval": f.recurrence_interval_years,
                "last_seen": last_seen
            }))
        return self._rank_and_format(scores, PredictionTarget.FAMILY)
