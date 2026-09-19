"""
MarkMint Mapping Gap Inventory.

Produces an auditable, ranked breakdown of question-to-topic mapping gaps across
the entire MarkMint corpus, strictly distinguishing authentic examination papers
from Question Banks, Study Material, Empty OCR Text, and Legacy Regulations.

Usage:
    python scripts/audit/mapping_gap_inventory.py
    python scripts/audit/mapping_gap_inventory.py --top 10
"""

import os
import sys
import argparse
from typing import Dict, List, Any
from collections import defaultdict
from sqlalchemy.orm import selectinload

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus, Document
from backend.services.observed_assessment_coverage import identify_exam_assessment
from scripts.audit.unmapped_exam_questions import determine_unmapped_reason


def generate_gap_inventory(top_n: int = None, db_session = None) -> Dict[str, Any]:
    db = db_session or SessionLocal()

    courses = db.query(Course).order_by(Course.id).all()
    inventory = []

    total_all_questions = 0
    total_all_mapped = 0
    total_all_unmapped = 0

    total_authentic_questions = 0
    total_authentic_mapped = 0
    total_authentic_unmapped = 0

    total_non_exam_questions = 0

    for course in courses:
        exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.document),
                selectinload(Exam.sections).selectinload(Section.questions).selectinload(Question.topics)
            )
            .filter(Exam.course_id == course.id)
            .order_by(Exam.year.desc().nullslast(), Exam.id.asc())
            .all()
        )

        c_total = 0
        c_mapped = 0
        c_unmapped = 0

        c_auth_total = 0
        c_auth_mapped = 0
        c_auth_unmapped = 0

        # Category breakdowns
        categories = defaultdict(int)
        exam_breakdowns = []

        for ex in exams:
            ident = identify_exam_assessment(ex, course.id)
            doc_title = ex.document.title if ex.document else "Untitled"

            e_total = 0
            e_mapped = 0
            e_unmapped = 0
            e_categories = defaultdict(int)

            for sec in ex.sections:
                for q in sec.questions:
                    e_total += 1
                    is_mapped = len(q.topics) > 0
                    if is_mapped:
                        e_mapped += 1
                    else:
                        e_unmapped += 1
                        reason = determine_unmapped_reason(q, ex)
                        # Extract the base category
                        cat_key = reason.split(" ")[0]
                        categories[cat_key] += 1
                        e_categories[cat_key] += 1

            c_total += e_total
            c_mapped += e_mapped
            c_unmapped += e_unmapped

            # Authentic exam determination: not pure question bank, not study material
            is_non_exam = any(k in e_categories for k in ["QUESTION_BANK", "STUDY_MATERIAL"]) and e_mapped == 0 and ident.normalized_code == "UNKNOWN"
            if not is_non_exam:
                c_auth_total += e_total
                c_auth_mapped += e_mapped
                # Authentic unmapped are those in PENDING_CLASSIFICATION or TAXONOMY_EXPANSION_PENDING
                c_auth_unmapped += (e_categories.get("PENDING_CLASSIFICATION", 0) + e_categories.get("TAXONOMY_EXPANSION_PENDING", 0))

            exam_breakdowns.append({
                "exam_id": ex.id,
                "year": ex.year,
                "assessment": ident.normalized_code,
                "cycle": ident.student_cycle,
                "document": doc_title,
                "total": e_total,
                "mapped": e_mapped,
                "unmapped": e_unmapped,
                "categories": dict(e_categories),
            })

        total_all_questions += c_total
        total_all_mapped += c_mapped
        total_all_unmapped += c_unmapped

        total_authentic_questions += c_auth_total
        total_authentic_mapped += c_auth_mapped
        total_authentic_unmapped += c_auth_unmapped

        non_exam = categories.get("QUESTION_BANK", 0) + categories.get("STUDY_MATERIAL", 0) + categories.get("EMPTY_TEXT", 0) + categories.get("LEGACY_REGULATION", 0)
        total_non_exam_questions += non_exam

        auth_unmapped = categories.get("PENDING_CLASSIFICATION", 0) + categories.get("TAXONOMY_EXPANSION_PENDING", 0)
        auth_rate = (c_auth_mapped / c_auth_total * 100) if c_auth_total > 0 else 0.0
        overall_rate = (c_mapped / c_total * 100) if c_total > 0 else 0.0

        inventory.append({
            "course_id": course.id,
            "course_code": course.canonical_code or course.code,
            "course_name": course.name,
            "total_questions": c_total,
            "mapped_questions": c_mapped,
            "unmapped_questions": c_unmapped,
            "overall_mapping_rate": round(overall_rate, 1),
            "authentic_questions": c_auth_total,
            "authentic_mapped": c_auth_mapped,
            "authentic_unmapped": auth_unmapped,
            "authentic_mapping_rate": round(auth_rate, 1),
            "pending_classification": categories.get("PENDING_CLASSIFICATION", 0),
            "taxonomy_expansion_pending": categories.get("TAXONOMY_EXPANSION_PENDING", 0),
            "legacy_regulation": categories.get("LEGACY_REGULATION", 0),
            "question_bank": categories.get("QUESTION_BANK", 0),
            "study_material": categories.get("STUDY_MATERIAL", 0),
            "empty_text": categories.get("EMPTY_TEXT", 0),
            "exams": exam_breakdowns,
        })

    # Rank courses primarily by authentic unmapped count, then by authentic unmapped percentage
    inventory.sort(
        key=lambda x: (-x["authentic_unmapped"], -(100.0 - x["authentic_mapping_rate"]))
    )

    print("=" * 110)
    print("MARKMINT MAPPING GAP INVENTORY: AUTHENTIC EXAM GAP RANKING")
    print("=" * 110)
    print(f"{'Rank':4s} | {'Code':12s} | {'Course Name':32s} | {'Total':5s} | {'Mapped':6s} | {'Unmapped':8s} | {'Auth Unmapped':13s} | {'Auth Rate':9s} | Top Reason")
    print("-" * 110)

    for rank, item in enumerate(inventory, start=1):
        if top_n and rank > top_n:
            break
        top_reason = "PENDING_CLASSIF" if item["pending_classification"] >= item["taxonomy_expansion_pending"] else "TAXONOMY_PEND"
        if item["authentic_unmapped"] == 0:
            top_reason = "NONE (Clean)" if item["unmapped_questions"] == 0 else "NON_EXAM/LEGACY"
        print(
            f"{rank:4d} | {item['course_code']:12s} | {item['course_name'][:32]:32s} | "
            f"{item['total_questions']:5d} | {item['mapped_questions']:6d} | {item['unmapped_questions']:8d} | "
            f"{item['authentic_unmapped']:13d} | {item['authentic_mapping_rate']:8.1f}% | {top_reason}"
        )

    print("=" * 110)
    print("INVENTORY SUMMARY:")
    print(f"  Total Questions Across All Papers:     {total_all_questions}")
    print(f"  Total Mapped Questions:                {total_all_mapped} ({total_all_mapped / total_all_questions * 100:.1f}%)")
    print(f"  Total Unmapped Questions:              {total_all_unmapped} ({total_all_unmapped / total_all_questions * 100:.1f}%)")
    print("  Breakdown of Unmapped Questions:")
    auth_total = sum(x["authentic_unmapped"] for x in inventory)
    qb_total = sum(x["question_bank"] for x in inventory)
    leg_total = sum(x["legacy_regulation"] for x in inventory)
    sm_total = sum(x["study_material"] for x in inventory)
    empty_total = sum(x["empty_text"] for x in inventory)
    print(f"    - Authentic Exam Unmapped (Pending): {auth_total:5d} ({auth_total / total_all_unmapped * 100:.1f}%)")
    print(f"        * PENDING_CLASSIFICATION:        {sum(x['pending_classification'] for x in inventory):5d}")
    print(f"        * TAXONOMY_EXPANSION_PENDING:    {sum(x['taxonomy_expansion_pending'] for x in inventory):5d}")
    print(f"    - Question Bank Practice Material:   {qb_total:5d} ({qb_total / total_all_unmapped * 100:.1f}%)")
    print(f"    - Legacy Regulation (2015/2018):     {leg_total:5d} ({leg_total / total_all_unmapped * 100:.1f}%)")
    print(f"    - Study Material / Lecture Notes:    {sm_total:5d} ({sm_total / total_all_unmapped * 100:.1f}%)")
    print(f"    - Empty / Unreadable OCR Text:       {empty_total:5d} ({empty_total / total_all_unmapped * 100:.1f}%)")
    print("=" * 110)

    if not db_session:
        db.close()

    return {
        "inventory": inventory,
        "total_questions": total_all_questions,
        "total_mapped": total_all_mapped,
        "total_unmapped": total_all_unmapped,
        "authentic_unmapped": auth_total,
        "question_bank": qb_total,
        "legacy_regulation": leg_total,
        "study_material": sm_total,
        "empty_text": empty_total,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mapping gap inventory.")
    parser.add_argument("--top", type=int, help="Show top N ranked courses.")
    args = parser.parse_args()

    generate_gap_inventory(top_n=args.top)
