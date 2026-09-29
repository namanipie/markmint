from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass(frozen=True)
class HistoricalContext:
    course_id: int
    cutoff_year: int
    assessment_cycle: Optional[str] = None
    track_id: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.cutoff_year, int) or self.cutoff_year <= 0:
            raise ValueError(f"HistoricalContext requires a positive integer cutoff_year, got {self.cutoff_year!r}")
        if not isinstance(self.course_id, int) or self.course_id <= 0:
            raise ValueError(f"HistoricalContext requires a positive integer course_id, got {self.course_id!r}")
    
class PredictionTarget:
    TOPIC = "topic"
    UNIT = "unit"
    FAMILY = "family"
    CONCEPT = "concept"


def resolve_target_year(
    db: Optional[Any],
    course_id: int,
    target_year: Optional[int] = None,
    track_id: Optional[int] = None,
    default_year: int = 2024,
) -> int:
    """Resolve the target exam year for prediction/intelligence.

    Contract:
    1. If target_year is explicitly provided as a positive integer, return it.
    2. Otherwise, dynamically derive: max(Exam.year) + 1 for the course/track.
    3. If no historical exams with known years exist, fall back to default_year (2024).
    """
    if target_year is not None and not hasattr(target_year, "default"):
        try:
            val = int(target_year)
            if val > 0:
                return val
        except (ValueError, TypeError):
            pass

    if db is None:
        return default_year

    from backend.models.core import Exam
    from sqlalchemy import func

    max_year_q = db.query(func.max(Exam.year)).filter(
        Exam.course_id == course_id,
        Exam.year.isnot(None),
        Exam.year > 0,
    )
    if track_id is not None:
        max_year_q = max_year_q.filter(Exam.track_id == track_id)

    max_year = max_year_q.scalar()
    if max_year is not None and max_year > 0:
        return max_year + 1
    return default_year

