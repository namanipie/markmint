"""Deterministic two-tier caching service for academic intelligence snapshots."""

import logging
import threading
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from backend.core.version import CORPUS_VERSION, MODEL_VERSION, TAXONOMY_VERSION
from backend.models.core import IntelligenceSnapshot

logger = logging.getLogger("markmint.intelligence.cache")

MAX_MEMORY_CACHE_ENTRIES = 256
_memory_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
_lock = threading.Lock()


def build_cache_key(
    identifier: Union[str, int],
    assessment_cycle: Optional[str],
    track: Optional[Union[str, int]] = None,
    student_id: Optional[str] = None,
) -> str:
    """Deterministic cache key incorporating identifier/course_id, cycle, track, student_id, and version invariants."""
    norm_cycle = (assessment_cycle or "ALL").upper().strip()
    track_part = str(track).lower().strip() if track is not None else "none"
    clean_student = student_id.strip() if student_id and isinstance(student_id, str) else ""
    student_part = f":student:{clean_student}" if clean_student and clean_student != "anonymous" else ""
    return f"{str(identifier).lower().strip()}:{norm_cycle}:{track_part}{student_part}:{CORPUS_VERSION}:{TAXONOMY_VERSION}:{MODEL_VERSION}"


def _validate_snapshot_payload(payload: Any) -> bool:
    """Validate that cached snapshot payload has required structural elements."""
    if not isinstance(payload, dict):
        return False
    required_keys = ("data_availability_status", "course", "metadata")
    if not all(k in payload for k in required_keys):
        return False
    if not isinstance(payload.get("course"), dict):
        return False
    if not isinstance(payload.get("metadata"), dict):
        return False
    return True


