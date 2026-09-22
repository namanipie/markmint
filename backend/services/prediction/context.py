from dataclasses import dataclass
from typing import List, Optional

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
