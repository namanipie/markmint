"""
MarkMint Corpus Quality Audit: Unmapped Exam Questions & Mapping Rates.

Audits question-to-topic mapping completeness across the entire MarkMint corpus.
Exposes data-quality metrics (mapped_questions, unmapped_questions, mapping_rate)
broken down by:
- Course
- Assessment cycle
- Exam paper
- Academic year

Usage:
    python scripts/audit/unmapped_exam_questions.py
    python scripts/audit/unmapped_exam_questions.py --summary-only
    python scripts/audit/unmapped_exam_questions.py --course 21MAB101T
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
from backend.models.core import Course, Exam, Section, Question, Topic, Document
from backend.services.observed_assessment_coverage import identify_exam_assessment


def determine_unmapped_reason(q: Question, exam: Exam) -> str:
    """Categorizes why a question currently lacks canonical topic mapping."""
    text = (q.original_text or q.normalized_text or "").strip()
    doc_title = (exam.document.title if exam.document else "") or ""
    doc_title_upper = doc_title.upper()

    if not text:
        return "EMPTY_TEXT (OCR extraction yielded no textual content)"
    if any(term in doc_title_upper for term in ["Q-BANK", "QUESTION BANK", "QB ANS", "SHORT ANSWER QUESTIONS"]):
        return "QUESTION_BANK (Practice question repository without targeted exam paper scope)"
    if "CHAPTER" in doc_title_upper or "ALL UNIT" in doc_title_upper:
        return "STUDY_MATERIAL (Lecture note / reference material, not an examination paper)"
    if exam.year and exam.year <= 2018:
        return "LEGACY_REGULATION (Historical 2015/2018 paper; topics may differ from Regulation 2021)"
    if exam.course and exam.course.canonical_code in ("21GNH101J", "SEM1-FORE", "21PYB101J", "SEM1-EMPHY", "SEM1-PHYMECH"):
        return "TAXONOMY_EXPANSION_PENDING (Course taxonomy not yet expanded with keyword classification rules)"
    return "PENDING_CLASSIFICATION (Unmatched by active deterministic classifier rules)"


def audit_corpus_mapping_quality(
    course_filter: str = None,
    summary_only: bool = False,
    unmapped_only: bool = False,
    db_session = None,
) -> Dict[str, Any]:
    db = db_session or SessionLocal()

    query = db.query(Course).order_by(Course.id)
    if course_filter:
        query = query.filter(
            (Course.canonical_code == course_filter) |
            (Course.code == course_filter) |
            (Course.name.ilike(f"%{course_filter}%"))
        )
    courses = query.all()

    total_corpus_questions = 0
    total_corpus_mapped = 0
    total_corpus_unmapped = 0

    course_summaries = []
    detailed_unmapped_records = []

    print("=" * 80)
    print("MARKMINT PERMANENT CORPUS QUALITY AUDIT: QUESTION MAPPING COMPLETENESS")
    print("=" * 80)

    for course in courses:
        course_exams = (
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

        # Assessment cycle breakdowns
        by_cycle = defaultdict(lambda: {"total": 0, "mapped": 0, "unmapped": 0})
        by_year = defaultdict(lambda: {"total": 0, "mapped": 0, "unmapped": 0})
        exam_records = []

        for ex in course_exams:
            ident = identify_exam_assessment(ex, course.id)
            cycle = ident.student_cycle
            year_label = str(ex.year) if ex.year else "Unknown Year"

            e_total = 0
            e_mapped = 0
            e_unmapped = 0

            for sec in ex.sections:
                for q in sec.questions:
                    e_total += 1
                    is_mapped = len(q.topics) > 0
                    if is_mapped:
                        e_mapped += 1
                    else:
                        e_unmapped += 1
                        reason = determine_unmapped_reason(q, ex)
                        rec = {
                            "exam_id": ex.id,
                            "course_id": course.id,
                            "course_code": course.canonical_code or course.code,
                            "course_name": course.name,
                            "year": ex.year,
                            "assessment": ident.normalized_code,
                            "student_cycle": cycle,
                            "question_id": q.id,
                            "question_number": str(q.question_number),
                            "marks": q.marks,
                            "mapping_state": "UNMAPPED",
                            "reason_unmapped": reason,
                            "text_snippet": (q.original_text or q.normalized_text or "")[:100].replace("\n", " "),
                        }
                        detailed_unmapped_records.append(rec)

            c_total += e_total
            c_mapped += e_mapped
            c_unmapped += e_unmapped

            by_cycle[cycle]["total"] += e_total
            by_cycle[cycle]["mapped"] += e_mapped
            by_cycle[cycle]["unmapped"] += e_unmapped

            by_year[year_label]["total"] += e_total
            by_year[year_label]["mapped"] += e_mapped
            by_year[year_label]["unmapped"] += e_unmapped

            e_rate = (e_mapped / e_total * 100) if e_total > 0 else 0.0
            exam_records.append({
                "exam_id": ex.id,
                "year": ex.year,
                "assessment": ident.normalized_code,
                "student_cycle": cycle,
                "document_title": ex.document.title if ex.document else None,
                "total_questions": e_total,
                "mapped_questions": e_mapped,
                "unmapped_questions": e_unmapped,
                "mapping_rate": round(e_rate, 1),
            })

        c_rate = (c_mapped / c_total * 100) if c_total > 0 else 0.0
        total_corpus_questions += c_total
        total_corpus_mapped += c_mapped
        total_corpus_unmapped += c_unmapped

        course_data = {
            "course_id": course.id,
            "course_code": course.canonical_code or course.code,
            "course_name": course.name,
            "total_questions": c_total,
            "mapped_questions": c_mapped,
            "unmapped_questions": c_unmapped,
            "mapping_rate": round(c_rate, 1),
            "by_cycle": dict(by_cycle),
            "by_year": dict(by_year),
            "exams": exam_records,
        }
        course_summaries.append(course_data)

        # Output course report
        print(f"\n[{course.canonical_code or course.code}] {course.name}")
        print(f"  Total Questions: {c_total} | Mapped: {c_mapped} | Unmapped: {c_unmapped} | Mapping Rate: {c_rate:.1f}%")

        if by_cycle:
            print("  Assessment Cycle Quality:")
            for cyc, stats in sorted(by_cycle.items()):
                rate = (stats["mapped"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
                print(f"    - {cyc:8s}: {stats['total']:3d} Qs | {stats['mapped']:3d} mapped | {stats['unmapped']:3d} unmapped | {rate:5.1f}% rate")

        if not summary_only and exam_records:
            print("  Exam Paper Quality:")
            for er in exam_records:
                print(f"    Exam {er['exam_id']:3d} (Yr {str(er['year']):4s}, {er['student_cycle']:6s}): {er['total_questions']:2d} Qs | {er['mapped_questions']:2d} mapped | {er['unmapped_questions']:2d} unmapped ({er['mapping_rate']:5.1f}%) | {er['document_title'] or 'N/A'}")

    corpus_rate = (total_corpus_mapped / total_corpus_questions * 100) if total_corpus_questions > 0 else 0.0

    print("\n" + "=" * 80)
    print("CORPUS OVERALL QUALITY METRIC SUMMARY")
    print("=" * 80)
    print(f"Total Exam Papers In Corpus: {sum(len(c['exams']) for c in course_summaries)}")
    print(f"Total Corpus Questions:      {total_corpus_questions}")
    print(f"Total Mapped Questions:      {total_corpus_mapped}")
    print(f"Total Unmapped Questions:    {total_corpus_unmapped}")
    print(f"Corpus Overall Mapping Rate: {corpus_rate:.1f}%")
    print("=" * 80)

    # Reasons breakdown for unmapped questions
    reason_counts = defaultdict(int)
    for u in detailed_unmapped_records:
        reason_counts[u["reason_unmapped"]] += 1

    print("\nUnmapped Questions Breakdown By Reason:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        pct = (count / total_corpus_unmapped * 100) if total_corpus_unmapped > 0 else 0.0
        print(f"  - {reason:30s}: {count:4d} ({pct:5.1f}%)")

    if not db_session:
        db.close()

    return {
        "total_corpus_questions": total_corpus_questions,
        "total_corpus_mapped": total_corpus_mapped,
        "total_corpus_unmapped": total_corpus_unmapped,
        "corpus_mapping_rate": round(corpus_rate, 2),
        "courses": course_summaries,
        "unmapped_records": detailed_unmapped_records,
        "reason_counts": dict(reason_counts),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit unmapped questions and mapping rates.")
    parser.add_argument("--course", help="Filter audit to a specific course canonical code or name.")
    parser.add_argument("--summary-only", action="store_true", help="Print only summary tables without paper-level lines.")
    parser.add_argument("--unmapped-only", action="store_true", help="Filter to courses with unmapped questions.")
    args = parser.parse_args()

    audit_corpus_mapping_quality(
        course_filter=args.course,
        summary_only=args.summary_only,
        unmapped_only=args.unmapped_only,
    )
