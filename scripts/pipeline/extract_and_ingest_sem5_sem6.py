"""
End-to-End Question Extraction, Database Ingestion, and Topic Classification Pipeline
for MarkMint Semesters 5 & 6:
- Course 32: Discrete Mathematics (SEM5-DM / 21MAB301T)
- Course 33: Formal Languages and Automata (SEM5-FLA / 21CSC301T)
- Course 34: Computer Networks (SEM5-CN / 21CSC302J)
- Course 35: Software Engineering and Project Management (SEM6-SEPM / 21CSC303J)
- Course 36: Compiler Design (SEM6-CD / 21CSC305J)
- Course 37: Data Science (SEM6-DS / 21CSC304P)

Features:
1. Renders PDF exam papers with pymupdf and extracts structured questions via gemini-3.5-flash-lite.
2. Caches extractions in data/sem5_sem6/extractions/ for instant idempotent replay.
3. Ingests Documents, Exams, Sections, and Questions with full provenance.
4. Classifies each question to authoritative syllabus topics with regex rule heuristics.
5. Populates question_topic and groups question families with canonical naming.
"""

import os
import sys
import re
import json
import hashlib
import argparse
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pymupdf
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Document, Exam, Section, Question, 
    QuestionFamily, QuestionFamilyMembership, question_topic
)
from scripts.curriculum.taxonomies.sem5_sem6_taxonomy import COURSES_TAXONOMY, TOPIC_CLASSIFICATION_RULES

EXTRACTIONS_CACHE_DIR = os.path.join(BASE_DIR, "data", "sem5_sem6", "extractions")
os.makedirs(EXTRACTIONS_CACHE_DIR, exist_ok=True)

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_year_term_from_filename(filename: str) -> tuple[int, str]:
    # e.g. "Computer Networks - PYQ 2024 May.pdf" or "Discrete Mathematics - PYQ 2024 Jan.pdf"
    year_match = re.search(r"202[0-9]", filename)
    year = int(year_match.group(0)) if year_match else 2024

    term = "END_SEM"
    lower = filename.lower()
    if "jan" in lower:
        term = "JAN"
    elif "may" in lower:
        term = "MAY"
    elif "june" in lower or "jun" in lower:
        term = "JUNE"
    elif "july" in lower or "jul" in lower:
        term = "JULY"
    elif "nov" in lower:
        term = "NOV"
    elif "dec" in lower:
        term = "DEC"
    elif "ct1" in lower or "cycle test 1" in lower:
        term = "CT1"
    elif "ct2" in lower or "cycle test 2" in lower:
        term = "CT2"

    return year, term

def extract_pdf_with_gemini(pdf_path: str, client: genai.Client) -> List[Dict[str, Any]]:
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    cache_file = os.path.join(EXTRACTIONS_CACHE_DIR, f"{stem}.json")

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"    [CACHE HIT] Loaded {len(data)} questions from {os.path.basename(cache_file)}")
                    return data
        except Exception as e:
            print(f"    [WARN] Cache corrupted, re-extracting: {e}")

    print(f"    [EXTRACTING] Processing with Gemini Vision: {os.path.basename(pdf_path)}...")
    doc = pymupdf.open(pdf_path)
    extracted_questions = []

    prompt = """Extract all examination questions from this page image into a JSON array of objects.
Each object must have the following keys:
- "number": string (e.g. "1", "2", "11a", "11b", "12a", "12b")
- "text": string (complete question text including mathematical expressions or multiple choice options)
- "marks": float or null (allocated marks)
- "is_or_choice": boolean (true if marked as OR choice / alternative question)
- "section": string ("PART - A", "PART - B", or "PART - C")
"""

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")

        try:
            res = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    prompt
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            items = json.loads(res.text)
            if isinstance(items, list):
                for item in items:
                    item["page"] = page_idx + 1
                    extracted_questions.append(item)
                print(f"      Page {page_idx + 1}/{len(doc)}: extracted {len(items)} questions")
        except Exception as e:
            print(f"      [ERROR] Page {page_idx + 1} extraction failed: {e}")

    doc.close()

    if extracted_questions:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(extracted_questions, f, indent=2)
        print(f"    [SAVED CACHE] {len(extracted_questions)} questions cached in {os.path.basename(cache_file)}")

    return extracted_questions

