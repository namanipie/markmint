import io
import re
import hashlib
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import pdfplumber

from backend.models.core import Document, Course, Topic, Unit, Syllabus
from backend.models.submission import PaperSubmission, ConsistencyStatus

MAX_SUBMISSION_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hexadecimal hash from byte payload."""
    return hashlib.sha256(content).hexdigest()


def validate_pdf_content(content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validates that the byte payload is a valid, uncorrupted PDF within size constraints.
    """
    if not content:
        return False, "File is empty."

    if len(content) > MAX_SUBMISSION_SIZE_BYTES:
        return False, f"File size ({len(content) / (1024 * 1024):.1f} MB) exceeds maximum allowed 20 MB."

    if not content.startswith(b"%PDF-"):
        return False, "Invalid file format: Missing '%PDF-' header signature."

    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if len(pdf.pages) == 0:
                return False, "PDF contains zero pages."
    except Exception as e:
        return False, f"Corrupted or unreadable PDF: {str(e)}"

    return True, None


def extract_preview_text(content: bytes, max_pages: int = 5) -> Tuple[str, int]:
    """
    Deterministically extracts text from up to max_pages without heavy OCR for instant preview.
    Returns (extracted_text, total_pages).
    """
    total_pages = 0
    pages_text = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        total_pages = len(pdf.pages)
        pages_to_read = min(total_pages, max_pages)
        for i in range(pages_to_read):
            text = pdf.pages[i].extract_text()
            if text and text.strip():
                pages_text.append(f"--- PAGE {i + 1} ---\n" + text.strip())

    combined_text = "\n\n".join(pages_text)
    return combined_text, total_pages


def detect_metadata_from_text(text: str) -> Dict[str, Any]:
    """
    Applies heuristic regular expressions to detect:
    - Academic Year (e.g. 2018 - 2026)
    - Assessment Cycle (Cycle Test 1, Cycle Test 2, End Semester, Model Exam)
    - Course Code (e.g. 21CSC201J, 21MTH101T)
    """
    detected_year: Optional[int] = None
    detected_cycle: Optional[str] = None
    detected_course_code: Optional[str] = None

    if not text:
        return {
            "year": None,
            "assessment": None,
            "course_code": None,
        }

    # 1. Course Code Detection (SRMIST style: 21CSC201J, 18MTH101T, etc.)
    code_pattern = re.compile(r"\b(\d{2}[A-Z]{3}\d{3}[A-Z]?|[A-Z]{2,4}\d{3,4})\b")
    # Search in upper text
    code_matches = code_pattern.findall(text.upper())
    # Exclude common non-course token false positives like "ISO9001", "HTML5"
    filtered_codes = [c for c in code_matches if not re.match(r"^(ISO|PAGE|PART|SECTION|REV)\d+", c)]
    if filtered_codes:
        detected_course_code = filtered_codes[0]

    # 2. Year Detection
    # Look for year patterns in exam context: e.g. "May 2023", "Nov/Dec 2022", "2023-2024", "2024"
    year_context_pattern = re.compile(
        r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|SEMESTER|EXAMINATION|ACADEMIC\s+YEAR)[^\d\n]{0,25}(201[8-9]|202[0-6])",
        re.IGNORECASE
    )
    year_match = year_context_pattern.search(text)
    if year_match:
        detected_year = int(year_match.group(1))
    else:
        # Fallback to standalone year
        standalone_year = re.search(r"\b(201[8-9]|202[0-6])\b", text)
        if standalone_year:
            detected_year = int(standalone_year.group(1))

    # 3. Assessment Cycle Detection
    text_lower = text.lower()
    if re.search(r"\b(cycle\s*test\s*[-–—]?\s*(?:1|i\b)|ct\s*[-–—]?\s*1\b|first\s+cycle\s+test)", text_lower):
        detected_cycle = "Cycle Test 1"
    elif re.search(r"\b(cycle\s*test\s*[-–—]?\s*(?:2|ii\b)|ct\s*[-–—]?\s*2\b|second\s+cycle\s+test)", text_lower):
        detected_cycle = "Cycle Test 2"
    elif re.search(r"\b(model\s+(?:examination|exam))", text_lower):
        detected_cycle = "Model Exam"
    elif re.search(r"\b(end\s*sem(?:ester)?|university\s+examination|semester\s+examination|regular\s+examination)", text_lower):
        detected_cycle = "End Semester"

    return {
        "year": detected_year,
        "assessment": detected_cycle,
        "course_code": detected_course_code,
    }


