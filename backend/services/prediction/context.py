from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class HistoricalContext:
    course_id: int
    cutoff_year: int
    assessment_cycle: Optional[str] = None
    track_id: Optional[int] = None
    
class PredictionTarget:
    TOPIC = "topic"
    UNIT = "unit"
    FAMILY = "family"
    CONCEPT = "concept"
