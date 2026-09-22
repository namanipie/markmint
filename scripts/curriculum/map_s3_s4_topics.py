"""
Deterministic taxonomy mapping script for Semester 3 and Semester 4 Core CSE:
- Course 24: Data Structures and Algorithms (21CSC201J)
- Course 25: Operating Systems (21CSC202J)
- Course 26: Computer Organization and Architecture (21CSS201T)
- Course 27: Design and Analysis of Algorithms (21CSC204J)
- Course 28: Database Management Systems (21CSC205P)

Guarantees:
- Uses authoritative declarative rules from TaxonomyRegistry.
- Zero cross-course leakage (rules strictly scoped per course).
- Maps high and medium confidence proposals into question_topic.
- Auditable provenance and metadata recording.
"""
import os
import sys
import json
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, Topic, question_topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService

COURSE_IDS = [24, 25, 26, 27, 28]

def map_s3_s4_questions(apply_changes: bool = True):
    db = SessionLocal()
    registry = get_taxonomy_registry()
    overall_summary = {}

    try:
        for course_id in COURSE_IDS:
            entry = registry.get_course(course_id)
            course_name = entry.course.name
            rules = registry.get_topic_rules(course_id)
            classifier = TaxonomyClassifierService(rules)

            # Fetch all questions for this course
            questions = (
                db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .filter(Exam.course_id == course_id)
                .order_by(Question.id)
                .all()
            )

            total_q = len(questions)
            mapped_count = 0
            high_count = 0
            medium_count = 0
            unmapped_count = 0
            proposals = []

            # Track existing mappings
            q_ids = [q.id for q in questions]
            existing_mappings = set(
                db.query(question_topic.c.question_id, question_topic.c.topic_id)
                .filter(question_topic.c.question_id.in_(q_ids))
                .all()
            )

            to_insert = []

            for q in questions:
                proposal = classifier.classify(q.id, q.original_text)
                proposals.append((q, proposal))

                if proposal.confidence in ["HIGH", "MEDIUM"] and proposal.topic_id:
                    mapped_count += 1
                    if proposal.confidence == "HIGH":
                        high_count += 1
                    else:
                        medium_count += 1

                    if (q.id, proposal.topic_id) not in existing_mappings:
                        to_insert.append((q.id, proposal.topic_id))

                    if apply_changes:
                        q.classification_confidence = 0.95 if proposal.confidence == "HIGH" else 0.80
                        q.classification_input = q.original_text
                        q.classification_metadata = {
                            "method": proposal.method,
                            "confidence": proposal.confidence,
                            "evidence": proposal.evidence,
                            "topic_id": proposal.topic_id,
                            "topic_name": proposal.topic_name,
                            "unit_id": proposal.unit_id,
                            "unit_name": proposal.unit_name
                        }
                else:
                    unmapped_count += 1
                    if apply_changes:
                        q.classification_confidence = 0.0
                        q.classification_input = q.original_text
                        q.classification_metadata = {
                            "method": proposal.method,
                            "confidence": "UNMAPPED",
                            "evidence": proposal.evidence,
                            "candidate_topics": proposal.candidate_topics
                        }

            if apply_changes and to_insert:
                for qid, tid in to_insert:
                    db.execute(
                        question_topic.insert().values(question_id=qid, topic_id=tid)
                    )
                db.flush()

            mapping_rate = (mapped_count / total_q * 100) if total_q > 0 else 0
            overall_summary[course_id] = {
                "course_name": course_name,
                "canonical_code": entry.course.canonical_code,
                "total_questions": total_q,
                "mapped_questions": mapped_count,
                "high_confidence": high_count,
                "medium_confidence": medium_count,
                "unmapped_questions": unmapped_count,
                "mapping_rate": f"{mapping_rate:.1f}%",
                "new_mappings_inserted": len(to_insert)
            }

            print(f"\n[{entry.course.canonical_code}] {course_name}:")
            print(f"  Total Questions: {total_q}")
            print(f"  Mapped: {mapped_count} ({mapping_rate:.1f}%) [HIGH: {high_count}, MEDIUM: {medium_count}]")
            print(f"  Unmapped: {unmapped_count}")
            print(f"  New question_topic rows inserted: {len(to_insert)}")

        if apply_changes:
            db.commit()
            print("\nSuccessfully committed all mappings to database!")
        else:
            db.rollback()
            print("\nDRY RUN complete - no database changes committed.")

        return overall_summary

    except Exception as e:
        db.rollback()
        print(f"Error during taxonomy mapping: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    map_s3_s4_questions(apply_changes=True)
