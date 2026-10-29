"""
Development and verification script for Phase 6.4 taxonomy refinements.
Tests additions in-memory against all second-year questions before writing to JSON.
"""
import os
import sys
import copy
import json
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, question_topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry, TaxonomyTopicRule
from backend.services.taxonomy_classifier import TaxonomyClassifierService

def run():
    db = SessionLocal()
    reg = get_taxonomy_registry()

    # Load all questions for S3-S4 courses
    courses = [22, 24, 25, 26, 27, 28, 29]
    questions_by_course = {}
    for cid in courses:
        qs = (
            db.query(Question.id, Question.original_text)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .order_by(Question.id)
            .all()
        )
        questions_by_course[cid] = qs

    # Load baseline mappings
    baseline_mapped = set(
        row[0] for row in db.query(question_topic.c.question_id).all()
    )

    print(f"Loaded questions across {len(courses)} courses:")
    for cid in courses:
        print(f"  Course {cid}: {len(questions_by_course[cid])} questions")

if __name__ == "__main__":
    run()