def classify_question_to_topic(course_id: int, q_text: str, topic_lookup: Dict[str, int]) -> Optional[int]:
    rules = TOPIC_CLASSIFICATION_RULES.get(course_id, [])
    lower_text = q_text.lower()

    for unit_num, topic_name, patterns in rules:
        for pat in patterns:
            if re.search(pat, lower_text):
                topic_id = topic_lookup.get(topic_name)
                if topic_id:
                    return topic_id
    return None

def ingest_course_papers(db: Session, course_data: Dict[str, Any], client: genai.Client) -> Dict[str, int]:
    course_id = course_data["id"]
    course_name = course_data["name"]
    sem = course_data["semester"]

    papers_dir = os.path.join(BASE_DIR, "corpus", f"Semester_{sem}", course_name, "EXAMINATION_PAPERS")
    if not os.path.exists(papers_dir):
        print(f"No papers directory found for Course {course_id} at {papers_dir}")
        return {"papers": 0, "questions": 0, "mapped": 0}

    pdf_files = [f for f in os.listdir(papers_dir) if f.lower().endswith(".pdf")]
    print(f"\n=======================================================")
    print(f"Ingesting Course {course_id}: {course_name} ({len(pdf_files)} PDF papers)")
    print(f"=======================================================")

    # Build topic lookup {topic_name: topic_id}
    topics = (
        db.query(Topic)
        .join(Unit, Topic.unit_id == Unit.id)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == course_id)
        .all()
    )
    topic_lookup = {t.name: t.id for t in topics}

    stats = {"papers": 0, "questions": 0, "mapped": 0, "families": 0}

    for pdf_name in pdf_files:
        pdf_path = os.path.join(papers_dir, pdf_name)
        file_hash = compute_sha256(pdf_path)
        year, term = parse_year_term_from_filename(pdf_name)

        # 1. Document
        doc = db.query(Document).filter(Document.document_hash == file_hash).first()
        if not doc:
            doc = Document(
                source="studique_curated",
                title=f"{course_name} - {term} {year}",
                semester=str(sem),
                subject=course_name,
                year=year,
                exam_type=term,
                document_hash=file_hash,
                resource_type="exam_paper",
                processing_status="completed",
                extraction_status="completed",
                extraction_confidence=1.0
            )
            db.add(doc)
            db.flush()

        # 2. Exam
        exam = db.query(Exam).filter(Exam.document_id == doc.id).first()
        if not exam:
            exam = db.query(Exam).filter(
                Exam.course_id == course_id,
                Exam.year == year,
                Exam.term == term
            ).first()

        if not exam:
            exam = Exam(
                course_id=course_id,
                document_id=doc.id,
                year=year,
                term=term,
                assessment_type="ENDSEM"
            )
            db.add(exam)
            db.flush()

        stats["papers"] += 1

        # Check existing questions
        existing_q_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .filter(Section.exam_id == exam.id)
            .count()
        )

        if existing_q_count > 0:
            print(f"  [EXAM EXISTS] {pdf_name}: Exam {exam.id} already has {existing_q_count} questions.")
            continue

        # Extract questions
        raw_items = extract_pdf_with_gemini(pdf_path, client)
        if not raw_items:
            print(f"  [WARN] No questions extracted from {pdf_name}")
            continue

        # Create sections
        sections_map = {}
        for item in raw_items:
            sec_name = (item.get("section") or "PART - A").upper().strip()
            if "PART - B" in sec_name or "SECTION B" in sec_name:
                sec_name = "PART - B"
            elif "PART - C" in sec_name or "SECTION C" in sec_name:
                sec_name = "PART - C"
            else:
                sec_name = "PART - A"

            if sec_name not in sections_map:
                section = db.query(Section).filter(
                    Section.exam_id == exam.id,
                    Section.name == sec_name
                ).first()
                if not section:
                    section = Section(exam_id=exam.id, name=sec_name)
                    db.add(section)
                    db.flush()
                sections_map[sec_name] = section

            target_section = sections_map[sec_name]
            q_num = str(item.get("number", "?")).strip(".")
            q_text = (item.get("text") or "").strip()
            if not q_text:
                continue

            marks = None
            raw_marks = item.get("marks")
            if raw_marks is not None:
                try:
                    marks = float(raw_marks)
                except (ValueError, TypeError):
                    marks = None

            is_alt = bool(item.get("is_or_choice", False))

            q_obj = Question(
                section_id=target_section.id,
                question_number=q_num,
                original_text=q_text,
                marks=marks,
                is_alternative=is_alt,
                extraction_method="VISION_GEMINI",
                extraction_confidence=1.0
            )
            db.add(q_obj)
            db.flush()
            stats["questions"] += 1

            # Topic classification
            mapped_topic_id = classify_question_to_topic(course_id, q_text, topic_lookup)
            if mapped_topic_id:
                # Insert into question_topic
                stmt = question_topic.insert().values(
                    question_id=q_obj.id,
                    topic_id=mapped_topic_id
                )
                db.execute(stmt)
                stats["mapped"] += 1

            # Create or link QuestionFamily
            # For exact or canonical repetition
            first_words = " ".join(q_text.split()[:8])
            canonical_fam_name = f"Family: {first_words}"
            fam = db.query(QuestionFamily).filter(
                QuestionFamily.subject == course_name,
                QuestionFamily.canonical_name == canonical_fam_name
            ).first()
            if not fam:
                fam = QuestionFamily(
                    subject=course_name,
                    canonical_name=canonical_fam_name,
                    first_seen_year=year,
                    latest_seen_year=year,
                    repetition_type="singleton"
                )
                db.add(fam)
                db.flush()
                stats["families"] += 1
            else:
                fam.repetition_type = "exact_repeat"
                if year and fam.latest_seen_year and year > fam.latest_seen_year:
                    fam.latest_seen_year = year
                db.flush()

            q_obj.family_id = fam.id
            db.flush()

            # Add member
            mem = QuestionFamilyMembership(
                family_id=fam.id,
                question_id=q_obj.id,
                similarity_score=1.0,
                match_type="EXACT" if fam.repetition_type == "exact_repeat" else "CANONICAL",
                decision_method="rule_heuristic",
                algorithm_version="v2.0"
            )
            db.add(mem)

        db.commit()
        print(f"  [INGESTED] {pdf_name}: Exam {exam.id} | {year} {term} | {len(raw_items)} questions ingested.")

    return stats

