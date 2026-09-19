from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, and_
from typing import List
from backend.models.core import Exam, Section, Question, QuestionFamily, QuestionFamilyMembership, Topic
from backend.services.prediction.context import HistoricalContext
from backend.services.assessment_cycle import filter_exams_by_cycle

class HistoricalRepository:
    """
    Enforces absolute temporal isolation and assessment cycle scoping. Every method
    in this repository MUST apply `Exam.year < cutoff_year` and `Exam.year IS NOT NULL`.
    """
    def __init__(self, db: Session, context: HistoricalContext):
        self.db = db
        self.context = context

    def get_historical_exams(self) -> List[Exam]:
        """Returns only exams strictly before the cutoff year with eager loading to prevent N+1 queries."""
        q = self.db.query(Exam).options(
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
        ).filter(
            Exam.course_id == self.context.course_id,
            Exam.year != None,
            Exam.year < self.context.cutoff_year
        )
        q = filter_exams_by_cycle(q, Exam.assessment_type, self.context.assessment_cycle, course_id=self.context.course_id)
        return q.order_by(Exam.year.asc()).all()

    def get_historical_questions(self) -> List[Question]:
        """Returns only questions belonging to historical exams."""
        q = self.db.query(Question).join(Section).join(Exam).filter(
            Exam.course_id == self.context.course_id,
            Exam.year != None,
            Exam.year < self.context.cutoff_year
        )
        q = filter_exams_by_cycle(q, Exam.assessment_type, self.context.assessment_cycle, course_id=self.context.course_id)
        return q.all()

    def get_historical_family_memberships(self) -> List[QuestionFamilyMembership]:
        """Returns only memberships corresponding to historical questions."""
        q = self.db.query(QuestionFamilyMembership).join(Question).join(Section).join(Exam).filter(
            Exam.course_id == self.context.course_id,
            Exam.year != None,
            Exam.year < self.context.cutoff_year
        )
        q = filter_exams_by_cycle(q, Exam.assessment_type, self.context.assessment_cycle, course_id=self.context.course_id)
        return q.all()

    def get_target_exams(self) -> List[Exam]:
        """Returns ONLY the target year exams. Never use this for historical feature generation!"""
        q = self.db.query(Exam).options(
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
        ).filter(
            Exam.course_id == self.context.course_id,
            Exam.year == self.context.cutoff_year
        )
        q = filter_exams_by_cycle(q, Exam.assessment_type, self.context.assessment_cycle, course_id=self.context.course_id)
        return q.all()
