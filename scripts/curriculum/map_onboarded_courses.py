"""
Deterministic, additive Question-to-Topic mapping for newly onboarded courses:
- Course 19: EM Physics (21PYB101J)
- Course 20: Physics Mechanics (21PYB104J)
- Course 8:  Foreign Languages (German, French, Spanish, Japanese, Korean, Chinese)

INVARIANTS:
1. Strict syllabus authority via TaxonomyRegistry.
2. For Course 8, candidate topic rules are strictly scoped to Exam.track_id (zero cross-track leakage).
3. Legacy regulation papers (e.g. Exam 248 for Course 19) are strictly excluded from 2021 mapping.
4. Only HIGH and MEDIUM confidence proposals are committed to question_topic.
5. AMBIGUOUS and UNMAPPED questions are strictly preserved as unmapped.
6. Raw Exam.assessment_type is NEVER modified.
7. Existing mappings are preserved (additive only).
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.core.database import SessionLocal
from backend.models.core import Question, Exam, Section, Topic, Unit, Course, CourseTrack, question_topic
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_registry import get_taxonomy_registry


EXCLUDED_ASSESSMENT_TYPES = {
    "QUESTION_BANK",
    "STUDY_MATERIAL",
    "EMPTY_TEXT",
    "LEGACY_REGULATION"
}


def run_course_mapping(course_id: int, apply_changes: bool = False) -> Dict[str, Any]:
    db = SessionLocal()
    registry = get_taxonomy_registry()

    report = {
        "course_id": course_id,
        "apply_changes": apply_changes,
        "total_authentic_questions": 0,
        "previously_mapped": 0,
        "newly_mapped": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "ambiguous": 0,
        "unmapped": 0,
        "by_track": defaultdict(lambda: {"total": 0, "newly_mapped": 0, "high": 0, "medium": 0, "ambiguous": 0, "unmapped": 0}),
        "samples": []
    }

    try:
        # Load course and verify
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError(f"Course {course_id} not found in database.")

        # Query authentic exams for this course
        exam_query = db.query(Exam).filter(
            Exam.course_id == course_id,
            ~Exam.assessment_type.in_(EXCLUDED_ASSESSMENT_TYPES)
        )

        # For Course 19: Exclude Exam 248 (2018 legacy regulation 18PYB101J)
        if course_id == 19:
            exam_query = exam_query.filter(Exam.id != 248, Exam.year > 2018)

        exams = exam_query.all()
        exam_ids = [e.id for e in exams]

        # Fetch questions
        questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .filter(Section.exam_id.in_(exam_ids))
            .order_by(Question.id)
            .all()
        )
        report["total_authentic_questions"] = len(questions)

        # Existing mappings set
        existing_qt = set(
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .filter(question_topic.c.question_id.in_([q.id for q in questions]))
            .all()
        )
        mapped_qids = {q_id for q_id, _ in existing_qt}
        report["previously_mapped"] = len(mapped_qids)

        # Pre-build classifiers
        classifiers_by_track = {}
        if course_id == 8:
            tracks = db.query(CourseTrack).filter(CourseTrack.course_id == 8).all()
            for t in tracks:
                rules = registry.get_topic_rules(8, track_id=t.id)
                classifiers_by_track[t.id] = TaxonomyClassifierService(rules=rules)
        else:
            rules = registry.get_topic_rules(course_id)
            default_classifier = TaxonomyClassifierService(rules=rules)

        for q in questions:
            exam = q.section.exam if q.section else None
            t_id = exam.track_id if exam else None
            t_label = f"Track_{t_id}" if t_id else "SingleTrack"

            report["by_track"][t_label]["total"] += 1

            if q.id in mapped_qids:
                continue

            # Select classifier
            if course_id == 8:
                if not t_id or t_id not in classifiers_by_track:
                    # Skip exams without assigned track
                    report["unmapped"] += 1
                    report["by_track"][t_label]["unmapped"] += 1
                    continue
                classifier = classifiers_by_track[t_id]
            else:
                classifier = default_classifier

            text = q.original_text or q.normalized_text or ""
            proposal = classifier.classify(q.id, text)

            if proposal.confidence in ("HIGH", "MEDIUM") and proposal.topic_id:
                report["newly_mapped"] += 1
                report["by_track"][t_label]["newly_mapped"] += 1

                if proposal.confidence == "HIGH":
                    report["high_confidence"] += 1
                    report["by_track"][t_label]["high"] += 1
                else:
                    report["medium_confidence"] += 1
                    report["by_track"][t_label]["medium"] += 1

                if len(report["samples"]) < 20:
                    report["samples"].append({
                        "question_id": q.id,
                        "exam_id": exam.id if exam else None,
                        "track_id": t_id,
                        "topic_id": proposal.topic_id,
                        "topic_name": proposal.topic_name,
                        "unit_id": proposal.unit_id,
                        "confidence": proposal.confidence,
                        "method": proposal.method,
                        "text": text[:100].strip().replace("\n", " ")
                    })

                if apply_changes:
                    # Insert question_topic row
                    db.execute(
                        question_topic.insert().values(
                            question_id=q.id,
                            topic_id=proposal.topic_id
                        )
                    )
                    # Update question metadata
                    q.classification_confidence = 0.95 if proposal.confidence == "HIGH" else 0.80
                    q.classification_input = text
                    q.classification_metadata = {
                        "topic_id": proposal.topic_id,
                        "topic_name": proposal.topic_name,
                        "unit_id": proposal.unit_id,
                        "unit_name": proposal.unit_name,
                        "confidence": proposal.confidence,
                        "method": proposal.method,
                        "evidence": proposal.evidence,
                        "track_id": t_id,
                    }
            elif proposal.confidence == "AMBIGUOUS":
                report["ambiguous"] += 1
                report["by_track"][t_label]["ambiguous"] += 1
            else:
                report["unmapped"] += 1
                report["by_track"][t_label]["unmapped"] += 1

        if apply_changes:
            db.commit()
            print(f"[APPLIED] Course {course_id}: newly mapped {report['newly_mapped']} questions to canonical topics.")
        else:
            print(f"[DRY-RUN] Course {course_id}: would map {report['newly_mapped']} questions (HIGH: {report['high_confidence']}, MED: {report['medium_confidence']}).")

        return report
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Map onboarded courses questions to topics.")
    parser.add_argument("--course", type=int, choices=[8, 19, 20], help="Specific course ID")
    parser.add_argument("--all", action="store_true", help="Map all onboarded courses (8, 19, 20)")
    parser.add_argument("--apply", action="store_true", help="Commit changes to database")
    args = parser.parse_args()

    courses = [args.course] if args.course else ([8, 19, 20] if args.all else [8, 19, 20])

    for cid in courses:
        print(f"\n==========================================")
        print(f"Processing Course {cid}")
        print(f"==========================================")
        res = run_course_mapping(cid, apply_changes=args.apply)
        print(f"Total Authentic: {res['total_authentic_questions']}")
        print(f"Newly Mapped:    {res['newly_mapped']} (HIGH: {res['high_confidence']}, MED: {res['medium_confidence']})")
        print(f"Ambiguous:       {res['ambiguous']}")
        print(f"Unmapped:        {res['unmapped']}")
        if res.get("by_track"):
            print("Track breakdown:")
            for trk, stats in res["by_track"].items():
                print(f"  {trk}: total {stats['total']}, newly mapped {stats['newly_mapped']} (HIGH: {stats['high']}, MED: {stats['medium']}, AMB: {stats['ambiguous']}, UNM: {stats['unmapped']})")


if __name__ == "__main__":
    main()
