"""Deterministic two-tier caching service for academic intelligence snapshots."""

import logging
import threading
import time
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


class BoundedAnalysisCache:
    """Thread-safe bounded LRU cache with TTL for analysis reports."""

    def __init__(self, max_size: int = 256, ttl: float = 300.0):
        self._max_size = max_size
        self._ttl = ttl
        self._cache: OrderedDict[Any, Any] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            ts, data = self._cache[key]
            if time.time() - ts >= self._ttl:
                self._cache.pop(key, None)
                return None
            self._cache.move_to_end(key)
            return data

    def set(self, key: Any, data: Any) -> None:
        with self._lock:
            self._cache[key] = (time.time(), data)
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def invalidate_course(self, course_id: int) -> int:
        with self._lock:
            keys_to_delete = [
                k for k in self._cache
                if (isinstance(k, tuple) and len(k) > 0 and (k[0] == course_id or str(k[0]).strip() == str(course_id)))
            ]
            for k in keys_to_delete:
                self._cache.pop(k, None)
            return len(keys_to_delete)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            ts, _ = self._cache[key]
            if time.time() - ts >= self._ttl:
                self._cache.pop(key, None)
                return False
            return True

    def __getitem__(self, key: Any) -> Any:
        with self._lock:
            return self._cache[key]

    def __setitem__(self, key: Any, val: Any) -> None:
        with self._lock:
            # val can be (timestamp, data) or raw data
            if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], (int, float)):
                self._cache[key] = val
            else:
                self._cache[key] = (time.time(), val)
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


analysis_cache = BoundedAnalysisCache(max_size=256, ttl=300.0)


def canonicalize_identifier(identifier: Union[str, int]) -> str:
    """Canonicalize course identifier: digits string converted to integer string, others lowercased and stripped."""
    s = str(identifier).strip()
    if s.isdigit():
        return str(int(s))
    return s.lower()


def canonicalize_cycle(assessment_cycle: Optional[str]) -> str:
    """Canonicalize assessment cycle, mapping None/empty/unknown to 'ALL'."""
    if not assessment_cycle or not isinstance(assessment_cycle, str):
        return "ALL"
    from backend.services.assessment_cycle import normalize_assessment_cycle
    norm = normalize_assessment_cycle(assessment_cycle)
    return norm if norm else "ALL"


def canonicalize_track(track: Optional[Union[str, int]]) -> str:
    """Canonicalize track identifier or track key."""
    if track is None:
        return "none"
    s = str(track).strip().lower()
    if s in ("", "none", "null"):
        return "none"
    return s


def canonicalize_student_id(student_id: Optional[str]) -> str:
    """Canonicalize student identifier, treating None/empty/anonymous/case-insensitive as empty string (anonymous)."""
    if not student_id or not isinstance(student_id, str):
        return ""
    clean = student_id.strip()
    if clean.lower() in ("", "anonymous", "none", "null"):
        return ""
    return clean


def build_cache_key(
    identifier: Union[str, int],
    assessment_cycle: Optional[str] = None,
    track: Optional[Union[str, int]] = None,
    student_id: Optional[str] = None,
    cutoff_year: Optional[int] = None,
) -> str:
    """Deterministic, canonical cache key incorporating course identifier, cycle, track, student_id, cutoff, and versions."""
    clean_id = canonicalize_identifier(identifier)
    norm_cycle = canonicalize_cycle(assessment_cycle)
    track_part = canonicalize_track(track)
    clean_student = canonicalize_student_id(student_id)
    student_part = f":student:{clean_student}" if clean_student else ""
    cutoff_part = f":cutoff:{cutoff_year}" if cutoff_year is not None else ""
    return f"{clean_id}:{norm_cycle}:{track_part}{student_part}{cutoff_part}:{CORPUS_VERSION}:{TAXONOMY_VERSION}:{MODEL_VERSION}"


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
    def invalidate_course(db: Optional[Session], course_id: int) -> int:
        """Invalidate all cached snapshots and analysis reports for a specific course across Tier 1, Tier 2, and analysis cache."""
        prefix = f"{course_id}:"
        with _lock:
            keys_to_delete = [
                k for k, v in _memory_cache.items()
                if k.startswith(prefix) or (isinstance(v, dict) and v.get("course", {}).get("id") == course_id)
            ]
            for k in keys_to_delete:
                _memory_cache.pop(k, None)

        # Invalidate in-memory analysis cache (DNA / Evolution)
        analysis_cache.invalidate_course(course_id)

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
        """Clear all entries from Tier 1 memory cache and analysis cache (useful for tests)."""
        with _lock:
            _memory_cache.clear()
        analysis_cache.clear()