class IntelligenceCacheService:
    @staticmethod
    def get_snapshot(
        db: Session,
        identifier: Union[str, int],
        assessment_cycle: Optional[str] = None,
        track: Optional[Union[str, int]] = None,
        student_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve snapshot from Tier 1 (LRU memory) or Tier 2 (Postgres/SQLite DB)."""
        key = build_cache_key(identifier, assessment_cycle, track, student_id=student_id)

        # Tier 1: In-process LRU cache (0 SQL queries)
        with _lock:
            if key in _memory_cache:
                payload = _memory_cache[key]
                if _validate_snapshot_payload(payload):
                    _memory_cache.move_to_end(key)
                    logger.debug("Tier 1 memory cache HIT for key %s", key)
                    return payload
                else:
                    logger.warning("Corrupted snapshot in Tier 1 memory cache for key %s; evicting", key)
                    _memory_cache.pop(key, None)

        # Tier 2: Persistent database table (1 query if identifier is course_id)
        if db is not None:
            try:
                # Query DB table by cache key
                row = (
                    db.query(IntelligenceSnapshot)
                    .filter(IntelligenceSnapshot.cache_key == key)
                    .first()
                )
                if row:
                    if _validate_snapshot_payload(row.payload):
                        with _lock:
                            _memory_cache[key] = row.payload
                            if len(_memory_cache) > MAX_MEMORY_CACHE_ENTRIES:
                                _memory_cache.popitem(last=False)
                        logger.debug("Tier 2 persistent cache HIT for key %s", key)
                        return row.payload
                    else:
                        logger.warning("Corrupted snapshot payload in DB for key %s; removing row", key)
                        db.delete(row)
                        db.commit()
            except Exception as e:
                logger.warning("Tier 2 persistent cache lookup failed: %s", e)

        return None

    @staticmethod
    def store_snapshot(
        db: Session,
        course_id: int,
        assessment_cycle: Optional[str],
        track_id: Optional[int],
        payload: Dict[str, Any],
        identifier: Optional[Union[str, int]] = None,
        track_key: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> None:
        """Store synthesized snapshot in Tier 1 (LRU memory) and Tier 2 (database table)."""
        norm_cycle = (assessment_cycle or "ALL").upper().strip()

        # Canonical DB key uses course_id and track_id (or track_key)
        # E.g. for language tracks, if track_key is 'german', use track_key so lookup by language matches
        track_param = track_key or track_id
        canonical_key = build_cache_key(course_id, norm_cycle, track_param, student_id=student_id)

        # Store in Tier 1 memory cache under canonical key
        with _lock:
            _memory_cache[canonical_key] = payload
            _memory_cache.move_to_end(canonical_key)

            # Also alias by track_id if track_key was used
            if track_id is not None and track_key is not None:
                id_key = build_cache_key(course_id, norm_cycle, track_id, student_id=student_id)
                _memory_cache[id_key] = payload

            # Also alias by original identifier string if different
            if identifier is not None and str(identifier).lower().strip() != str(course_id):
                alias_key = build_cache_key(identifier, norm_cycle, track_param, student_id=student_id)
                _memory_cache[alias_key] = payload

            while len(_memory_cache) > MAX_MEMORY_CACHE_ENTRIES:
                _memory_cache.popitem(last=False)

        # Store in Tier 2 persistent database table
        if db is not None:
            try:
                existing = (
                    db.query(IntelligenceSnapshot)
                    .filter(IntelligenceSnapshot.cache_key == canonical_key)
                    .first()
                )
                if existing:
                    existing.payload = payload
                    existing.updated_at = datetime.utcnow()
                else:
                    new_snapshot = IntelligenceSnapshot(
                        course_id=course_id,
                        track_id=track_id,
                        cache_key=canonical_key,
                        assessment_cycle=norm_cycle,
                        model_version=MODEL_VERSION,
                        taxonomy_version=TAXONOMY_VERSION,
                        corpus_version=CORPUS_VERSION,
                        payload=payload,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(new_snapshot)
                db.commit()
                logger.info("Persisted intelligence snapshot to DB for key %s", canonical_key)
            except Exception as e:
                db.rollback()
                logger.warning("Failed to persist snapshot to DB: %s", e)

    @staticmethod
    def alias_memory_cache(
        identifier: Union[str, int],
        assessment_cycle: Optional[str],
        track: Optional[Union[str, int]],
        payload: Dict[str, Any],
        student_id: Optional[str] = None,
    ) -> None:
        """Alias an existing valid payload in Tier 1 memory cache under an alternative key."""
        if not _validate_snapshot_payload(payload):
            return
        alias_key = build_cache_key(identifier, assessment_cycle, track, student_id=student_id)
        with _lock:
            _memory_cache[alias_key] = payload
            _memory_cache.move_to_end(alias_key)
            while len(_memory_cache) > MAX_MEMORY_CACHE_ENTRIES:
                _memory_cache.popitem(last=False)

    @staticmethod
    def invalidate_course(db: Session, course_id: int) -> int:
        """Invalidate all cached snapshots for a specific course across Tier 1 and Tier 2."""
        prefix = f"{course_id}:"
        with _lock:
            keys_to_delete = [
                k for k, v in _memory_cache.items()
                if k.startswith(prefix) or (isinstance(v, dict) and v.get("course", {}).get("id") == course_id)
            ]
            for k in keys_to_delete:
                _memory_cache.pop(k, None)

        db_deleted = 0
        if db is not None:
            try:
                db_deleted = (
                    db.query(IntelligenceSnapshot)
                    .filter(IntelligenceSnapshot.course_id == course_id)
                    .delete(synchronize_session=False)
                )
                db.commit()
                logger.info("Invalidated %d DB snapshot rows for course_id=%d", db_deleted, course_id)
            except Exception as e:
                db.rollback()
                logger.warning("Failed to delete snapshots from DB for course_id=%d: %s", course_id, e)

        return db_deleted

    @staticmethod
    def clear_memory_cache() -> None:
        """Clear all entries from Tier 1 memory cache (useful for tests)."""
        with _lock:
            _memory_cache.clear()
