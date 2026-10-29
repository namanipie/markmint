"""
Read-Only Audit Script for Phase 6 Second-Year Taxonomy & Mapping Quality.
Analyzes Courses 22, 24, 25, 26, 27, 28, 29, 30, 31:
- Mapping status, confidence breakdown (HIGH, MEDIUM, LOW, UNRESOLVED, NEEDS_REVIEW)
- Topic coverage (represented topics vs zero-question topics)
- Unmapped question analysis & classification into A, B, C, D, E categories
- Taxonomy gaps vs missing classification keywords
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
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus, question_topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService

SECOND_YEAR_COURSES = [22, 24, 25, 26, 27, 28, 29, 30, 31]

def run_audit():
    db = SessionLocal()
    registry = get_taxonomy_registry()

    report = {}

    try:
        for cid in SECOND_YEAR_COURSES:
            course = db.query(Course).filter(Course.id == cid).first()
            if not course:
                continue

            entry = registry.get_course(cid) if registry.has_course(cid) else None
            rules = registry.get_topic_rules(cid) if entry else []
            classifier = TaxonomyClassifierService(rules) if rules else None

            # Get all questions
            questions = (
                db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .filter(Exam.course_id == cid)
                .order_by(Question.id)
                .all()
            )

            total_q = len(questions)
            mapped_qs = [q for q in questions if q.topics]
            unmapped_qs = [q for q in questions if not q.topics]

            # Confidence breakdown from existing metadata / classifier evaluation
            high_count = 0
            med_count = 0
            low_count = 0
            needs_review_count = 0
            unresolved_count = 0

            # Inspect mapped questions
            for q in mapped_qs:
                meta = q.classification_metadata or {}
                conf = meta.get("confidence")
                if not conf and classifier:
                    p = classifier.classify(q.id, q.original_text)
                    conf = p.confidence

                if conf == "HIGH":
                    high_count += 1
                elif conf == "MEDIUM":
                    med_count += 1
                elif conf == "LOW":
                    low_count += 1
                else:
                    med_count += 1 # mapped in question_topic

                if q.needs_review:
                    needs_review_count += 1

            # All topics for this course
            topics = (
                db.query(Topic)
                .join(Unit, Topic.unit_id == Unit.id)
                .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                .filter(Syllabus.course_id == cid)
                .all()
            )

            # Topic question distribution
            topic_q_counts = defaultdict(int)
            for q in mapped_qs:
                for t in q.topics:
                    topic_q_counts[t.id] += 1

            represented_topics = [t for t in topics if topic_q_counts[t.id] > 0]
            zero_q_topics = [t for t in topics if topic_q_counts[t.id] == 0]

            # Analyze unmapped questions
            unmapped_analysis = {
                "A_EXISTING_TOPIC_CONFIDENT": [],
                "B_EXISTING_TOPIC_AMBIGUOUS": [],
                "C_TAXONOMY_GAP": [],
                "D_OUT_OF_SYLLABUS": [],
                "E_INSUFFICIENT_INFORMATION": [],
            }

            for q in unmapped_qs:
                text = q.original_text or ""
                norm = TaxonomyClassifierService.normalize_text(text)
                proposal = classifier.classify(q.id, text) if classifier else None

                if proposal and proposal.confidence in ["HIGH", "MEDIUM"]:
                    # Can be mapped with current rules if rerun!
                    unmapped_analysis["A_EXISTING_TOPIC_CONFIDENT"].append({
                        "id": q.id,
                        "text": text[:120],
                        "suggested_topic": proposal.topic_name,
                        "confidence": proposal.confidence,
                        "method": proposal.method
                    })
                elif proposal and proposal.confidence == "AMBIGUOUS":
                    unmapped_analysis["B_EXISTING_TOPIC_AMBIGUOUS"].append({
                        "id": q.id,
                        "text": text[:120],
                        "candidates": [c.get("topic_name") for c in proposal.candidate_topics]
                    })
                elif len(norm.split()) < 4:
                    unmapped_analysis["E_INSUFFICIENT_INFORMATION"].append({
                        "id": q.id,
                        "text": text[:120],
                        "reason": "Text too short or missing context"
                    })
                else:
                    # Check if text aligns with syllabus topics but lacks rule keywords
                    # Or represents a distinct syllabus topic missing in taxonomy
                    unmapped_analysis["C_TAXONOMY_GAP"].append({
                        "id": q.id,
                        "text": text[:140],
                    })

            unresolved_count = len(unmapped_qs)

            report[cid] = {
                "course_name": course.name,
                "canonical_code": course.canonical_code,
                "semester": course.semester,
                "total_questions": total_q,
                "mapped_questions": len(mapped_qs),
                "unmapped_questions": len(unmapped_qs),
                "high_confidence": high_count,
                "medium_confidence": med_count,
                "low_confidence": low_count,
                "needs_review": needs_review_count,
                "unresolved": unresolved_count,
                "topics_total": len(topics),
                "topics_represented": len(represented_topics),
                "topics_zero_questions": len(zero_q_topics),
                "zero_topics_names": [f"{t.id}: {t.name}" for t in zero_q_topics[:10]],
                "unmapped_categorization": {
                    k: len(v) for k, v in unmapped_analysis.items()
                },
                "unmapped_sample": {
                    k: v[:5] for k, v in unmapped_analysis.items()
                }
            }

        with open("data/s3_s4/second_year_taxonomy_audit.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("=== READ-ONLY SECOND-YEAR TAXONOMY MAPPING AUDIT ===")
        print(f"{'Course':<40} | {'Total':<5} | {'Mapped':<6} | {'Unmapped':<8} | {'Cov%':<6} | {'High':<5} | {'Med':<5} | {'Zero-Topics'}")
        print("-" * 105)
        for cid, r in report.items():
            cov = f"{(r['mapped_questions']/r['total_questions']*100):.1f}%" if r['total_questions'] else "0.0%"
            zero_top = f"{r['topics_zero_questions']}/{r['topics_total']}"
            print(f"{r['course_name'][:38]:<40} | {r['total_questions']:<5} | {r['mapped_questions']:<6} | {r['unmapped_questions']:<8} | {cov:<6} | {r['high_confidence']:<5} | {r['medium_confidence']:<5} | {zero_top}")

    finally:
        db.close()

if __name__ == "__main__":
    run_audit()
