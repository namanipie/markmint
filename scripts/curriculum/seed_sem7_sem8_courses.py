"""
Database Seeder for Semesters 7 & 8 Core & Professional Elective Courses:
- Course 38: Internet of Things (SEM7-IOT / 21CSC401T) - Semester 7
- Course 39: Digital Image Processing (SEM7-DIP / 21CSC402T) - Semester 7
- Course 40: Security Governance, Risk and Compliance (SEM7-GRC / 21CSS401T) - Semester 7
- Course 41: Security Risk Management and Principles (SEM7-SRMP / 21CSC403T) - Semester 7
- Course 42: Information Security (SEM7-IS / 21CSC404T) - Semester 7
- Course 43: Digital Signal Processing (SEM8-DSP / 21ECC302J) - Semester 8
"""

import os
import sys
import argparse
from typing import Dict, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models.core import Course, Syllabus, Unit, Topic, Concept, CurriculumMapping
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
from scripts.curriculum.taxonomies.sem7_sem8_taxonomy import COURSES_TAXONOMY

def seed_database(db: Session) -> Dict[str, Any]:
    stats = {
        "courses_created": 0,
        "courses_updated": 0,
        "syllabuses_created": 0,
        "units_created": 0,
        "topics_created": 0,
        "concepts_created": 0,
        "assessment_plans_created": 0,
        "mappings_promoted": 0
    }

    for cdata in COURSES_TAXONOMY:
        cid = cdata["id"]
        course = db.query(Course).filter(Course.id == cid).first()
        if not course:
            course = db.query(Course).filter(Course.code == cdata["code"]).first()
        if not course:
            course = db.query(Course).filter(Course.canonical_code == cdata["canonical_code"]).first()

        if not course:
            course = Course(
                id=cid,
                name=cdata["name"],
                code=cdata["code"],
                canonical_code=cdata["canonical_code"],
                regulation_year=cdata["regulation_year"],
                department=cdata["department"]
            )
            db.add(course)
            db.flush()
            stats["courses_created"] += 1
            print(f"[Course Created] ID {course.id}: {course.name} ({course.canonical_code})")
        else:
            course.name = cdata["name"]
            course.code = cdata["code"]
            course.canonical_code = cdata["canonical_code"]
            course.regulation_year = cdata["regulation_year"]
            course.department = cdata["department"]
            db.flush()
            stats["courses_updated"] += 1
            print(f"[Course Updated] ID {course.id}: {course.name} ({course.canonical_code})")

        # Syllabus
        syllabus = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
        if not syllabus:
            syllabus = Syllabus(course_id=course.id, version="2021")
            db.add(syllabus)
            db.flush()
            stats["syllabuses_created"] += 1
            print(f"  [Syllabus Created] for {course.name}")

        # Units & Topics
        unit_map = {}
        for udata in cdata["units"]:
            unit = db.query(Unit).filter(
                Unit.syllabus_id == syllabus.id,
                Unit.number == udata["number"]
            ).first()
            if not unit:
                unit = Unit(
                    syllabus_id=syllabus.id,
                    number=udata["number"],
                    name=udata["name"]
                )
                db.add(unit)
                db.flush()
                stats["units_created"] += 1
                print(f"  [Unit Created] Unit {unit.number}: {unit.name} (id={unit.id})")
            else:
                unit.name = udata["name"]
                db.flush()
            unit_map[unit.number] = unit

            # Topics and Concepts
            for t_name in udata["topics"]:
                topic = db.query(Topic).filter(
                    Topic.unit_id == unit.id,
                    Topic.name == t_name
                ).first()
                if not topic:
                    topic = Topic(
                        unit_id=unit.id,
                        name=t_name
                    )
                    db.add(topic)
                    db.flush()
                    stats["topics_created"] += 1

                # Concept
                concept = db.query(Concept).filter(Concept.canonical_name == t_name).first()
                if not concept:
                    concept = Concept(
                        canonical_name=t_name,
                        unit_id=unit.id
                    )
                    db.add(concept)
                    db.flush()
                    stats["concepts_created"] += 1

        # Assessment Plan
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
            endsem = AssessmentComponent(
                plan_id=plan.id,
                course_id=course.id,
                code="ENDSEM",
                canonical_label="End Semester Examination",
                student_label="End Semester",
                role="SUMMATIVE_EXAM",
                sequence=3,
                marks=100.0,
                raw_labels=["END_SEM", "ENDSEM", "End Semester", "Semester Exam", "DEGREE EXAMINATION"]
            )
            db.add_all([cla1, cla2, endsem])
            db.flush()

            # Scope Coverage: CLA1 (Units 1-2), CLA2 (Units 3-5), EndSem (Units 1-5)
            db.add(AssessmentCoverage(assessment_component_id=cla1.id, unit_id=unit_map[1].id, coverage_type="IN_SCOPE"))
            db.add(AssessmentCoverage(assessment_component_id=cla1.id, unit_id=unit_map[2].id, coverage_type="IN_SCOPE"))
            db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_map[3].id, coverage_type="IN_SCOPE"))
            db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_map[4].id, coverage_type="IN_SCOPE"))
            db.add(AssessmentCoverage(assessment_component_id=cla2.id, unit_id=unit_map[5].id, coverage_type="IN_SCOPE"))
            for unum in range(1, 6):
                db.add(AssessmentCoverage(assessment_component_id=endsem.id, unit_id=unit_map[unum].id, coverage_type="IN_SCOPE"))
            db.flush()
            stats["assessment_plans_created"] += 1
            print(f"  [Assessment Plan Created] for {course.name}")

        # Promote Curriculum Mappings
        mappings = db.query(CurriculumMapping).filter(
            CurriculumMapping.semester == cdata["semester"],
            CurriculumMapping.status == "UNMATCHED"
        ).all()
        promoted_for_course = 0
        for m in mappings:
            if cdata["curriculum_filter"](m.subject_name):
                m.course_id = course.id
                m.status = "MATCHED"
                promoted_for_course += 1
                stats["mappings_promoted"] += 1
        db.flush()
        print(f"  [Curriculum Mappings Promoted] {promoted_for_course} branch subjects linked to {course.name}")

    db.commit()
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
    parser = argparse.ArgumentParser(description="Seed Semesters 7 and 8 Courses")
    parser.add_argument("--db-url", type=str, default=None)
    parser.add_argument("--sqlite-path", type=str, default=None)
    parser.add_argument("--use-env", action="store_true")
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
        test_db = os.path.join(
            "C:\\Users\\ASUS\\.gemini\\antigravity\\brain\\70daf3e1-493b-412c-ae3f-f59f589f02db\\scratch",
            "isolated_test_corpus.db"
        )
        db_url = f"sqlite:///{test_db}"

    print(f"Connecting to database: {mask_url(db_url)}")
    engine = create_engine(db_url)
    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()

    try:
        stats = seed_database(session)
        print("\n" + "=" * 50)
        print("SEEDING COMPLETE:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print("=" * 50)
    finally:
        session.close()

if __name__ == "__main__":
    main()
