"""
Deterministic multi-signal classifier for academic resources.
Classifies resources into PYQ, STUDY_MATERIAL, SYLLABUS, ASSIGNMENT, LAB, REFERENCE, OTHER, UNKNOWN.
Extracts assessment years and types without hallucinating.
"""

import re
from typing import Optional, List, Tuple
from .models import ResourceClassification, ClassificationResult


class ResourceClassifier:
    """Deterministic, explainable rule-based academic document classifier."""

    # PYQ patterns with weights
    PYQ_PATTERNS = [
        (r"\bpyqs?\b", 1.0, "Contains keyword 'PYQ'"),
        (r"\bprevious\s+years?\b", 0.95, "Contains 'previous year'"),
        (r"\bprev\s+years?\b", 0.9, "Contains 'prev year'"),
        (r"\bpast\s+years?\b", 0.9, "Contains 'past year'"),
        (r"\bquestion\s+papers?\b", 0.95, "Contains 'question paper'"),
        (r"\bq\.?p\.?\b", 0.7, "Contains abbreviation 'QP'"),
        (r"\bold\s+questions?\b", 0.8, "Contains 'old question'"),
        (r"\bclass\s*tests?\b", 0.9, "Contains 'class test'"),
        (r"\bcycle\s*tests?\b", 0.9, "Contains 'cycle test'"),
        (r"\bct\s*[1-3]\b", 0.95, "Contains CT assessment pattern (CT1/CT2/CT3)"),
        (r"\bct[-_][1-3]\b", 0.95, "Contains CT assessment pattern"),
        (r"\bend\s*sem(?:ester)?\b", 0.95, "Contains 'end sem'"),
        (r"\bmid\s*sem(?:ester)?\b", 0.9, "Contains 'mid sem'"),
        (r"\bmidterm\b", 0.85, "Contains 'midterm'"),
        (r"\bmodel\s+exam\b", 0.85, "Contains 'model exam'"),
        (r"\bmodel\s+papers?\b", 0.85, "Contains 'model paper'"),
        (r"\bsem\s+exam\b", 0.85, "Contains 'sem exam'"),
        (r"\bexamination\s+papers?\b", 0.95, "Contains 'examination paper'"),
        (r"\bexam\s+paper\b", 0.9, "Contains 'exam paper'"),
        (r"\bquestion\s+banks?\b", 0.75, "Contains 'question bank'"),
    ]

    # Study material patterns with weights
    STUDY_PATTERNS = [
        (r"\blecture\s*notes?\b", 1.0, "Contains 'lecture notes'"),
        (r"\bnotes?\b", 0.75, "Contains 'notes'"),
        (r"\bunit\s*[1-5]\b", 0.9, "Contains unit marker (e.g. Unit 1)"),
        (r"\bunitwise\b", 0.95, "Contains 'unitwise'"),
        (r"\bmodule\s*[1-5]\b", 0.9, "Contains module marker"),
        (r"\bchapter\s*\d+\b", 0.85, "Contains chapter marker"),
        (r"\bhandouts?\b", 0.85, "Contains 'handout'"),
        (r"\bslides?\b", 0.8, "Contains 'slides'"),
        (r"\bpresentations?\b", 0.8, "Contains 'presentation'"),
        (r"\bstudy\s+materials?\b", 0.95, "Contains 'study material'"),
        (r"\bcourse\s+materials?\b", 0.9, "Contains 'course material'"),
        (r"\btutorials?\b", 0.7, "Contains 'tutorial'"),
        (r"\bformula\s+sheet\b", 0.85, "Contains 'formula sheet'"),
        (r"\bsummary\b", 0.65, "Contains 'summary'"),
    ]

    # Syllabus patterns
    SYLLABUS_PATTERNS = [
        (r"\bsyllabus\b", 1.0, "Contains 'syllabus'"),
        (r"\bcurriculum\b", 0.9, "Contains 'curriculum'"),
        (r"\bcourse\s+outline\b", 0.9, "Contains 'course outline'"),
        (r"\bcourse\s+plan\b", 0.9, "Contains 'course plan'"),
    ]

    # Lab patterns
    LAB_PATTERNS = [
        (r"\blab\s+manual\b", 1.0, "Contains 'lab manual'"),
        (r"\blaboratory\b", 0.85, "Contains 'laboratory'"),
        (r"\bpractical\b", 0.8, "Contains 'practical'"),
        (r"\bexperiments?\b", 0.75, "Contains 'experiment'"),
        (r"\bviva\b", 0.8, "Contains 'viva'"),
    ]

    # Assignment patterns
    ASSIGNMENT_PATTERNS = [
        (r"\bassignments?\b", 0.95, "Contains 'assignment'"),
        (r"\bhomework\b", 0.9, "Contains 'homework'"),
        (r"\bproblem\s+sets?\b", 0.85, "Contains 'problem set'"),
    ]

    # Reference patterns
    REFERENCE_PATTERNS = [
        (r"\btextbooks?\b", 0.9, "Contains 'textbook'"),
        (r"\breference\s+books?\b", 0.95, "Contains 'reference book'"),
    ]

    # Year patterns: 2010 to 2030
    YEAR_PATTERNS = [
        r"\b(20[1-3][0-9])\b",
        r"\b(?:jan|january|feb|february|mar|march|apr|april|may|june?|july?|aug|august|sep|september|oct|october|nov|november|dec|december)\s+(20[1-3][0-9])\b",
        r"\b(20[1-3][0-9])\s+(?:jan|january|feb|february|mar|march|apr|april|may|june?|july?|aug|august|sep|september|oct|october|nov|november|dec|december)\b",
    ]

    # Assessment type patterns
    ASSESSMENT_PATTERNS = [
        (r"\bct\s*1\b|\bct-1\b|\bcycle\s*test\s*1\b|\bclass\s*test\s*1\b", "CT1"),
        (r"\bct\s*2\b|\bct-2\b|\bcycle\s*test\s*2\b|\bclass\s*test\s*2\b", "CT2"),
        (r"\bct\s*3\b|\bct-3\b|\bcycle\s*test\s*3\b|\bclass\s*test\s*3\b", "CT3"),
        (r"\bend\s*sem(?:ester)?\b|\bendsem(?:ester)?\b|\bsemester\s*exam\b|\bfinal\s*exam\b", "END_SEM"),
        (r"\bmid\s*sem(?:ester)?\b|\bmidsem(?:ester)?\b|\bmidterm\b|\bmid[- ]term\b", "MID_SEM"),
        (r"\bmodel\s*(?:exam|paper|test)\b", "MODEL"),
    ]

    @classmethod
    def extract_year(cls, text: str) -> Optional[int]:
        """Extract valid academic year (2010..2030). Returns None if not explicitly present."""
        if not text:
            return None
        text_lower = text.lower()
        for pattern in cls.YEAR_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                for grp in match.groups():
                    if grp and grp.isdigit():
                        yr = int(grp)
                        if 2010 <= yr <= 2030:
                            return yr
        return None

    @classmethod
    def extract_assessment_type(cls, text: str) -> Optional[str]:
        """Extract assessment type (CT1, CT2, END_SEM, etc.). Returns None if not found."""
        if not text:
            return None
        text_lower = text.lower()
        for pattern, atype in cls.ASSESSMENT_PATTERNS:
            if re.search(pattern, text_lower):
                return atype
        return None

    @classmethod
    def classify(
        cls,
        title: str,
        filename: Optional[str] = None,
        source_type: Optional[str] = None,
        drive_path: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Deterministic multi-factor classifier.
        Evaluates title, filename, source_type, and folder path hierarchy.
        """
        combined = " ".join(filter(None, [title, filename, source_type, drive_path])).lower()

        reasons: List[str] = []
        year = cls.extract_year(combined)
        assessment_type = cls.extract_assessment_type(combined)

        if year:
            reasons.append(f"Detected academic year: {year}")
        if assessment_type:
            reasons.append(f"Detected assessment type: {assessment_type}")

        # Check explicit source_type hint if present
        source_type_lower = (source_type or "").lower()
        if source_type_lower in ["pyq", "pyqs", "examination papers / pyqs", "ct papers"]:
            reasons.append(f"Source catalog explicitly tagged as: '{source_type}'")
        elif source_type_lower in ["ppt", "ppts", "lecture notes", "notes"]:
            reasons.append(f"Source catalog explicitly tagged as: '{source_type}'")

        # Calculate category scores
        scores: Dict[str, float] = {
            ResourceClassification.PYQ.value: 0.0,
            ResourceClassification.STUDY_MATERIAL.value: 0.0,
            ResourceClassification.SYLLABUS.value: 0.0,
            ResourceClassification.LAB.value: 0.0,
            ResourceClassification.ASSIGNMENT.value: 0.0,
            ResourceClassification.REFERENCE.value: 0.0,
        }

        # Match PYQ
        for pat, weight, desc in cls.PYQ_PATTERNS:
            if re.search(pat, combined):
                scores[ResourceClassification.PYQ.value] = max(
                    scores[ResourceClassification.PYQ.value], weight
                )
                reasons.append(desc)

        # Match Study Material
        for pat, weight, desc in cls.STUDY_PATTERNS:
            if re.search(pat, combined):
                scores[ResourceClassification.STUDY_MATERIAL.value] = max(
                    scores[ResourceClassification.STUDY_MATERIAL.value], weight
                )
                reasons.append(desc)

        # Match Syllabus
        for pat, weight, desc in cls.SYLLABUS_PATTERNS:
            if re.search(pat, combined):
                scores[ResourceClassification.SYLLABUS.value] = max(
                    scores[ResourceClassification.SYLLABUS.value], weight
                )
                reasons.append(desc)

        # Match Lab
        for pat, weight, desc in cls.LAB_PATTERNS:
            if re.search(pat, combined):
                scores[ResourceClassification.LAB.value] = max(
                    scores[ResourceClassification.LAB.value], weight
                )
                reasons.append(desc)

        # Match Assignment
        for pat, weight, desc in cls.ASSIGNMENT_PATTERNS:
            if re.search(pat, combined):
                scores[ResourceClassification.ASSIGNMENT.value] = max(
                    scores[ResourceClassification.ASSIGNMENT.value], weight
                )
                reasons.append(desc)

        # Match Reference
        for pat, weight, desc in cls.REFERENCE_PATTERNS:
            if re.search(pat, combined):
                scores[ResourceClassification.REFERENCE.value] = max(
                    scores[ResourceClassification.REFERENCE.value], weight
                )
                reasons.append(desc)

        # Boost from source_type
        if source_type_lower in ["pyq", "pyqs", "ct papers"]:
            scores[ResourceClassification.PYQ.value] = max(
                scores[ResourceClassification.PYQ.value], 0.95
            )
        elif source_type_lower in ["ppt", "ppts", "lecture notes"]:
            scores[ResourceClassification.STUDY_MATERIAL.value] = max(
                scores[ResourceClassification.STUDY_MATERIAL.value], 0.95
            )
        elif source_type_lower == "syllabus":
            scores[ResourceClassification.SYLLABUS.value] = max(
                scores[ResourceClassification.SYLLABUS.value], 0.95
            )

        # Boost PYQ if assessment_type was explicitly detected
        if assessment_type and scores[ResourceClassification.PYQ.value] > 0.0:
            scores[ResourceClassification.PYQ.value] = min(1.0, scores[ResourceClassification.PYQ.value] + 0.1)

        # Prioritize explicit filename notes/study-material indicators over inherited folder path PYQ keywords
        explicit_name = " ".join(filter(None, [title, filename])).lower()
        has_explicit_notes = bool(re.search(r"(?:^|[\s_/-])(?:lecture[\s_/-]*)?notes?|\bhandouts?\b|\bformula\s+sheet\b|\bsummary\b", explicit_name))
        has_explicit_pyq = bool(re.search(r"\b(?:pyqs?|question\s*papers?|qp)\b", explicit_name))
        if has_explicit_notes and not has_explicit_pyq:
            scores[ResourceClassification.STUDY_MATERIAL.value] = max(
                scores[ResourceClassification.STUDY_MATERIAL.value], 0.95
            )
            if scores[ResourceClassification.PYQ.value] > 0.8:
                scores[ResourceClassification.PYQ.value] = 0.5
            reasons.append("Prioritized explicit 'notes' in filename over inherited folder keywords")

        # Find best candidate
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_scores[0]
        second_cat, second_score = sorted_scores[1]

        # Uncertainty threshold: require >= 0.6 confidence and a margin over runner-up if runner-up is strong
        if top_score < 0.6:
            return ClassificationResult(
                category=ResourceClassification.UNKNOWN,
                confidence=top_score,
                reasons=["Insufficient confidence signals"] + reasons,
                extracted_year=year,
                assessment_type=assessment_type,
            )

        # If PYQ and STUDY_MATERIAL are in direct contention without clear winner
        if top_cat in [ResourceClassification.PYQ.value, ResourceClassification.STUDY_MATERIAL.value] and \
           second_cat in [ResourceClassification.PYQ.value, ResourceClassification.STUDY_MATERIAL.value] and \
           (top_score - second_score) < 0.15:
            return ClassificationResult(
                category=ResourceClassification.UNKNOWN,
                confidence=top_score,
                reasons=["Conflicting PYQ and Study Material signals"] + reasons,
                extracted_year=year,
                assessment_type=assessment_type,
            )

        return ClassificationResult(
            category=ResourceClassification(top_cat),
            confidence=round(top_score, 2),
            reasons=reasons,
            extracted_year=year,
            assessment_type=assessment_type,
        )
