"""
Declarative taxonomy data models and schemas for MarkMint.
Provides strict dataclasses representing syllabus structure, units, topics,
classification rules, provenance, and taxonomy versioning.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TopicDefinition:
    """Structured configuration for a single syllabus topic within a unit."""
    id: int
    name: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    strong_phrases: List[str] = field(default_factory=list)
    specific_keywords: List[str] = field(default_factory=list)
    negative_guards: List[str] = field(default_factory=list)
    context_hints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "canonical_name": self.canonical_name,
            "aliases": self.aliases,
            "strong_phrases": self.strong_phrases,
            "specific_keywords": self.specific_keywords,
            "negative_guards": self.negative_guards,
            "context_hints": self.context_hints,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopicDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            canonical_name=data.get("canonical_name", data["name"]),
            aliases=data.get("aliases", []),
            strong_phrases=data.get("strong_phrases", []),
            specific_keywords=data.get("specific_keywords", []),
            negative_guards=data.get("negative_guards", []),
            context_hints=data.get("context_hints", []),
        )


@dataclass
class UnitDefinition:
    """Structured configuration for a syllabus unit containing topics."""
    id: int
    number: int
    name: str
    topics: List[TopicDefinition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "topics": [t.to_dict() for t in self.topics],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnitDefinition":
        return cls(
            id=data["id"],
            number=data["number"],
            name=data["name"],
            topics=[TopicDefinition.from_dict(t) for t in data.get("topics", [])],
        )


@dataclass
class CourseDefinition:
    """Course metadata identifying the subject in the canonical registry."""
    id: int
    name: str
    canonical_code: str
    code: str
    regulation_year: Optional[int] = None
    department: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "canonical_code": self.canonical_code,
            "code": self.code,
            "regulation_year": self.regulation_year,
            "department": self.department,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CourseDefinition":
        return cls(
            id=data["id"],
            name=data["name"],
            canonical_code=data.get("canonical_code", ""),
            code=data.get("code", ""),
            regulation_year=data.get("regulation_year"),
            department=data.get("department"),
        )


@dataclass
class ProvenanceDefinition:
    """Authoritative source and regulation provenance for the syllabus."""
    source_document: str
    regulation: str
    approved_by: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_document": self.source_document,
            "regulation": self.regulation,
            "approved_by": self.approved_by,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceDefinition":
        return cls(
            source_document=data.get("source_document", ""),
            regulation=data.get("regulation", ""),
            approved_by=data.get("approved_by", ""),
            notes=data.get("notes", ""),
        )


@dataclass
class CourseTaxonomyRegistryEntry:
    """Complete declarative taxonomy configuration for a course."""
    schema_version: str
    taxonomy_version: str
    course: CourseDefinition
    provenance: ProvenanceDefinition
    units: List[UnitDefinition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "taxonomy_version": self.taxonomy_version,
            "course": self.course.to_dict(),
            "provenance": self.provenance.to_dict(),
            "units": [u.to_dict() for u in self.units],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CourseTaxonomyRegistryEntry":
        required_fields = ["schema_version", "taxonomy_version", "course", "provenance", "units"]
        for rf in required_fields:
            if rf not in data:
                raise ValueError(f"Malformed taxonomy definition: missing required field '{rf}'")

        return cls(
            schema_version=data["schema_version"],
            taxonomy_version=data["taxonomy_version"],
            course=CourseDefinition.from_dict(data["course"]),
            provenance=ProvenanceDefinition.from_dict(data["provenance"]),
            units=[UnitDefinition.from_dict(u) for u in data["units"]],
        )