def mask_url(url: str) -> str:
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        return url
    except Exception:
        return "<DATABASE_URL masked>"

def normalize_target_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if "sslmode=" not in url and "?" in url:
        url = f"{url}&sslmode=require"
    elif "sslmode=" not in url and not url.startswith("sqlite"):
        url = f"{url}?sslmode=require"
    return url

def main():
    parser = argparse.ArgumentParser(description="Extract and Ingest Semesters 5 and 6 Examination Papers")
    parser.add_argument("--db-url", type=str, default=None)
    parser.add_argument("--sqlite-path", type=str, default=None)
    parser.add_argument("--use-env", action="store_true", help="Use DATABASE_URL from environment / .env")
    args = parser.parse_args()

    if args.use_env:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        env_url = os.environ.get("DATABASE_URL")
        if not env_url:
            raise ValueError("DATABASE_URL not found in environment or .env")
        db_url = normalize_target_url(env_url)
    elif args.sqlite_path:
        db_url = f"sqlite:///{os.path.abspath(args.sqlite_path)}"
    elif args.db_url:
        db_url = normalize_target_url(args.db_url)
    else:
        test_db = "C:/Users/ASUS/.gemini/antigravity/brain/70daf3e1-493b-412c-ae3f-f59f589f02db/scratch/isolated_test_corpus.db"
        db_url = f"sqlite:///{test_db}"

    print(f"Connecting to database: {mask_url(db_url)}")
    engine = create_engine(db_url)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()

    client = genai.Client()

    overall_stats = {"papers": 0, "questions": 0, "mapped": 0, "families": 0}
    try:
        for cdata in COURSES_TAXONOMY:
            stats = ingest_course_papers(session, cdata, client)
            for k in overall_stats:
                overall_stats[k] += stats.get(k, 0)

        print("\n" + "=" * 60)
        print("EXTRACTION & INGESTION COMPLETED SUCCESSFULLY:")
        for k, v in overall_stats.items():
            print(f"  Total {k}: {v}")
        print("=" * 60)
    finally:
        session.close()

if __name__ == "__main__":
    main()
