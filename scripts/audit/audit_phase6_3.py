"""
Phase 6.3 Forensic Precision Audit & Ambiguity Validation Tool.

Analyzes all remaining unmapped second-year questions (Semesters 3 & 4) across:
- Probability & Statistics (22)
- Data Structures & Algorithms (24)
- Operating Systems (25)
- Computer Organization & Architecture (26)
- Design & Analysis of Algorithms (27)
- Database Management Systems (28)
- Artificial Intelligence (29)
- Transforms and Boundary Value Problems (30)
- Probability and Queueing Theory (31)

Categorizes every question into A/B/C/D/E and validates Category C questions as:
- AMBIGUOUS_CORRECT: genuine multi-topic comparison, multi-part, or OR questions
- FALSE_AMBIGUITY: one primary topic was intended, competing match is spurious
"""
import os
import sys
import json
import re
from collections import defaultdict
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus, QuestionFamily, QuestionFamilyMembership, question_topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService, ClassificationProposal

SECOND_YEAR_COURSES = [22, 24, 25, 26, 27, 28, 29, 30, 31]

def run_phase6_3_audit() -> Dict[str, Any]:
    db = SessionLocal()
    registry = get_taxonomy_registry()

    report: Dict[str, Any] = {
        "metadata": {
            "title": "Phase 6.3 Unmapped Precision Audit & Ambiguity Validation",
            "courses_audited": SECOND_YEAR_COURSES,
        },
        "summary": {
            "total_second_year_questions": 0,
            "total_mapped": 0,
            "total_unmapped": 0,
            "coverage_pct": 0.0,
            "category_counts": defaultdict(int),
            "category_c_validation": {
                "total_ambiguous": 0,
                "ambiguous_correct": 0,
                "false_ambiguity": 0
            },
            "by_course": {}
        },
        "ambiguous_validations": [],
        "unmapped_questions": []
    }

    try:
        # 1. First, fetch all sibling mappings for second-year questions
        all_sy_q = (
            db.query(Question.id, Question.family_id, Exam.course_id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id.in_(SECOND_YEAR_COURSES))
            .all()
        )
        report["summary"]["total_second_year_questions"] = len(all_sy_q)

        family_ids = [q[1] for q in all_sy_q if q[1] is not None]
        
        # Mapped questions across all families
        mapped_rows = (
            db.query(Question.id, Question.family_id, Topic.id, Topic.name)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .filter(Question.family_id.in_(family_ids))
            .all()
        )
        family_sibling_mappings = defaultdict(list)
        for q_id, fam_id, top_id, top_name in mapped_rows:
            family_sibling_mappings[fam_id].append({
                "question_id": q_id,
                "topic_id": top_id,
                "topic_name": top_name
            })

        for cid in SECOND_YEAR_COURSES:
            course = db.query(Course).filter(Course.id == cid).first()
            if not course:
                continue

            entry = registry.get_course(cid) if registry.has_course(cid) else None
            rules = registry.get_topic_rules(cid) if entry else []
            classifier = TaxonomyClassifierService(rules, isolate_mcq_distractors=True) if rules else None

            # Get all questions for this course
            questions = (
                db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .filter(Exam.course_id == cid)
                .order_by(Question.id)
                .all()
            )

            total_c = len(questions)
            mapped_c = [q for q in questions if q.topics]
            unmapped_c = [q for q in questions if not q.topics]

            report["summary"]["total_mapped"] += len(mapped_c)
            report["summary"]["total_unmapped"] += len(unmapped_c)

            course_summary = {
                "course_id": cid,
                "course_name": course.name,
                "course_code": course.canonical_code or course.code,
                "total_questions": total_c,
                "mapped_questions": len(mapped_c),
                "unmapped_questions": len(unmapped_c),
                "coverage_pct": round(len(mapped_c) / total_c * 100, 1) if total_c else 0.0,
                "cat_a": 0, "cat_b": 0, "cat_c": 0, "cat_d": 0, "cat_e": 0,
                "cat_c_correct": 0,
                "cat_c_false_ambiguity": 0
            }

            for q in unmapped_c:
                exam = q.section.exam
                stem, opts = TaxonomyClassifierService.split_stem_and_options(q.original_text)
                is_mcq = bool(opts)

                # Classify question
                prop = classifier.classify(q.id, q.original_text) if classifier else None

                # Sibling analysis
                fam_id = q.family_id
                fam_siblings = family_sibling_mappings.get(fam_id, [])
                mapped_siblings = [s for s in fam_siblings if s["question_id"] != q.id]

                # Categorize
                category = "A"
                rejection_reason = ""
                ambiguity_validation = None

                if prop and prop.confidence == "AMBIGUOUS":
                    category = "C"
                    rejection_reason = f"Ambiguous candidates: {[c['topic_name'] for c in prop.candidate_topics]}"
                    
                    # Detailed Forensic Ambiguity Validation
                    cand_names = [c["topic_name"] for c in prop.candidate_topics]
                    cand_ids = [c["topic_id"] for c in prop.candidate_topics]
                    norm_text = q.original_text.lower()
                    norm_stem = stem.lower() if stem else norm_text

                    # Detection of genuine multi-topic patterns:
                    is_comparison = bool(re.search(r'\b(compare|contrast|difference between|differentiate|distinguish between|vs\.?|versus)\b', norm_stem))
                    is_multi_part = bool(re.search(r'(\([a-d]\)|\b[a-d]\.\s|\b[ivx]+\.\s|\([ivx]+\)|\bpart\s+[ab]\b|subquestions)', norm_text))
                    is_or_choice = bool(re.search(r'---\s*or\s*---|[\r\n]\s*or\s*[\r\n]|\(or\)', norm_text))

                    # Check if knowledge of both topics is required or if one is clearly a false match
                    # A match is false ambiguity if one candidate has high evidence in stem and the other
                    # candidate is only in an option distractor, or is a broad parent topic that matched a single generic word.
                    evidence_by_cand = {c["topic_id"]: c["evidence"] for c in prop.candidate_topics}
                    
                    # Does one topic have stem-level canonical evidence while others have only distractor evidence?
                    stem_ev_cands = []
                    option_only_cands = []
                    for c in prop.candidate_topics:
                        ev_list = c.get("evidence", [])
                        in_stem = any(ev.lower() in norm_stem for ev in ev_list)
                        if in_stem:
                            stem_ev_cands.append(c["topic_id"])
                        else:
                            option_only_cands.append(c["topic_id"])

                    # Detection of cross-paradigm problem selection:
                    is_paradigm_classification = bool(re.search(r'\b(cannot be solved by|cannot be solved using|can be solved using|solved using dynamic programming)\b', norm_stem))
                    is_composite_and = bool(re.search(r'\b(and also|and find|then find|also test)\b', norm_stem))

                    if is_comparison or is_or_choice:
                        amb_classification = "AMBIGUOUS_CORRECT"
                        amb_reason = "Explicit comparison or alternative (OR) across distinct syllabus topics"
                    elif is_multi_part or is_composite_and:
                        amb_classification = "AMBIGUOUS_CORRECT"
                        amb_reason = "Multi-part or composite question spanning multiple distinct syllabus concepts"
                    elif is_paradigm_classification:
                        amb_classification = "AMBIGUOUS_CORRECT"
                        amb_reason = "Cross-paradigm algorithmic selection testing applicability across multiple topic paradigms"
                    elif len(stem_ev_cands) == 1 and len(option_only_cands) >= 1 and is_mcq:
                        amb_classification = "FALSE_AMBIGUITY"
                        primary_tid = stem_ev_cands[0]
                        primary_name = [c["topic_name"] for c in prop.candidate_topics if c["topic_id"] == primary_tid][0]
                        amb_reason = f"MCQ distractor infiltration; primary question belongs to {primary_name}"
                    else:
                        # Check whether topics belong to different units
                        cand_units = set(c.get("unit_id") for c in prop.candidate_topics if "unit_id" in c)
                        if len(cand_units) > 1 and (is_multi_part or " and " in norm_stem):
                            amb_classification = "AMBIGUOUS_CORRECT"
                            amb_reason = "Question spans topics across distinct syllabus units"
                        else:
                            # Further inspect candidate evidence strength
                            high_cands = [c for c in prop.candidate_topics if c.get("level") == "HIGH"]
                            if len(high_cands) == 1 and len(prop.candidate_topics) > 1:
                                amb_classification = "FALSE_AMBIGUITY"
                                amb_reason = f"Single HIGH-confidence candidate: {high_cands[0]['topic_name']}"
                            else:
                                amb_classification = "AMBIGUOUS_CORRECT"
                                amb_reason = "Multiple competing topics equally supported by question text"

                    ambiguity_validation = {
                        "question_id": q.id,
                        "course_id": cid,
                        "course_name": course.name,
                        "text": q.original_text,
                        "stem": stem,
                        "options": opts,
                        "competing_topics": prop.candidate_topics,
                        "is_comparison": is_comparison,
                        "is_multi_part": is_multi_part,
                        "is_or_choice": is_or_choice,
                        "classification": amb_classification,
                        "rationale": amb_reason
                    }
                    report["ambiguous_validations"].append(ambiguity_validation)
                    if amb_classification == "AMBIGUOUS_CORRECT":
                        report["summary"]["category_c_validation"]["ambiguous_correct"] += 1
                        course_summary["cat_c_correct"] += 1
                    else:
                        report["summary"]["category_c_validation"]["false_ambiguity"] += 1
                        course_summary["cat_c_false_ambiguity"] += 1
                    report["summary"]["category_c_validation"]["total_ambiguous"] += 1

                elif mapped_siblings:
                    category = "D"
                    rejection_reason = f"Unmapped while siblings mapped to: {[s['topic_name'] for s in mapped_siblings]}"
                elif prop and prop.method == "GUARDRAIL_REJECTED":
                    category = "B"
                    rejection_reason = f"Rejected by guardrails: {prop.evidence}"
                elif not q.original_text or len(q.original_text.strip()) < 15:
                    category = "E"
                    rejection_reason = "Insufficient / noisy / low text length"
                else:
                    category = "A"
                    rejection_reason = "No matching topic rules or canonical phrases"

                course_summary[f"cat_{category.lower()}"] += 1
                report["summary"]["category_counts"][category] += 1

                q_record = {
                    "question_id": q.id,
                    "course_id": cid,
                    "course_code": course.canonical_code or course.code,
                    "course_name": course.name,
                    "semester": exam.semester if hasattr(exam, "semester") else None,
                    "exam_id": exam.id,
                    "exam_year": exam.year if hasattr(exam, "year") else None,
                    "assessment_type": exam.assessment_type if hasattr(exam, "assessment_type") else None,
                    "track_id": exam.track_id if hasattr(exam, "track_id") else None,
                    "family_id": q.family_id,
                    "family_name": q.family.canonical_name if q.family else None,
                    "original_text": q.original_text,
                    "stem": stem,
                    "is_mcq": is_mcq,
                    "classifier_proposal": prop.to_dict() if prop else None,
                    "diagnostic_category": category,
                    "rejection_reason": rejection_reason,
                    "sibling_family_questions_mapped": bool(mapped_siblings),
                    "sibling_mapped_topics": mapped_siblings,
                    "ambiguity_validation": ambiguity_validation
                }
                report["unmapped_questions"].append(q_record)

            report["summary"]["by_course"][cid] = course_summary

        if report["summary"]["total_second_year_questions"] > 0:
            report["summary"]["coverage_pct"] = round(
                report["summary"]["total_mapped"] / report["summary"]["total_second_year_questions"] * 100, 1
            )

        out_path = os.path.join(BASE_DIR, "data", "s3_s4", "phase6_3_audit_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("=" * 80)
        print("PHASE 6.3 UNMAPPED QUESTION PRECISION AUDIT & AMBIGUITY VALIDATION")
        print("=" * 80)
        print(f"Total Second-Year Questions: {report['summary']['total_second_year_questions']}")
        print(f"Total Mapped:               {report['summary']['total_mapped']} ({report['summary']['coverage_pct']}%)")
        print(f"Total Unmapped:             {report['summary']['total_unmapped']}")
        print("-" * 80)
        print("Category Breakdown:")
        for cat, cnt in sorted(report["summary"]["category_counts"].items()):
            print(f"  Category {cat}: {cnt:3d} ({cnt / report['summary']['total_unmapped'] * 100:.1f}%)")
        print("-" * 80)
        c_val = report["summary"]["category_c_validation"]
        print(f"Category C Ambiguity Validation (Total: {c_val['total_ambiguous']}):")
        print(f"  AMBIGUOUS_CORRECT (True Multi-Topic / Composite): {c_val['ambiguous_correct']}")
        print(f"  FALSE_AMBIGUITY   (Resolvable Collisions)       : {c_val['false_ambiguity']}")
        print("-" * 80)
        print(f"Report exported to: {out_path}")
        print("=" * 80)

        return report

    finally:
        db.close()

if __name__ == "__main__":
    run_phase6_3_audit()
