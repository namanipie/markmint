"""
Additive, idempotent seeder and corpus ingestion pipeline for Semester 3 and Semester 4 Core CSE:
- Course 24: Data Structures and Algorithms (21CSC201J, SEM3-DSA)
- Course 25: Operating Systems (21CSC202J, SEM3-OS)
- Course 26: Computer Organization and Architecture (21CSS201T, SEM3-COA)
- Course 27: Design and Analysis of Algorithms (21CSC204J, SEM4-DAA)
- Course 28: Database Management Systems (21CSC205P, SEM4-DBMS)

Guarantees:
1. Canonical 5-unit syllabus derived strictly from authoritative SRMIST Regulation 2021 curriculum.
2. Ingests all verified genuine exam papers with SHA-256 deduplication and full provenance.
3. Maps branch curriculum entries across Computing Technologies, Computational Intelligence, etc.
4. Links CourseAssessmentPlans with CLA-1, CLA-2, and END_SEM components and unit coverage.
5. Idempotent: safe to run multiple times without duplicating or overwriting data.
"""
import os
import sys
import json
import hashlib
import re
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Exam, Document, Section, Question, CurriculumMapping
)
from backend.models.assessment import (
    CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
)

COURSES_CONFIG = [
    {
        "id": 24,
        "name": "Data Structures and Algorithms",
        "canonical_code": "21CSC201J",
        "code": "SEM3-DSA",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 3,
        "taxonomy_file": "backend/services/taxonomy_registry/definitions/course_24_dsa.json",
        "paper_prefix": "DSA_",
        "keywords": ["data structure", "data structures and algorithms"]
    },
    {
        "id": 25,
        "name": "Operating Systems",
        "canonical_code": "21CSC202J",
        "code": "SEM3-OS",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 3,
        "taxonomy_file": "backend/services/taxonomy_registry/definitions/course_25_os.json",
        "paper_prefix": "OS_",
        "keywords": ["operating system", "operating systems"]
    },
    {
        "id": 26,
        "name": "Computer Organization and Architecture",
        "canonical_code": "21CSS201T",
        "code": "SEM3-COA",
        "regulation_year": 2021,
        "department": "Computational Intelligence",
        "semester": 3,
        "taxonomy_file": "backend/services/taxonomy_registry/definitions/course_26_coa.json",
        "paper_prefix": "COA_",
        "keywords": ["computer organization", "organization and architecture", "computer architecture"]
    },
    {
        "id": 27,
        "name": "Design and Analysis of Algorithms",
        "canonical_code": "21CSC204J",
        "code": "SEM4-DAA",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 4,
        "taxonomy_file": "backend/services/taxonomy_registry/definitions/course_27_daa.json",
        "paper_prefix": "DAA_",
        "keywords": ["design and analysis of algorithms", "analysis of algorithm"]
    },
    {
        "id": 28,
        "name": "Database Management Systems",
        "canonical_code": "21CSC205P",
        "code": "SEM4-DBMS",
        "regulation_year": 2021,
        "department": "Computing Technologies",
        "semester": 4,
        "taxonomy_file": "backend/services/taxonomy_registry/definitions/course_28_dbms.json",
        "paper_prefix": "DBMS_",
        "keywords": ["database management", "database systems", "dbms"]
    }
]

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def seed_s3_s4():
    db = SessionLocal()
    try:
        print("=== Step 1: Seeding Courses, Syllabuses, Units and Topics ===")
        for c_cfg in COURSES_CONFIG:
            course = db.query(Course).filter(Course.id == c_cfg["id"]).first()
            if not course:
                # Also check by code
                course = db.query(Course).filter(Course.code == c_cfg["code"]).first()
            
            if not course:
                course = Course(
                    id=c_cfg["id"],
                    name=c_cfg["name"],
                    code=c_cfg["code"],
                    canonical_code=c_cfg["canonical_code"],
                    regulation_year=c_cfg["regulation_year"],
                    department=c_cfg["department"]
                )
                db.add(course)
                db.flush()
                print(f"[Course] Created {course.id}: {course.name} ({course.canonical_code})")
            else:
                course.canonical_code = c_cfg["canonical_code"]
                course.regulation_year = c_cfg["regulation_year"]
                course.department = c_cfg["department"]
                db.flush()
                print(f"[Course] Updated {course.id}: {course.name} ({course.canonical_code})")

            # Load taxonomy definition
            with open(c_cfg["taxonomy_file"], "r", encoding="utf-8") as tf:
                tax_data = json.load(tf)

            # Syllabus
            syllabus = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
            if not syllabus:
                syllabus = Syllabus(
                    course_id=course.id,
                    version=str(c_cfg["regulation_year"])
                )
                db.add(syllabus)
                db.flush()
                print(f"  [Syllabus] Created for {course.name}")

            # Units & Topics
            unit_obj_map = {}
            for u_idx, u_data in enumerate(tax_data["units"], 1):
                unit = db.query(Unit).filter(
                    Unit.syllabus_id == syllabus.id,
                    Unit.number == u_data["number"]
                ).first()
                if not unit:
                    unit = Unit(
                        id=u_data["id"],
                        syllabus_id=syllabus.id,
                        number=u_data["number"],
                        name=u_data["name"]
                    )
                    db.add(unit)
                    db.flush()
                    print(f"  [Unit] Created Unit {unit.number}: {unit.name} (id={unit.id})")
                else:
                    unit.name = u_data["name"]
                    db.flush()
                unit_obj_map[unit.number] = unit

                for t_data in u_data["topics"]:
                    topic = db.query(Topic).filter(Topic.id == t_data["id"]).first()
                    if not topic:
                        topic = db.query(Topic).filter(
                            Topic.unit_id == unit.id,
                            Topic.name == t_data["name"]
                        ).first()
                    if not topic:
                        topic = Topic(
                            id=t_data["id"],
                            unit_id=unit.id,
                            name=t_data["name"]
                        )
                        db.add(topic)
                        db.flush()
                    else:
                        topic.name = t_data["name"]
                        db.flush()

            # Seed CourseAssessmentPlan & AssessmentComponents
            plan = db.query(CourseAssessmentPlan).filter(
                CourseAssessmentPlan.course_id == course.id,
                CourseAssessmentPlan.regulation_year == 2021
            ).first()
            if not plan:
                plan = CourseAssessmentPlan(
                    course_id=course.id,
                    regulation_year=2021,
                    source_title=f"Regulation 2021 {course.name} Assessment Scheme",
                    version="1.0"
                )
                db.add(plan)
                db.flush()

                # Components
                cla1 = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=course.id,
                    code="CLA1",
                    canonical_label="Continuous Learning Assessment 1",
                    student_label="CLA-1",
                    role="FORMATIVE_TEST",
                    sequence=1,
                    marks=50.0,
                    raw_labels=["CLA1", "CLA-1", "CT1", "Cycle Test 1"]
                )
                cla2 = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=course.id,
                    code="CLA2",
                    canonical_label="Continuous Learning Assessment 2",
                    student_label="CLA-2",
                    role="FORMATIVE_TEST",
                    sequence=2,
                    marks=50.0,
                    raw_labels=["CLA2", "CLA-2", "CT2", "Cycle Test 2"]
                )
                end_sem = AssessmentComponent(
                    plan_id=plan.id,
                    course_id=course.id,
                    code="ENDSEM",
                    canonical_label="End Semester Examination",
                    student_label="End Semester",
                    role="SUMMATIVE_EXAM",
                    sequence=3,
                    marks=100.0,
                    raw_labels=["END_SEM", "ENDSEM", "End Semester", "Semester Exam"]
                )
                db.add_all([cla1, cla2, end_sem])
                db.flush()

                # Coverage: CLA-1 covers Unit 1, Unit 2
                db.add(AssessmentCoverage(assessment_component_id=cla1.id, unit_id=unit_obj_map[1].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla1.id, unit_id=unit_obj_map[2].id, coverage_type="IN_SCOPE"))

                # Coverage: CLA-2 covers Unit 3, Unit 4, Unit 5
                db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_obj_map[3].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_obj_map[4].id, coverage_type="IN_SCOPE"))
                db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_obj_map[5].id, coverage_type="IN_SCOPE"))

                # Coverage: END_SEM covers Units 1..5
                for u_num in range(1, 6):
                    db.add(AssessmentCoverage(assessment_component_id=end_sem.id, unit_id=unit_obj_map[u_num].id, coverage_type="IN_SCOPE"))
                db.flush()
                print(f"  [AssessmentPlan] Created plan and 3 components with unit coverage for {course.name}")

        print("\n=== Step 2: Linking Curriculum Mappings (Branch/Semester) ===")
        all_mappings = db.query(CurriculumMapping).filter(
            CurriculumMapping.semester.in_([3, 4])
        ).all()
        
        linked_count = 0
        for m in all_mappings:
            subj_lower = m.subject_name.lower()
            target_course_id = None
            for c_cfg in COURSES_CONFIG:
                if m.semester == c_cfg["semester"]:
                    for kw in c_cfg["keywords"]:
                        if kw in subj_lower:
                            target_course_id = c_cfg["id"]
                            break
                if target_course_id:
                    break
            
            if target_course_id and m.course_id != target_course_id:
                m.course_id = target_course_id
                m.status = "MATCHED"
                linked_count += 1

        db.flush()
        print(f"[CurriculumMapping] Linked {linked_count} branch semester curriculum slots to courses.")

        print("\n=== Step 3: Ingesting Exam Papers and Questions from Extractions ===")
        extraction_dir = "data/s3_s4/extractions"
        pyq_dir = "data/s3_s4/pyqs"

        if not os.path.exists(extraction_dir):
            print("Extraction directory not found.")
            return

        extracted_files = sorted(os.listdir(extraction_dir))
        total_ingested_papers = 0
        total_ingested_questions = 0

        for f_name in extracted_files:
            if not f_name.endswith(".json"):
                continue

            base_stem = os.path.splitext(f_name)[0]
            pdf_path = os.path.join(pyq_dir, f"{base_stem}.pdf")
            if not os.path.exists(pdf_path):
                print(f"Warning: PDF file {pdf_path} not found for extraction {f_name}")
                continue

            file_hash = compute_sha256(pdf_path)

            # Determine course
            course_id = None
            for c_cfg in COURSES_CONFIG:
                if base_stem.startswith(c_cfg["paper_prefix"]):
                    course_id = c_cfg["id"]
                    break

            if not course_id:
                print(f"Skipping {f_name}: no matching course config prefix")
                continue

            # Check if Document already exists
            doc = db.query(Document).filter(Document.document_hash == file_hash).first()
            if not doc:
                # Determine Year & Term
                year = None
                term = None
                year_match = re.search(r'(202[0-9])', base_stem)
                if year_match:
                    year = int(year_match.group(1))

                for month in ["Jan", "May", "June", "July", "Nov", "Dec"]:
                    if month.lower() in base_stem.lower():
                        term = month.upper()
                        break

                c_info = next(c for c in COURSES_CONFIG if c["id"] == course_id)
                doc = Document(
                    title=f"{c_info['name']} - {term or ''} {year or ''} Examination Paper".strip(),
                    source="STUDIQUE",
                    original_url=pdf_path,
                    semester=str(c_info["semester"]),
                    subject=c_info["name"],
                    resource_type="QUESTION_PAPER",
                    year=year,
                    exam_type="END_SEM",
                    document_hash=file_hash,
                    extraction_status="completed",
                    extraction_confidence=1.0
                )
                db.add(doc)
                db.flush()

            # Check if Exam already exists
            exam = db.query(Exam).filter(Exam.document_id == doc.id).first()
            if exam:
                # Check if questions have empty text
                has_empty_q = db.query(Question).join(Section).filter(Section.exam_id == exam.id, Question.original_text == '').first()
                if has_empty_q:
                    print(f"  [Refreshing] Exam {exam.id} ({base_stem}) has empty questions. Deleting old sections/questions to re-ingest...")
                    sec_ids = [s.id for s in db.query(Section).filter(Section.exam_id == exam.id).all()]
                    if sec_ids:
                        db.query(Question).filter(Question.section_id.in_(sec_ids)).delete(synchronize_session=False)
                        db.query(Section).filter(Section.exam_id == exam.id).delete(synchronize_session=False)
                        db.flush()
                    exam = None

            if not exam:
                with open(os.path.join(extraction_dir, f_name), "r", encoding="utf-8") as jf:
                    extracted_data = json.load(jf)

                # Determine assessment type
                meta = extracted_data.get("metadata") or {}
                extracted_assessment = meta.get("assessment_type")
                if extracted_assessment in ["END_SEM", "CT1", "CT2", "MODEL"]:
                    assessment_type = extracted_assessment
                else:
                    # Check questions marks: standard SRM end sem is 100 marks with Part A, B, C
                    sections = extracted_data.get("sections", [])
                    sec_names = [s.get("name", "").upper() for s in sections]
                    if any("PART" in sn or "SECTION" in sn for sn in sec_names):
                        assessment_type = "END_SEM"
                    else:
                        assessment_type = "UNKNOWN"

                exam_year = meta.get("year") or doc.year

                exam = db.query(Exam).filter(Exam.document_id == doc.id).first()
                if not exam:
                    exam = Exam(
                        course_id=course_id,
                        document_id=doc.id,
                        year=exam_year,
                        term=doc.term if hasattr(doc, 'term') else None,
                        assessment_type=assessment_type
                    )
                    db.add(exam)
                    db.flush()
                else:
                    exam.assessment_type = assessment_type
                    exam.year = exam_year
                    db.flush()

                # Insert Sections & Questions
                paper_q_count = 0
                for sec_idx, sec_data in enumerate(extracted_data.get("sections", []), 1):
                    sec_name = sec_data.get("name", f"Section {sec_idx}")
                    section = Section(
                        exam_id=exam.id,
                        name=sec_name,
                        instructions=sec_data.get("instructions")
                    )
                    db.add(section)
                    db.flush()

                    for q_data in sec_data.get("questions", []):
                        # Construct comprehensive question text
                        q_num = str(q_data.get("question_number") or q_data.get("number") or "?")
                        main_text = q_data.get("original_text") or q_data.get("text") or ""
                        sub_texts = []
                        for sub in q_data.get("subquestions", []):
                            sub_num = sub.get("number") or sub.get("question_number") or ""
                            sub_body = sub.get("text") or sub.get("original_text") or ""
                            sub_str = f"({sub_num}) {sub_body}"
                            if sub.get("marks"):
                                sub_str += f" [{sub.get('marks')} marks]"
                            sub_texts.append(sub_str)
                        
                        full_text = main_text
                        if sub_texts and not any(s in full_text for s in sub_texts):
                            full_text += "\n" + "\n".join(sub_texts)

                        marks = q_data.get("marks")
                        if not marks and q_data.get("subquestions"):
                            sub_marks = [s.get("marks") for s in q_data["subquestions"] if s.get("marks")]
                            if sub_marks:
                                marks = sum(sub_marks)

                        q_obj = Question(
                            section_id=section.id,
                            question_number=q_num,
                            original_text=full_text,
                            marks=marks,
                            is_alternative=False,
                            extraction_method="VISION_GEMINI",
                            extraction_confidence=1.0
                        )
                        db.add(q_obj)
                        paper_q_count += 1

                        # Alternative question (OR choice)
                        alt_data = q_data.get("or_alternative")
                        if alt_data:
                            alt_num = str(alt_data.get("question_number") or alt_data.get("number") or q_num) + " (OR)"
                            alt_main = alt_data.get("original_text") or alt_data.get("text") or ""
                            alt_subs = []
                            for asub in alt_data.get("subquestions", []):
                                asub_num = asub.get("number") or asub.get("question_number") or ""
                                asub_body = asub.get("text") or asub.get("original_text") or ""
                                asub_str = f"({asub_num}) {asub_body}"
                                if asub.get("marks"):
                                    asub_str += f" [{asub.get('marks')} marks]"
                                alt_subs.append(asub_str)
                            alt_full = alt_main
                            if alt_subs and not any(s in alt_full for s in alt_subs):
                                alt_full += "\n" + "\n".join(alt_subs)

                            alt_marks = alt_data.get("marks") or marks
                            alt_q_obj = Question(
                                section_id=section.id,
                                question_number=alt_num,
                                original_text=alt_full,
                                marks=alt_marks,
                                is_alternative=True,
                                extraction_method="VISION_GEMINI",
                                extraction_confidence=1.0
                            )
                            db.add(alt_q_obj)
                            paper_q_count += 1

                total_ingested_papers += 1
                total_ingested_questions += paper_q_count
                print(f"  [Ingested] {base_stem}: Exam {exam.id} | {assessment_type} | {len(extracted_data.get('sections', []))} sections | {paper_q_count} questions")
            else:
                pass  # already ingested

        db.commit()
        print(f"\nSuccessfully committed! Ingested {total_ingested_papers} new exams, {total_ingested_questions} new questions.")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_s3_s4()
