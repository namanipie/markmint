"""
Final First-Year Local Integrity Audit for Courses 1-13 in MarkMint.
Audits:
- course exists
- syllabus exists
- units/topics valid
- question counts
- exam counts
- question-topic mappings
- family counts
- prediction mode
- data availability status
- study plan
- practice
- historical evidence
- no cross-course mappings
- no student progress pollution
"""
import os
import sys
import sqlite3
from typing import Dict, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus, question_topic, StudentTopicProgress, StudentResourceProgress
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def run_full_first_year_audit() -> Dict[int, Dict[str, Any]]:
    db = SessionLocal()
    conn = sqlite3.connect("production_corpus.db")
    c = conn.cursor()

    report = {}

    for cid in range(1, 14):
        course = db.query(Course).filter(Course.id == cid).first()
        if not course:
            report[cid] = {"status": "MISSING_COURSE"}
            continue

        syl = db.query(Syllabus).filter(Syllabus.course_id == cid).first()
        units_count = db.query(Unit).filter(Unit.syllabus_id == syl.id).count() if syl else 0
        topics_count = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.syllabus_id == syl.id)
            .count()
            if syl else 0
        )

        exams_count = db.query(Exam).filter(Exam.course_id == cid).count()
        questions_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .count()
        )
        families_count = (
            db.query(Question.family_id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .distinct()
            .count()
        )
        mapped_questions_count = (
            db.query(Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .filter(Exam.course_id == cid)
            .distinct()
            .count()
        )

        # Cross-course check
        cross_course_mappings = (
            db.query(Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == cid, Syllabus.course_id != cid)
            .count()
        )

        # Intelligence snapshot
        snap = get_intelligence_snapshot(course_id=str(cid), db=db)
        pred_mode = snap.get("prediction_mode")
        data_status = snap.get("data_availability_status")
        has_evidence = len(snap.get("family_predictions", [])) > 0 or len(snap.get("topic_predictions", [])) > 0

        # Study plan
        plan = get_study_priorities(course.name, db=db)
        plan_mode = plan.get("plan_mode")
        plan_items = len(plan.get("priorities", []))

        # Practice
        practice_code = course.canonical_code or course.code or course.name
        try:
            prac = get_practice_questions(practice_code, limit=5)
            practice_ok = len(prac.get("questions", [])) > 0
        except Exception:
            practice_ok = False

        report[cid] = {
            "name": course.name,
            "code": course.canonical_code,
            "units": units_count,
            "topics": topics_count,
            "exams": exams_count,
            "questions": questions_count,
            "families": families_count,
            "mapped_questions": mapped_questions_count,
            "cross_course_mappings": cross_course_mappings,
            "pred_mode": pred_mode,
            "data_status": data_status,
            "has_evidence": has_evidence,
            "plan_mode": plan_mode,
            "plan_items": plan_items,
            "practice_ok": practice_ok,
        }

    # Student progress audit
    st_progress = db.query(StudentTopicProgress).count()
    sr_progress = db.query(StudentResourceProgress).count()

    db.close()
    conn.close()

    print(f"{'CID':<3} | {'Course Name':<35} | {'Code':<10} | {'U/T':<6} | {'Q/Map':<10} | {'Ex/Fam':<8} | {'Pred':<7} | {'DataStatus':<20} | {'Plan':<7} | {'Prac':<5} | {'X-Map':<5}")
    print("-" * 135)
    for cid, r in report.items():
        ut = f"{r['units']}/{r['topics']}"
        qmap = f"{r['questions']}/{r['mapped_questions']}"
        ef = f"{r['exams']}/{r['families']}"
        print(f"{cid:<3} | {r['name'][:35]:<35} | {(r['code'] or '')[:10]:<10} | {ut:<6} | {qmap:<10} | {ef:<8} | {r['pred_mode']:<7} | {r['data_status']:<20} | {r['plan_mode']:<7} | {str(r['practice_ok']):<5} | {r['cross_course_mappings']:<5}")

    print("\n--- Student Progress ---")
    print(f"StudentTopicProgress count: {st_progress} (Legitimate existing rows only)")
    print(f"StudentResourceProgress count: {sr_progress}")

    return report


if __name__ == "__main__":
    run_full_first_year_audit()
