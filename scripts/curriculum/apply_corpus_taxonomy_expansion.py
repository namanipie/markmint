"""
MarkMint Phase 3: Apply Corpus Taxonomy Expansion.

Executes TaxonomyClassifierService on authentic unmapped exam questions across
the 8 target courses with existing canonical syllabus taxonomies:
  - Course 13: SPCM (21PYB102J)
  - Course 14: EEE (21EEB101J)
  - Course 15: Communicative English (21LEH101T)
  - Course 1:  Calculus (21MAB101T)
  - Course 16: ACCA (21MAB102T)
  - Course 17: OODP (21CSC102J)
  - Course 18: ESPCB (21ECC101J)
  - Course 5:  PPS (21CSS101J)

INVARIANTS:
1. Only authentic examination papers are processed (excludes QUESTION_BANK,
   STUDY_MATERIAL, EMPTY_TEXT, and LEGACY_REGULATION).
2. Existing Question -> Topic mappings are NEVER modified or deleted.
3. Only HIGH and MEDIUM confidence classifications are promoted to question_topic.
4. AMBIGUOUS and UNMAPPED questions are strictly preserved as unmapped.
5. All lineage Question -> Topic -> Unit is strictly canonical and validated.
6. Raw Exam.assessment_type is NEVER modified.
"""

import os
import sys
import json
from collections import defaultdict
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Exam, Section, Topic, Unit, Course, question_topic
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_registry import get_taxonomy_registry
from scripts.audit.unmapped_exam_questions import determine_unmapped_reason


TARGET_COURSES = [
    (13, "SPCM"),
    (14, "EEE"),
    (15, "English"),
    (1, "Calculus"),
    (16, "ACCA"),
    (17, "OODP"),
    (18, "ESPCB"),
    (5, "PPS")
]

EXCLUDED_ASSESSMENT_TYPES = {
    "QUESTION_BANK",
    "STUDY_MATERIAL",
    "EMPTY_TEXT",
    "LEGACY_REGULATION"
}


def apply_expansion(dry_run: bool = False) -> Dict[str, Any]:
    db = SessionLocal()
    registry = get_taxonomy_registry()

    report = {
        "dry_run": dry_run,
        "courses": {},
        "total_newly_mapped": 0,
        "total_high": 0,
        "total_medium": 0,
        "total_ambiguous": 0,
        "total_unmapped": 0,
        "samples": []
    }

    try:
        for course_id, course_name in TARGET_COURSES:
            rules = registry.get_topic_rules(course_id)
            classifier = TaxonomyClassifierService(rules=rules)

            # Query authentic unmapped questions for this course (strictly 2019+ authentic exam papers)
            unmapped_questions = (
                db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .filter(Exam.course_id == course_id)
                .filter(~Exam.assessment_type.in_(EXCLUDED_ASSESSMENT_TYPES))
                .filter(Exam.year > 2018)
                .filter(~Question.topics.any())
                .order_by(Question.id)
                .all()
            )

            course_stat = {
                "course_id": course_id,
                "course_name": course_name,
                "unmapped_authentic_pool": len(unmapped_questions),
                "newly_mapped": 0,
                "high": 0,
                "medium": 0,
                "ambiguous": 0,
                "still_unmapped": 0,
                "promoted_topic_ids": defaultdict(int)
            }

            for q in unmapped_questions:
                exam = q.section.exam if q.section else None
                reason = determine_unmapped_reason(q, exam) if exam else "UNKNOWN"
                if not reason.startswith("PENDING_CLASSIFICATION"):
                    course_stat["still_unmapped"] += 1
                    report["total_unmapped"] += 1
                    continue

                text = q.original_text or q.normalized_text or ""
                proposal = classifier.classify(q.id, text)

                if proposal.confidence in ("HIGH", "MEDIUM") and proposal.topic_id:
                    course_stat["newly_mapped"] += 1
                    if proposal.confidence == "HIGH":
                        course_stat["high"] += 1
                        report["total_high"] += 1
                    else:
                        course_stat["medium"] += 1
                        report["total_medium"] += 1

                    course_stat["promoted_topic_ids"][proposal.topic_id] += 1
                    report["total_newly_mapped"] += 1

                    if len(report["samples"]) < 50:
                        report["samples"].append({
                            "question_id": q.id,
                            "course_id": course_id,
                            "course_name": course_name,
                            "topic_id": proposal.topic_id,
                            "topic_name": proposal.topic_name,
                            "unit_id": proposal.unit_id,
                            "unit_name": proposal.unit_name,
                            "confidence": proposal.confidence,
                            "method": proposal.method,
                            "text_snippet": (q.original_text or "")[:120].strip().replace("\n", " ")
                        })

                    if not dry_run:
                        # Insert into question_topic
                        topic_obj = db.get(Topic, proposal.topic_id)
                        if topic_obj and topic_obj not in q.topics:
                            q.topics.append(topic_obj)
                            q.classification_confidence = 0.95 if proposal.confidence == "HIGH" else 0.80

                elif proposal.confidence == "AMBIGUOUS":
                    course_stat["ambiguous"] += 1
                    report["total_ambiguous"] += 1
                else:
                    course_stat["still_unmapped"] += 1
                    report["total_unmapped"] += 1

            report["courses"][course_id] = course_stat

        if not dry_run:
            db.commit()
            print("Successfully committed new question mappings to database.")
        else:
            db.rollback()
            print("Dry run completed. No changes committed.")

    finally:
        db.close()

    return report


def print_report(report: Dict[str, Any]):
    print("\n" + "=" * 90)
    print(f"MARKMINT CORPUS TAXONOMY EXPANSION REPORT ({'DRY RUN' if report['dry_run'] else 'APPLIED'})")
    print("=" * 90)
    print(f"{'Course':<12} | {'Pool':>6} | {'New Map':>8} | {'HIGH':>6} | {'MED':>5} | {'AMBIG':>6} | {'UNMAP':>6} | {'Yield':>6}")
    print("-" * 90)

    for cid, stat in report["courses"].items():
        pool = stat["unmapped_authentic_pool"]
        new_map = stat["newly_mapped"]
        rate = (new_map / pool * 100) if pool else 0.0
        print(f"{stat['course_name']:<12} | {pool:>6} | {new_map:>8} | {stat['high']:>6} | {stat['medium']:>5} | {stat['ambiguous']:>6} | {stat['still_unmapped']:>6} | {rate:>5.1f}%")

    print("-" * 90)
    print(f"{'TOTAL':<12} | {sum(s['unmapped_authentic_pool'] for s in report['courses'].values()):>6} | {report['total_newly_mapped']:>8} | {report['total_high']:>6} | {report['total_medium']:>5} | {report['total_ambiguous']:>6} | {report['total_unmapped']:>6} | {(report['total_newly_mapped'] / sum(s['unmapped_authentic_pool'] for s in report['courses'].values()) * 100):>5.1f}%")
    print("=" * 90)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without committing")
    args = parser.parse_args()

    rep = apply_expansion(dry_run=args.dry_run)
    print_report(rep)
