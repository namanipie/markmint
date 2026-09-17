"""Deterministic study-priority and resource services."""

from datetime import datetime, date, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend.models.core import (
    Concept, Course, Document, Exam, MappingConfidence, Question, Section,
    StudentTopicProgress, StudyEvidence, Syllabus, Topic, Unit,
)
from backend.services.prediction.engine import PredictionResult


class StudyPriority(str):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityResult:
    def __init__(
        self,
        topic: str,
        prediction_score: float,
        priority: str,
        reasons: List[str],
        resources: List[Dict[str, Any]],
        confidence: str = "LOW",
        probability: Optional[float] = None,
        student_status: Optional[str] = None,
        practice_accuracy: Optional[float] = None,
        reason_codes: Optional[List[str]] = None,
        topic_id: Optional[int] = None,
        recommended_action: str = "DEEP_STUDY_URGENT",
    ):
        self.topic = topic
        self.prediction_score = prediction_score
        self.priority = priority
        self.reasons = reasons
        self.resources = resources
        self.confidence = confidence
        self.probability = probability if probability is not None else prediction_score
        self.student_status = student_status
        self.practice_accuracy = practice_accuracy
        self.reason_codes = reason_codes or []
        self.topic_id = topic_id
        self.recommended_action = recommended_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "name": self.topic,
            "topic_id": self.topic_id,
            "prediction_score": self.prediction_score,
            "probability": self.probability,
            "confidence": self.confidence,
            "priority": self.priority,
            "recommended_action": self.recommended_action,
            "reasons": self.reasons,
            "reason_codes": self.reason_codes,
            "resources": self.resources,
            "student_status": self.student_status,
            "practice_accuracy": self.practice_accuracy,
        }


class StudyIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    def _course_topic(self, topic_name: str, course_id: int) -> Topic | None:
        if self.db is None:
            return None
        return self.db.query(Topic).join(Unit).join(Syllabus).filter(
            Topic.name == topic_name, Syllabus.course_id == course_id
        ).first()

    def _course_topic_by_id(self, topic_id: int, course_id: int) -> Topic | None:
        if self.db is None:
            return None
        return self.db.query(Topic).join(Unit).join(Syllabus).filter(
            Topic.id == topic_id, Syllabus.course_id == course_id
        ).first()

    def get_topic_resources(self, topic_name: str, course_id: int) -> List[Dict[str, Any]]:
        if self.db is None:
            return []
        topic = self._course_topic(topic_name, course_id)
        if not topic:
            return []
        course = self.db.query(Course).filter(Course.id == course_id).first()
        concept = self.db.query(Concept).filter(
            Concept.canonical_name == topic.name,
            Concept.unit_id == topic.unit_id,
        ).first()
        resources: List[Dict[str, Any]] = []
        if concept and course:
            evidence_rows = (
                self.db.query(StudyEvidence)
                .join(Document, StudyEvidence.document_id == Document.id)
                .filter(
                    StudyEvidence.concept_id == concept.id,
                    StudyEvidence.confidence.in_([MappingConfidence.HIGH, MappingConfidence.MEDIUM]),
                    Document.subject == course.name,
                )
                .all()
            )
            seen = set()
            for evidence in evidence_rows:
                if evidence.document_id in seen:
                    continue
                seen.add(evidence.document_id)
                document = evidence.document
                resources.append({
                    "id": document.id,
                    "title": document.title or "Untitled Document",
                    "source": document.source or "local",
                    "resource_type": document.resource_type or "study_material",
                    "original_url": document.original_url,
                    "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
                    "owner_id": document.owner_id,
                    "page_number": evidence.page_number,
                    "content": evidence.content[:250] if evidence.content else None,
                })

        question_count = (
            self.db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .filter(Exam.course_id == course_id, Topic.id == topic.id)
            .count()
        )
        if question_count:
            resources.append({
                "id": None,
                "title": f"Previous exam questions for {topic.name}",
                "source": "historical_exams",
                "resource_type": "previous_exam_questions",
                "question_count": question_count,
            })
        return resources

    def calculate_study_priority(
        self, prediction: PredictionResult, course_id: int | None = None, student_id: str = "anonymous"
    ) -> PriorityResult:
        score = float(prediction.score)
        evidence = prediction.evidence or {}
        confidence = getattr(prediction, "confidence", "LOW")

        if score >= 0.8:
            priority = StudyPriority.VERY_HIGH
            reasons = [
                "Exceptionally high predicted probability.",
                "Very high predicted exam probability.",
            ]
        elif score >= 0.6:
            priority = StudyPriority.HIGH
            reasons = ["High predicted exam probability."]
        elif score >= 0.4:
            priority = StudyPriority.MEDIUM
            reasons = ["Moderate predicted exam probability."]
        else:
            priority = StudyPriority.LOW
            reasons = ["Lower predicted exam probability."]

        if evidence.get("occurrences", 0) >= 2 or evidence.get("freq", 0) > 0.3:
            reasons.append("Appears repeatedly in historical papers.")
        if evidence.get("recent_freq", 0) > 0.2:
            reasons.append("Appeared recently in historical papers.")
        if evidence.get("marks_weight", 0) > 0.15:
            reasons.append("Carries significant historical marks weight.")

        resources = self.get_topic_resources(prediction.name, course_id) if course_id is not None else []
        reasons.append(
            "Study material or related past questions are available."
            if resources else "No trusted topic-mapped study material is available."
        )

        topic = self._course_topic(prediction.name, course_id) if course_id is not None else None
        progress = (
            self.db.query(StudentTopicProgress).filter_by(
                student_id=student_id, topic_id=topic.id
            ).first() if (topic and self.db is not None) else None
        )
        
        student_status = progress.status if progress else "NOT_STARTED"
        practice_accuracy = None
        if progress and progress.practice_attempted:
            practice_accuracy = round((progress.practice_correct or 0) / progress.practice_attempted, 2)

        # Personalization: Adjust priority based on mastery / progress
        if progress and progress.status == "COMPLETED" and (practice_accuracy is None or practice_accuracy >= 0.8):
            reasons.append("Topic completed with high mastery (>= 80%); deprioritized for active study.")
            if priority == StudyPriority.VERY_HIGH:
                priority = StudyPriority.HIGH
            elif priority == StudyPriority.HIGH:
                priority = StudyPriority.MEDIUM
            elif priority == StudyPriority.MEDIUM:
                priority = StudyPriority.LOW
            recommended_action = "MAINTAIN_AND_REVIEW"
        else:
            weak = course_id is not None and self.db is not None and not progress
            if progress and progress.practice_attempted:
                weak = (progress.practice_correct or 0) / progress.practice_attempted < 0.6
                if weak:
                    reasons.append("Recorded practice accuracy is below 60%.")
            elif weak:
                reasons.append("No student progress evidence is recorded.")
            if weak and priority == StudyPriority.HIGH:
                priority = StudyPriority.VERY_HIGH
            elif weak and priority == StudyPriority.MEDIUM:
                priority = StudyPriority.HIGH

            if priority == StudyPriority.VERY_HIGH:
                recommended_action = "DEEP_STUDY_URGENT"
            elif priority == StudyPriority.HIGH:
                recommended_action = "PRACTICE_QUESTIONS"
            elif priority == StudyPriority.MEDIUM:
                recommended_action = "CONCEPT_REINFORCEMENT"
            else:
                recommended_action = "FOUNDATIONAL_EXPLORATION"

        reason_codes = list(getattr(prediction, "reason_codes", []))
        if progress and progress.status == "COMPLETED":
            reason_codes.append("STUDENT_MASTERED")
        elif not progress:
            reason_codes.append("STUDENT_UNSTUDIED")

        return PriorityResult(
            topic=prediction.name,
            prediction_score=round(score, 4),
            priority=priority,
            reasons=reasons,
            resources=resources,
            confidence=confidence,
            probability=round(getattr(prediction, "probability", score), 4),
            student_status=student_status,
            practice_accuracy=practice_accuracy,
            reason_codes=reason_codes,
            topic_id=topic.id if topic else None,
            recommended_action=recommended_action,
        )

    def generate_study_plan(
        self,
        predictions: List[PredictionResult],
        course_id: int,
        student_id: str = "anonymous",
        target_exam_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        priorities = [
            self.calculate_study_priority(prediction, course_id, student_id)
            for prediction in predictions if getattr(prediction, "target", "topic") == "topic"
        ]
        order = {StudyPriority.VERY_HIGH: 0, StudyPriority.HIGH: 1,
                 StudyPriority.MEDIUM: 2, StudyPriority.LOW: 3}
        priorities.sort(key=lambda item: (order[item.priority], -item.prediction_score, item.topic))
        return [{"order": index, **priority.to_dict()} for index, priority in enumerate(priorities, 1)]

    def calculate_coverage_gap(
        self,
        predictions: List[PredictionResult],
        course_id: int,
        student_id: str = "anonymous"
    ) -> Dict[str, Any]:
        priorities = [
            self.calculate_study_priority(p, course_id, student_id)
            for p in predictions if getattr(p, "target", "topic") == "topic"
        ]
        total_predicted = len(priorities)
        if total_predicted == 0:
            return {
                "total_predicted_topics": 0,
                "mastered_topics": 0,
                "in_progress_topics": 0,
                "unstudied_topics": 0,
                "student_preparation_coverage": 0.0,
                "coverage_gap_topics": [],
                "high_priority_gap_count": 0,
                "mastered_topic_count": 0,
                "in_progress_count": 0,
                "unstudied_count": 0,
            }

        mastered = 0
        in_progress = 0
        unstudied = 0
        gap_topics = []

        for item in priorities:
            status = item.student_status or "NOT_STARTED"
            acc = item.practice_accuracy
            is_mastered = (status == "COMPLETED" and (acc is None or acc >= 0.6))
            if is_mastered:
                mastered += 1
            elif status in {"STARTED", "IN_PROGRESS"}:
                in_progress += 1
                if item.priority in {StudyPriority.VERY_HIGH, StudyPriority.HIGH}:
                    gap_topics.append(item.topic)
            else:
                unstudied += 1
                if item.priority in {StudyPriority.VERY_HIGH, StudyPriority.HIGH}:
                    gap_topics.append(item.topic)

        coverage_pct = round(((mastered + 0.5 * in_progress) / total_predicted) * 100.0, 1)

        return {
            "total_predicted_topics": total_predicted,
            "mastered_topics": mastered,
            "in_progress_topics": in_progress,
            "unstudied_topics": unstudied,
            "student_preparation_coverage": coverage_pct,
            "coverage_gap_topics": gap_topics,
            "high_priority_gap_count": len(gap_topics),
            "mastered_topic_count": mastered,
            "in_progress_count": in_progress,
            "unstudied_count": unstudied,
        }

    def generate_exam_schedule(
        self,
        priorities: List[PriorityResult],
        target_exam_date_str: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        if not target_exam_date_str:
            return None

        try:
            target_date = datetime.strptime(target_exam_date_str.strip(), "%Y-%m-%d").date()
            today = date.today()
            days_remaining = (target_date - today).days
            if days_remaining <= 0:
                return {
                    "target_exam_date": target_exam_date_str,
                    "days_remaining": 0,
                    "status": "EXAM_DUE_OR_PASSED",
                    "phases": []
                }

            # Build focus topic dicts with topic_id and topic_name
            vh_topics = [{"topic_id": p.topic_id, "topic_name": p.topic} for p in priorities if p.priority == StudyPriority.VERY_HIGH]
            h_topics = [{"topic_id": p.topic_id, "topic_name": p.topic} for p in priorities if p.priority == StudyPriority.HIGH]
            m_topics = [{"topic_id": p.topic_id, "topic_name": p.topic} for p in priorities if p.priority in {StudyPriority.MEDIUM, StudyPriority.LOW}]

            # Strict time conservation: ensure sum(phase.duration_days) == days_remaining
            if days_remaining == 1:
                phases = [
                    {
                        "phase": 1,
                        "name": "Final High-Yield Review",
                        "duration_days": 1,
                        "focus_topics": (vh_topics + h_topics)[:5] or [{"topic_id": None, "topic_name": "Core Formulas"}],
                        "description": "Emergency high-yield formula and core concept reinforcement."
                    }
                ]
            elif days_remaining == 2:
                phases = [
                    {
                        "phase": 1,
                        "name": "Core High-Yield Focus",
                        "duration_days": 1,
                        "focus_topics": vh_topics[:5] or h_topics[:5],
                        "description": "Essential theorems and high-weight recurrences."
                    },
                    {
                        "phase": 2,
                        "name": "Targeted Question Practice",
                        "duration_days": 1,
                        "focus_topics": h_topics[:5] or m_topics[:5],
                        "description": "Practice high-frequency questions and formulas."
                    }
                ]
            else:
                phase1_days = max(1, int(round(days_remaining * 0.5)))
                phase2_days = max(1, int(round(days_remaining * 0.3)))
                phase3_days = days_remaining - phase1_days - phase2_days
                if phase3_days < 1:
                    phase3_days = 1
                    if phase1_days > phase2_days:
                        phase1_days = max(1, phase1_days - 1)
                    else:
                        phase2_days = max(1, phase2_days - 1)

                phases = [
                    {
                        "phase": 1,
                        "name": "High-Yield Foundation",
                        "duration_days": phase1_days,
                        "focus_topics": vh_topics,
                        "description": "Core concepts & highest predicted recurrence topics."
                    },
                    {
                        "phase": 2,
                        "name": "Targeted Question Practice",
                        "duration_days": phase2_days,
                        "focus_topics": h_topics,
                        "description": "Solve historical questions and recurring families."
                    },
                    {
                        "phase": 3,
                        "name": "Final Timed Drill & Revision",
                        "duration_days": phase3_days,
                        "focus_topics": m_topics,
                        "description": "Comprehensive review and formula reinforcement."
                    }
                ]

            return {
                "target_exam_date": target_exam_date_str,
                "days_remaining": days_remaining,
                "status": "ON_TRACK",
                "recommended_daily_topics": round(len(priorities) / max(1, days_remaining), 1),
                "phases": phases
            }
        except (ValueError, TypeError):
            return None

    def record_progress(
        self, user_id: str = None, course_id: int = None, topic_id: int = None, status: str = None,
        viewed_resource: bool = False, practice_attempted: bool = False,
        practice_accuracy: float = None, student_id: str = None,
    ) -> StudentTopicProgress:
        effective_user_id = student_id or user_id or "anonymous"
        if not self._course_topic_by_id(topic_id, course_id):
            raise ValueError("Topic does not belong to the selected course")
        progress = self.db.query(StudentTopicProgress).filter_by(
            student_id=effective_user_id, topic_id=topic_id
        ).first()
        if not progress:
            progress = StudentTopicProgress(student_id=effective_user_id, topic_id=topic_id)
            self.db.add(progress)
        if status:
            if status not in {"NOT_STARTED", "STARTED", "COMPLETED"}:
                raise ValueError("status must be NOT_STARTED, STARTED, or COMPLETED")
            progress.status = status
        if practice_attempted:
            progress.practice_attempted = (progress.practice_attempted or 0) + 1
            if practice_accuracy is not None and practice_accuracy >= 0.5:
                progress.practice_correct = (progress.practice_correct or 0) + 1
        progress.last_studied_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(progress)
        return progress