def evaluate_course_consistency(
    db: Session,
    course_id: Optional[int],
    extracted_text: str,
    detected_course_code: Optional[str]
) -> Tuple[float, str, str]:
    """
    Evaluates consistency between the declared course and the extracted document text.
    Returns: (consistency_score [0.0 - 1.0], consistency_status, consistency_notes)
    """
    if not course_id:
        return 0.5, ConsistencyStatus.UNCERTAIN.value, "No course ID selected for verification."

    course = db.query(Course).get(course_id)
    if not course:
        return 0.0, ConsistencyStatus.MISMATCH.value, f"Course ID {course_id} does not exist in curriculum."

    notes = []
    target_code = (course.code or "").upper().strip()
    target_name = (course.name or "").lower().strip()

    # 1. Course Code Check
    if detected_course_code:
        norm_detected = detected_course_code.upper().strip()
        if norm_detected == target_code:
            notes.append(f"Exact course code match detected: '{norm_detected}'.")
            return 1.0, ConsistencyStatus.CONSISTENT.value, " ".join(notes)
        else:
            # Check if detected code belongs to another known course in database
            other_course = db.query(Course).filter(Course.code == norm_detected).first()
            if other_course and other_course.id != course.id:
                notes.append(
                    f"Warning: Document contains course code '{norm_detected}' corresponding to '{other_course.name}', which conflicts with declared '{course.name}' ({target_code})."
                )
                return 0.1, ConsistencyStatus.MISMATCH.value, " ".join(notes)
            else:
                notes.append(f"Detected code '{norm_detected}' differs from target code '{target_code}'.")

    # 2. Text Keyword and Topic Overlap Check
    text_lower = extracted_text.lower()
    
    # Check course name words
    name_words = [w for w in re.split(r"\W+", target_name) if len(w) > 3 and w not in ["engineering", "science", "technology", "introductory", "basic"]]
    name_hits = [w for w in name_words if w in text_lower]

    # Fetch canonical syllabus topics for the course
    topics = (
        db.query(Topic.name)
        .join(Unit, Topic.unit_id == Unit.id)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == course_id)
        .all()
    )

    topic_hits = []
    for (t_name,) in topics:
        clean_topic = t_name.lower().strip()
        if len(clean_topic) > 4 and clean_topic in text_lower:
            topic_hits.append(clean_topic)

    total_hits = len(name_hits) + len(topic_hits)

    if total_hits >= 3 or (len(name_words) > 0 and len(name_hits) >= len(name_words) * 0.6):
        notes.append(f"Course content matches: Found {len(name_hits)} subject keyword matches and {len(topic_hits)} syllabus topic matches.")
        return 0.85, ConsistencyStatus.CONSISTENT.value, " ".join(notes)
    elif total_hits >= 1:
        notes.append(f"Moderate content overlap: Found {total_hits} related keywords or topics.")
        return 0.5, ConsistencyStatus.UNCERTAIN.value, " ".join(notes)
    else:
        notes.append("Low content overlap: Extracted text does not contain representative course topics or titles.")
        return 0.25, ConsistencyStatus.UNCERTAIN.value, " ".join(notes)


def check_for_duplicates(db: Session, file_hash: str) -> Tuple[bool, Optional[int], Optional[int], str]:
    """
    Checks if a file with this hash already exists in production documents or previous submissions.
    Returns: (is_duplicate, duplicate_of_doc_id, duplicate_of_sub_id, message)
    """
    existing_doc = db.query(Document).filter(Document.document_hash == file_hash).first()
    existing_sub = db.query(PaperSubmission).filter(PaperSubmission.file_hash == file_hash).first()

    if existing_doc:
        sub_id = existing_sub.id if existing_sub else None
        return True, existing_doc.id, sub_id, f"Duplicate paper: already exists in production corpus as Document #{existing_doc.id} ({existing_doc.title or 'Untitled'})."

    if existing_sub:
        return True, None, existing_sub.id, f"Duplicate submission: already submitted on {existing_sub.created_at.strftime('%Y-%m-%d')} with status '{existing_sub.status}' (Submission #{existing_sub.id})."

    return False, None, None, "File is unique (no duplicates detected)."
