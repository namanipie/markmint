"""
Focused integration tests for Course 8: Foreign Languages (SEM1-FORE).
Verifies:
- Explicit language track requirement (TRACK_SELECTION_REQUIRED when omitted)
- Isolated language track snapshot, prediction, and study intelligence
- Practice question generation per track
"""
import pytest
from fastapi import HTTPException
from backend.core.database import SessionLocal
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_foreign_languages_track_selection_enforced():
    """Verify Course 8 strictly enforces language track selection."""
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc_info:
            get_intelligence_snapshot(course_id="8", db=db)
        assert exc_info.value.status_code == 400
        assert "TRACK_SELECTION_REQUIRED" in exc_info.value.detail
    finally:
        db.close()


def test_foreign_languages_track_segmented_mode():
    """Verify Course 8 operates truthfully when a specific language track is provided."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="8", language="german", db=db)
        assert snapshot["data_availability_status"] == "READY"
        assert snapshot["track"]["track_key"] == "german"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] > 0
        assert len(snapshot["predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] > 0
    finally:
        db.close()


def test_foreign_languages_study_plan_and_practice():
    """Verify study plan and practice operate correctly for a specified track."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Foreign Languages", language="german", db=db)
        assert priorities["plan_mode"] in ("topic", "family")
        assert len(priorities["priorities"]) > 0

        practice = get_practice_questions("Foreign Languages", language="german", limit=10)
        assert len(practice["questions"]) > 0
        assert practice["subject"] == "Foreign Languages"
    finally:
        db.close()
