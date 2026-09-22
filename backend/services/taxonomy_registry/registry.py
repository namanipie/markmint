"""
Unified declarative taxonomy registry engine for MarkMint.
Loads, validates, and manages authoritative course syllabus taxonomies
and classification rules with strict consistency and zero cross-course leakage.
"""

import json
import os
from typing import Dict, List, Optional, Any, Set
from threading import Lock

from backend.core.version import TAXONOMY_VERSION
from backend.services.taxonomy_classifier import TaxonomyTopicRule
from backend.services.taxonomy_registry.models import (
    CourseTaxonomyRegistryEntry,
    UnitDefinition,
    TopicDefinition,
)

DEFAULT_DEFINITIONS_DIR = os.path.join(os.path.dirname(__file__), "definitions")


class TaxonomyRegistry:
    """Central declarative registry for course syllabus taxonomies and classification rules."""

    def __init__(self, definitions_dir: Optional[str] = None):
        self.definitions_dir = definitions_dir or DEFAULT_DEFINITIONS_DIR
        self._courses: Dict[int, CourseTaxonomyRegistryEntry] = {}
        self._all_topic_ids: Dict[int, int] = {}  # topic_id -> course_id
        self._topic_rules_cache: Dict[int, List[TaxonomyTopicRule]] = {}
        self.taxonomy_version: str = TAXONOMY_VERSION
        self._load_definitions()

    def _load_definitions(self) -> None:
        """Deterministically discover, parse, and validate all declarative taxonomy definition files."""
        if not os.path.exists(self.definitions_dir):
            return

        json_files = sorted([
            f for f in os.listdir(self.definitions_dir)
            if f.endswith(".json")
        ])

        for fname in json_files:
            fpath = os.path.join(self.definitions_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as exc:
                    raise ValueError(f"Malformed JSON in taxonomy definition '{fname}': {exc}") from exc

            entry = CourseTaxonomyRegistryEntry.from_dict(data)
            self._register_entry(entry, source_file=fname)

    def _register_entry(self, entry: CourseTaxonomyRegistryEntry, source_file: str = "") -> None:
        """Register a single course taxonomy entry with strict invariant validation."""
        cid = entry.course.id

        if cid in self._courses:
            existing_source = self._courses[cid].course.name
            raise ValueError(
                f"Duplicate course ID {cid} in taxonomy registry: '{entry.course.name}' in {source_file} "
                f"conflicts with existing '{existing_source}'"
            )

        # Enforce declarative unit cardinality
        declared_expected = entry.expected_units or entry.course.expected_units
        if declared_expected is not None:
            expected_count = int(declared_expected)
            from backend.services.curriculum_units import validate_unit_cardinality
            if not entry.tracks:
                validate_unit_cardinality(
                    expected_count,
                    [u.number for u in entry.units],
                    context_label=f"Course {cid} ({entry.course.name})"
                )
            else:
                for track_info in (entry.tracks or []):
                    t_id = track_info.get("id")
                    t_units = [u.number for u in entry.units if u.track_id == t_id]
                    validate_unit_cardinality(
                        expected_count,
                        t_units,
                        context_label=f"Course {cid} ({entry.course.name}) Track {track_info.get('track_name', t_id)}"
                    )

        seen_unit_ids: Set[int] = set()
        seen_unit_keys: Set[Any] = set()
        seen_topic_names: Set[Any] = set()

        topic_rules: List[TaxonomyTopicRule] = []

        for unit in entry.units:
            if unit.id in seen_unit_ids:
                raise ValueError(
                    f"Course {cid} ({entry.course.name}): duplicate unit ID {unit.id} ('{unit.name}') in {source_file}"
                )
            seen_unit_ids.add(unit.id)

            unit_key = (unit.track_id, unit.number) if unit.track_id is not None else unit.number
            if unit_key in seen_unit_keys:
                raise ValueError(
                    f"Course {cid} ({entry.course.name}): duplicate unit number {unit.number} in {source_file}"
                )
            seen_unit_keys.add(unit_key)

            for topic in unit.topics:
                # Global topic ID uniqueness check
                if topic.id in self._all_topic_ids:
                    owner_cid = self._all_topic_ids[topic.id]
                    raise ValueError(
                        f"Globally duplicate topic ID {topic.id} ('{topic.name}') in Course {cid}: "
                        f"already claimed by Course {owner_cid}"
                    )
                self._all_topic_ids[topic.id] = cid

                # Course/Track-local topic name uniqueness check
                normalized_name = topic.name.strip().lower()
                topic_key = (unit.track_id, normalized_name) if unit.track_id is not None else normalized_name
                if topic_key in seen_topic_names:
                    raise ValueError(
                        f"Course {cid} ({entry.course.name}): duplicate topic name '{topic.name}' in {source_file}"
                    )
                seen_topic_names.add(topic_key)

                # Convert to runtime TaxonomyTopicRule
                rule = TaxonomyTopicRule(
                    topic_id=topic.id,
                    topic_name=topic.name,
                    unit_id=unit.id,
                    unit_name=unit.name,
                    strong_phrases=list(topic.strong_phrases),
                    specific_keywords=list(topic.specific_keywords),
                    negative_guards=list(topic.negative_guards),
                    context_hints=list(topic.context_hints),
                )
                topic_rules.append(rule)

        self._courses[cid] = entry
        self._topic_rules_cache[cid] = topic_rules

    def get_course_expected_units(self, course_id: int, track_id: Optional[int] = None) -> int:
        """Retrieve declared expected units for a course (or default 5)."""
        if course_id in self._courses:
            entry = self._courses[course_id]
            if entry.expected_units is not None:
                return entry.expected_units
            if entry.course.expected_units is not None:
                return entry.course.expected_units
            if entry.tracks and track_id is not None:
                t_units = [u for u in entry.units if u.track_id == track_id]
                if t_units:
                    return len(t_units)
            elif not entry.tracks and entry.units:
                return len(entry.units)
        return 5

    def get_course(self, course_id: int, track_key: Optional[str] = None) -> CourseTaxonomyRegistryEntry:
        """Retrieve a course's declarative taxonomy entry by course ID, optionally filtered by track."""
        if course_id not in self._courses:
            raise KeyError(f"Course ID {course_id} is not registered in the taxonomy registry.")
        entry = self._courses[course_id]
        if not track_key:
            return entry

        filtered_units = [u for u in entry.units if u.track_key == track_key]
        return CourseTaxonomyRegistryEntry(
            schema_version=entry.schema_version,
            taxonomy_version=entry.taxonomy_version,
            course=entry.course,
            provenance=entry.provenance,
            units=filtered_units,
            tracks=entry.tracks
        )

    def has_course(self, course_id: int) -> bool:
        """Check if a course is registered in the taxonomy registry."""
        return course_id in self._courses

    def list_courses(self) -> List[int]:
        """List all registered course IDs in deterministic sorted order."""
        return sorted(list(self._courses.keys()))

    def get_topic_rules(
        self,
        course_id: int,
        track_id: Optional[int] = None,
        track_key: Optional[str] = None
    ) -> List[TaxonomyTopicRule]:
        """Retrieve the executable TaxonomyTopicRule objects for a course, optionally filtered by track."""
        if course_id not in self._topic_rules_cache:
            raise KeyError(f"No taxonomy rules registered for Course ID {course_id}.")
        
        all_rules = list(self._topic_rules_cache[course_id])
        if track_id is None and track_key is None:
            return all_rules

        entry = self._courses[course_id]
        matching_unit_ids = {
            u.id for u in entry.units
            if (track_id is not None and u.track_id == track_id) or
               (track_key is not None and u.track_key == track_key)
        }
        return [r for r in all_rules if r.unit_id in matching_unit_ids]

    def validate_against_database(self, course_id: int, db: Any) -> Dict[str, Any]:
        """
        Validate that the declarative registry matches the runtime database taxonomy:
        - Course exists
        - All units exist with matching numbers and names
        - All topics exist with matching IDs and names
        """
        from backend.models.core import Course, Unit, Topic

        entry = self.get_course(course_id)
        course_orm = db.query(Course).filter(Course.id == course_id).first()
        if not course_orm:
            return {"valid": False, "error": f"Course ID {course_id} not found in database"}

        mismatches: List[str] = []

        for reg_unit in entry.units:
            db_u = db.query(Unit).filter(Unit.id == reg_unit.id).first()
            if not db_u:
                mismatches.append(f"Unit ID {reg_unit.id} ('{reg_unit.name}') missing in database")
                continue
            if db_u.syllabus and db_u.syllabus.course_id != course_id:
                mismatches.append(f"Unit ID {reg_unit.id} belongs to Course {db_u.syllabus.course_id}, not {course_id}")
            if db_u.name.strip().lower() != reg_unit.name.strip().lower():
                mismatches.append(f"Unit ID {reg_unit.id} name mismatch: DB '{db_u.name}' != Registry '{reg_unit.name}'")

            db_topics = db.query(Topic).filter(Topic.unit_id == reg_unit.id).all()
            db_topic_map = {t.id: t for t in db_topics}

            for reg_topic in reg_unit.topics:
                if reg_topic.id not in db_topic_map:
                    mismatches.append(f"Topic ID {reg_topic.id} ('{reg_topic.name}') missing in DB unit {reg_unit.id}")
                    continue
                db_t = db_topic_map[reg_topic.id]
                if db_t.name.strip().lower() != reg_topic.name.strip().lower():
                    mismatches.append(f"Topic ID {reg_topic.id} name mismatch: DB '{db_t.name}' != Registry '{reg_topic.name}'")

        return {
            "valid": len(mismatches) == 0,
            "course_id": course_id,
            "mismatches": mismatches,
            "units_verified": len(entry.units),
            "topics_verified": sum(len(u.topics) for u in entry.units),
        }


# Thread-safe global singleton
_GLOBAL_REGISTRY: Optional[TaxonomyRegistry] = None
_REGISTRY_LOCK = Lock()


def get_taxonomy_registry(definitions_dir: Optional[str] = None) -> TaxonomyRegistry:
    """Retrieve or initialize the global TaxonomyRegistry instance."""
    global _GLOBAL_REGISTRY
    with _REGISTRY_LOCK:
        if _GLOBAL_REGISTRY is None or (definitions_dir and _GLOBAL_REGISTRY.definitions_dir != definitions_dir):
            _GLOBAL_REGISTRY = TaxonomyRegistry(definitions_dir=definitions_dir)
        return _GLOBAL_REGISTRY


def reset_taxonomy_registry() -> None:
    """Reset the global singleton (primarily for test isolation)."""
    global _GLOBAL_REGISTRY
    with _REGISTRY_LOCK:
        _GLOBAL_REGISTRY = None
