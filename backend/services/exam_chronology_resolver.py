"""
Deterministic Exam Chronology & Metadata Resolver Service for MarkMint / Exam DNA.

Recovers missing exam year and assessment cycle metadata exclusively from verified,
deterministic evidence (institutional PDF headers, filenames, manifest entries).
Guaranteed:
- Zero mutation of database during resolution.
- Preserves all existing non-null metadata.
- Zero LLM dependencies or external network requests.
- Returns UNRESOLVED or AMBIGUOUS when evidence is non-deterministic.
- Completely idempotent and reproducible.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class EvidenceSource(str, Enum):
    EXISTING_METADATA = "EXISTING_METADATA"
    PDF_HEADER_ACADEMIC_YEAR = "PDF_HEADER_ACADEMIC_YEAR"
    PDF_HEADER_DATE = "PDF_HEADER_DATE"
    PDF_HEADER_MONTH_YEAR = "PDF_HEADER_MONTH_YEAR"
    PDF_HEADER_EXAM_TITLE = "PDF_HEADER_EXAM_TITLE"
    DOCUMENT_TITLE_ACADEMIC_YEAR = "DOCUMENT_TITLE_ACADEMIC_YEAR"
    DOCUMENT_TITLE_YEAR = "DOCUMENT_TITLE_YEAR"
    QUESTION_TEXT_HEADER = "QUESTION_TEXT_HEADER"
    UNRESOLVED_NO_EVIDENCE = "UNRESOLVED_NO_EVIDENCE"
    UNRESOLVED_QUESTION_BANK = "UNRESOLVED_QUESTION_BANK"
    UNRESOLVED_SCANNED = "UNRESOLVED_SCANNED"
    AMBIGUOUS_CONFLICTING = "AMBIGUOUS_CONFLICTING"


class ResolutionCategory(str, Enum):
    ALREADY_RESOLVED = "ALREADY_RESOLVED"
    RESOLVED_EXPLICIT = "RESOLVED_EXPLICIT"
    RESOLVED_STRONG = "RESOLVED_STRONG"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


@dataclass
class Evidence:
    source: EvidenceSource
    snippet: str
    confidence: str  # "HIGH", "MEDIUM", "LOW", "NONE"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    exam_id: int
    course_id: int
    course_name: str
    current_year: Optional[int]
    proposed_year: Optional[int]
    current_assessment_type: Optional[str]
    proposed_assessment_type: Optional[str]
    source_filename: str
    evidence_source: EvidenceSource
    evidence_snippet: str
    resolution_category: ResolutionCategory
    confidence: str
    reason: str
    is_mutation_candidate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "course_id": self.course_id,
            "course": self.course_name,
            "current_year": self.current_year,
            "proposed_year": self.proposed_year,
            "current_assessment_type": self.current_assessment_type,
            "proposed_assessment_type": self.proposed_assessment_type,
            "source_filename": self.source_filename,
            "evidence_source": self.evidence_source.value,
            "evidence_snippet": self.evidence_snippet,
            "resolution_category": self.resolution_category.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "is_mutation_candidate": self.is_mutation_candidate,
        }


class ExamChronologyResolver:
    """
    Deterministic resolver for exam years and assessment types.
    """

    # Academic Year: e.g. "Academic Year: 2022-23", "Academic Year 2023-2024"
    # Handles variable whitespace and optional colons/hyphens
    RE_ACADEMIC_YEAR = re.compile(
        r"Academic\s*Year\s*[:\-]?\s*(20\d\d)\s*[-–/]\s*(\d{2,4})",
        re.IGNORECASE,
    )

    # Date stamp: DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
    RE_DATE_STAMP = re.compile(
        r"\b(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](20[12]\d)\b"
    )

    # Month Year: e.g. "November 2022", "Nov 2023", "JULY 2024"
    RE_MONTH_YEAR = re.compile(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)[,\.\s\-/]+(20[12]\d)\b",
        re.IGNORECASE,
    )

    # Exam Title Year in Header: e.g. "Semester Examination - November / December - 2021"
    RE_EXAM_TITLE_YEAR = re.compile(
        r"(?:Semester\s+Examination|Cycle\s+Test|Model\s+Examination|Assessment\s+Test)"
        r"[\s\w\-/–—,]+(20[12]\d)\b",
        re.IGNORECASE,
    )

    # Course Regulation Code Pattern: e.g. 18PYB103J, 21CSS101J, 21CSC101T, 18CSC201J
    RE_COURSE_CODE = re.compile(
        r"\b(?:18|21)[A-Z]{2,4}\d{3,4}[A-Z]?\b",
        re.IGNORECASE,
    )

    # Cohort / Admission Year Pattern: e.g. "(For the candidates admitted from the academic year 2021-2022)"
    # This denotes regulation cohort, NOT the exam administration date.
    RE_COHORT_ADMISSION = re.compile(
        r"\(?For\s+the\s+candidates\s+admitted[^\)]*\)?",
        re.IGNORECASE,
    )

    # Question Bank / Multi-Unit compilation keywords in title
    RE_QUESTION_BANK = re.compile(
        r"(?:Question[\s_]*Bank|Short[\s_]*Answer[\s_]*Questions|ALL[\s_]*CT[\s_]*COMPILATION|"
        r"ALL[\s_]*UNIT|Chapter[\s_]*\d|\bQB\b|Notes[\s_]+CT|compilation)",
        re.IGNORECASE,
    )

    # Assessment Type Regexes
    RE_CT1 = re.compile(
        r"\bCycle\s*Test\s*[-–—]?\s*(?:I|1)\b|\bCT\s*[-–—]?\s*1\b|\bCAT\s*[-–—]?\s*1\b|\bCLA\s*[-–—]?\s*1\b",
        re.IGNORECASE,
    )
    RE_CT2 = re.compile(
        r"\bCycle\s*Test\s*[-–—]?\s*(?:II|2)\b|\bCT\s*[-–—]?\s*2\b|\bCAT\s*[-–—]?\s*2\b|\bCLA\s*[-–—]?\s*2\b|\bFT\s*[-–—]?\s*(?:II|2)\b",
        re.IGNORECASE,
    )
    RE_CT3 = re.compile(
        r"\bCycle\s*Test\s*[-–—]?\s*(?:III|3)\b|\bCT\s*[-–—]?\s*3\b|\bCAT\s*[-–—]?\s*3\b",
        re.IGNORECASE,
    )
    RE_MODEL = re.compile(
        r"\bModel\s*(?:Exam|Examination|QP|Paper|Test)\b|\bModel\b",
        re.IGNORECASE,
    )
    RE_END_SEM = re.compile(
        r"\b(?:Semester|University|Degree)\s*Examination\b|\bEnd\s*Sem(?:ester)?\b|\bEND_SEM\b",
        re.IGNORECASE,
    )

    @classmethod
    def clean_header_text(cls, text: str) -> str:
        """
        Strips non-exam chronological noise:
        1. Cohort admission statements: '(For the candidates admitted from...)'
        2. Course regulation codes: '18PYB103J', '21CSS101J'
        """
        if not text:
            return ""
        # Strip admission cohort lines first so their internal years disappear
        text = cls.RE_COHORT_ADMISSION.sub(" ", text)
        # Strip course codes
        text = cls.RE_COURSE_CODE.sub(" ", text)
        return text

    @classmethod
    def strip_course_codes(cls, text: str) -> str:
        """Strips course codes like 18PYB103J to prevent their regulation prefix being parsed as year."""
        return cls.RE_COURSE_CODE.sub(" ", text)

    @classmethod
    def is_question_bank_or_compilation(cls, title: str) -> bool:
        """Determines if a document title indicates a non-exam compilation or question bank."""
        if not title:
            return False
        return bool(cls.RE_QUESTION_BANK.search(title))

    @classmethod
    def extract_assessment_type_from_text(cls, text: str) -> Optional[str]:
        """Deterministically extracts standardized assessment type from header or title text."""
        if not text:
            return None
        if cls.RE_CT1.search(text):
            return "CT1"
        if cls.RE_CT2.search(text):
            return "CT2"
        if cls.RE_CT3.search(text):
            return "CT3"
        if cls.RE_MODEL.search(text):
            return "Model"
        if cls.RE_END_SEM.search(text):
            return "END_SEM"
        return None

    @classmethod
    def extract_year_from_header_text(
        cls, header_text: str
    ) -> Tuple[Optional[int], Optional[Evidence]]:
        """
        Parses the first 1-2 pages of an exam paper header.
        Extracts year according to deterministic precedence:
        1. Explicit Date Stamp (e.g. 04-10-2023)
        2. Explicit Month-Year / Degree Examination Header (e.g. DEGREE EXAMINATION, MAY 2023)
        3. Explicit Academic Year (e.g. Academic Year: 2023-24)
        4. Exam Title Year
        """
        if not header_text or len(header_text.strip()) == 0:
            return None, None

        # Clean chronological noise
        clean_header = cls.clean_header_text(header_text)

        # 1. Date stamp in header
        date_match = cls.RE_DATE_STAMP.search(clean_header)
        if date_match:
            yr = int(date_match.group(3))
            if 2010 <= yr <= 2030:
                evidence = Evidence(
                    source=EvidenceSource.PDF_HEADER_DATE,
                    snippet=date_match.group(0),
                    confidence="HIGH",
                    details={"matched": date_match.group(0), "year": yr},
                )
                return yr, evidence

        # 2. Month + Year in header (Degree Examination, MAY 2023, etc.)
        month_match = cls.RE_MONTH_YEAR.search(clean_header)
        if month_match:
            yr = int(month_match.group(2))
            if 2010 <= yr <= 2030:
                evidence = Evidence(
                    source=EvidenceSource.PDF_HEADER_MONTH_YEAR,
                    snippet=month_match.group(0),
                    confidence="HIGH",
                    details={"matched": month_match.group(0), "year": yr},
                )
                return yr, evidence

        # 3. Academic Year in header (Cycle Tests)
        ay_match = cls.RE_ACADEMIC_YEAR.search(clean_header)
        if ay_match:
            y1 = int(ay_match.group(1))
            if 2010 <= y1 <= 2030:
                evidence = Evidence(
                    source=EvidenceSource.PDF_HEADER_ACADEMIC_YEAR,
                    snippet=ay_match.group(0),
                    confidence="HIGH",
                    details={"matched": ay_match.group(0), "base_year": y1},
                )
                return y1, evidence

        # 4. Exam Title Year
        exam_yr_match = cls.RE_EXAM_TITLE_YEAR.search(clean_header)
        if exam_yr_match:
            yr = int(exam_yr_match.group(1))
            if 2010 <= yr <= 2030:
                evidence = Evidence(
                    source=EvidenceSource.PDF_HEADER_EXAM_TITLE,
                    snippet=exam_yr_match.group(0),
                    confidence="HIGH",
                    details={"matched": exam_yr_match.group(0), "year": yr},
                )
                return yr, evidence

        return None, None

    @classmethod
    def extract_year_from_title(
        cls, title: str
    ) -> Tuple[Optional[int], Optional[Evidence]]:
        """Extracts year from filename or document title if unambiguously present."""
        if not title:
            return None, None

        clean_title = cls.strip_course_codes(title)

        # Academic year in title
        ay_match = cls.RE_ACADEMIC_YEAR.search(clean_title)
        if ay_match:
            y1 = int(ay_match.group(1))
            if 2010 <= y1 <= 2030:
                return y1, Evidence(
                    source=EvidenceSource.DOCUMENT_TITLE_ACADEMIC_YEAR,
                    snippet=ay_match.group(0),
                    confidence="MEDIUM-HIGH",
                    details={"matched": ay_match.group(0), "base_year": y1},
                )

        # Standalone year in title
        year_matches = re.findall(r"\b(20[12]\d)\b", clean_title)
        if len(year_matches) == 1:
            yr = int(year_matches[0])
            if 2010 <= yr <= 2030:
                return yr, Evidence(
                    source=EvidenceSource.DOCUMENT_TITLE_YEAR,
                    snippet=year_matches[0],
                    confidence="MEDIUM-HIGH",
                    details={"year": yr},
                )
        elif len(year_matches) > 1:
            # Conflicting years in title
            return None, Evidence(
                source=EvidenceSource.AMBIGUOUS_CONFLICTING,
                snippet=f"Multiple years in title: {year_matches}",
                confidence="LOW",
                details={"years": year_matches},
            )

        return None, None

    @classmethod
    def read_pdf_header(
        cls, local_path: Optional[str], max_pages: int = 2
    ) -> Tuple[str, int, bool]:
        """
        Safely reads the top header text from the local PDF file.
        Returns (header_text, num_pages, is_scanned).
        """
        if not local_path or not os.path.exists(local_path):
            return "", 0, False

        try:
            import pymupdf  # PyMuPDF
            doc = pymupdf.open(local_path)
            num_pages = len(doc)
            header_text = ""
            for pno in range(min(max_pages, num_pages)):
                header_text += " " + doc[pno].get_text()
            doc.close()

            is_scanned = num_pages > 0 and len(header_text.strip()) == 0
            return header_text, num_pages, is_scanned
        except Exception:
            return "", 0, False

    @classmethod
    def resolve_exam(
        cls,
        exam_id: int,
        course_id: int,
        course_name: str,
        current_year: Optional[int],
        current_assessment_type: Optional[str],
        source_title: str,
        local_path: Optional[str] = None,
        question_texts: Optional[List[str]] = None,
    ) -> ResolutionResult:
        """
        Resolves an individual exam deterministically according to precedence hierarchy.
        """
        # Rule 1 & 2: Preserve existing non-null metadata
        if current_year is not None:
            return ResolutionResult(
                exam_id=exam_id,
                course_id=course_id,
                course_name=course_name,
                current_year=current_year,
                proposed_year=current_year,
                current_assessment_type=current_assessment_type,
                proposed_assessment_type=current_assessment_type,
                source_filename=source_title or "",
                evidence_source=EvidenceSource.EXISTING_METADATA,
                evidence_snippet=str(current_year),
                resolution_category=ResolutionCategory.ALREADY_RESOLVED,
                confidence="HIGH",
                reason="Existing non-null year preserved",
                is_mutation_candidate=False,
            )

        # Check if file indicates question bank or syllabus compilation
        is_qb = cls.is_question_bank_or_compilation(source_title)

        # Try Tier 1: PDF Header Text
        header_text, num_pages, is_scanned = cls.read_pdf_header(local_path)

        # Check assessment type candidate from header or title
        cand_atype = cls.extract_assessment_type_from_text(header_text) or cls.extract_assessment_type_from_text(source_title)
        # Normalize proposed assessment type: preserve existing if already meaningful, otherwise propose
        proposed_atype = current_assessment_type
        if current_assessment_type in (None, "None", "UNKNOWN", "") and cand_atype:
            proposed_atype = cand_atype

        # Check for year in header
        cand_year, header_evidence = cls.extract_year_from_header_text(header_text)
        if cand_year is not None and header_evidence is not None:
            return ResolutionResult(
                exam_id=exam_id,
                course_id=course_id,
                course_name=course_name,
                current_year=None,
                proposed_year=cand_year,
                current_assessment_type=current_assessment_type,
                proposed_assessment_type=proposed_atype,
                source_filename=source_title or "",
                evidence_source=header_evidence.source,
                evidence_snippet=header_evidence.snippet,
                resolution_category=ResolutionCategory.RESOLVED_EXPLICIT,
                confidence=header_evidence.confidence,
                reason="Explicit date / academic year found in PDF header",
                is_mutation_candidate=True,
            )

        # Try Tier 2: Title / Filename
        title_year, title_evidence = cls.extract_year_from_title(source_title)
        if title_year is not None and title_evidence is not None and not is_qb:
            return ResolutionResult(
                exam_id=exam_id,
                course_id=course_id,
                course_name=course_name,
                current_year=None,
                proposed_year=title_year,
                current_assessment_type=current_assessment_type,
                proposed_assessment_type=proposed_atype,
                source_filename=source_title or "",
                evidence_source=title_evidence.source,
                evidence_snippet=title_evidence.snippet,
                resolution_category=ResolutionCategory.RESOLVED_STRONG,
                confidence=title_evidence.confidence,
                reason="Explicit year found in document title",
                is_mutation_candidate=True,
            )

        # Check Tier 3: Ingested question text header leakage
        if question_texts:
            all_q_text = " ".join(question_texts[:10])
            ay_q_match = cls.RE_ACADEMIC_YEAR.search(cls.strip_course_codes(all_q_text))
            if ay_q_match and not is_qb:
                y1 = int(ay_q_match.group(1))
                if 2010 <= y1 <= 2030:
                    return ResolutionResult(
                        exam_id=exam_id,
                        course_id=course_id,
                        course_name=course_name,
                        current_year=None,
                        proposed_year=y1,
                        current_assessment_type=current_assessment_type,
                        proposed_assessment_type=proposed_atype,
                        source_filename=source_title or "",
                        evidence_source=EvidenceSource.QUESTION_TEXT_HEADER,
                        evidence_snippet=ay_q_match.group(0),
                        resolution_category=ResolutionCategory.RESOLVED_STRONG,
                        confidence="MEDIUM",
                        reason="Explicit academic session found in question OCR header",
                        is_mutation_candidate=True,
                    )

        # Check Ambiguous / Unresolved
        if title_evidence and title_evidence.source == EvidenceSource.AMBIGUOUS_CONFLICTING:
            return ResolutionResult(
                exam_id=exam_id,
                course_id=course_id,
                course_name=course_name,
                current_year=None,
                proposed_year=None,
                current_assessment_type=current_assessment_type,
                proposed_assessment_type=current_assessment_type,
                source_filename=source_title or "",
                evidence_source=EvidenceSource.AMBIGUOUS_CONFLICTING,
                evidence_snippet=title_evidence.snippet,
                resolution_category=ResolutionCategory.AMBIGUOUS,
                confidence="LOW",
                reason="Conflicting years detected in metadata",
                is_mutation_candidate=False,
            )

        if is_qb:
            return ResolutionResult(
                exam_id=exam_id,
                course_id=course_id,
                course_name=course_name,
                current_year=None,
                proposed_year=None,
                current_assessment_type=current_assessment_type,
                proposed_assessment_type=proposed_atype,
                source_filename=source_title or "",
                evidence_source=EvidenceSource.UNRESOLVED_QUESTION_BANK,
                evidence_snippet=f"Title indicates question bank or compilation: '{source_title}'",
                resolution_category=ResolutionCategory.UNRESOLVED,
                confidence="HIGH",
                reason="Question bank / multi-unit compilation without single exam date; year intentionally left None",
                is_mutation_candidate=False,
            )

        if is_scanned:
            return ResolutionResult(
                exam_id=exam_id,
                course_id=course_id,
                course_name=course_name,
                current_year=None,
                proposed_year=None,
                current_assessment_type=current_assessment_type,
                proposed_assessment_type=proposed_atype,
                source_filename=source_title or "",
                evidence_source=EvidenceSource.UNRESOLVED_SCANNED,
                evidence_snippet=f"Image-only PDF ({num_pages} pgs) without text layer",
                resolution_category=ResolutionCategory.UNRESOLVED,
                confidence="NONE",
                reason="Scanned PDF without extractable text layer or date header",
                is_mutation_candidate=False,
            )

        # General unresolved
        snippet = header_text[:80].strip() if header_text else "No text or file available"
        return ResolutionResult(
            exam_id=exam_id,
            course_id=course_id,
            course_name=course_name,
            current_year=None,
            proposed_year=None,
            current_assessment_type=current_assessment_type,
            proposed_assessment_type=proposed_atype,
            source_filename=source_title or "",
            evidence_source=EvidenceSource.UNRESOLVED_NO_EVIDENCE,
            evidence_snippet=snippet,
            resolution_category=ResolutionCategory.UNRESOLVED,
            confidence="NONE",
            reason="No explicit date or academic year pattern found",
            is_mutation_candidate=False,
        )
