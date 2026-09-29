"""
Authoritative Forensic Diagnostic Tool for Remaining Unmapped Second-Year Questions (Phase 6.1).

Covers Semesters 3 & 4 (Courses 22, 24, 25, 26, 27, 28, 29, 30, 31).
Performs in-depth inspection of all unmapped questions:
1. Question & Exam Context (IDs, course, semester, assessment_type, year, track)
2. QuestionFamily Context (family_id, canonical_name, family members)
3. Classifier Diagnosis (confidence, method, evidence, guardrail rejections, candidate topics)
4. MCQ Dissection (stem vs options, stem proposal vs full proposal)
5. Sibling Analysis (mapped sibling questions in same family, sibling topics, difference analysis)
6. Forensic Categorization:
   - Category A: Genuine taxonomy gap (valid syllabus topic missing from taxonomy)
   - Category B: Existing topic, classifier rejection (narrow keyword, over-aggressive guard, MCQ distractor)
   - Category C: Ambiguous / multi-topic / collision
   - Category D: QuestionFamily sibling mapped (family consistency gap)
   - Category E: Insufficient / unclear / noisy
7. Structured export to data/s3_s4/unmapped_diagnostic_report.json
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

def diagnose_unmapped_questions(output_file: str = "data/s3_s4/unmapped_diagnostic_report.json") -> Dict[str, Any]:
    db = SessionLocal()
    registry = get_taxonomy_registry()

    report: Dict[str, Any] = {
        "metadata": {
            "title": "Phase 6.1 Second-Year Unmapped Question Forensic Audit",
            "courses_audited": SECOND_YEAR_COURSES,
        },
        "summary": {
            "total_questions": 0,
            "total_mapped": 0,
            "total_unmapped": 0,
            "category_counts": defaultdict(int),
            "by_course": {}
        },
        "questions": []
    }

    try:
        all_unmapped: List[Dict[str, Any]] = []

        for cid in SECOND_YEAR_COURSES:
            course = db.query(Course).filter(Course.id == cid).first()
            if not course:
                continue

            entry = registry.get_course(cid) if registry.has_course(cid) else None
            rules = registry.get_topic_rules(cid) if entry else []
            classifier = TaxonomyClassifierService(rules) if rules else None

            # Also instantiate classifier with distractor isolation to see what happens
            classifier_distractor_iso = TaxonomyClassifierService(rules, isolate_mcq_distractors=True) if rules else None

            # Get all questions for this course
            questions = (
                db.query(Question)
                .join(Section, Question.section_id == Section.id)
                .join(Exam, Section.exam_id == Exam.id)
                .filter(Exam.course_id == cid)
                .order_by(Question.id)
                .all()
            )

            total_c_q = len(questions)
            mapped_c_q = [q for q in questions if q.topics]
            unmapped_c_q = [q for q in questions if not q.topics]

            report["summary"]["total_questions"] += total_c_q
            report["summary"]["total_mapped"] += len(mapped_c_q)
            report["summary"]["total_unmapped"] += len(unmapped_c_q)

            course_cat_counts = defaultdict(int)

            # Pre-fetch all topics for this course for reference
            topics = (
                db.query(Topic)
                .join(Unit, Topic.unit_id == Unit.id)
                .join(Syllabus, Unit.syllabus_id == Syllabus.id)
                .filter(Syllabus.course_id == cid)
                .all()
            )
            topic_by_id = {t.id: t.name for t in topics}

            for q in unmapped_c_q:
                exam = q.section.exam
                stem, opts = TaxonomyClassifierService.split_stem_and_options(q.original_text)
                norm_full = TaxonomyClassifierService.normalize_text(q.original_text)
                norm_stem = TaxonomyClassifierService.normalize_text(stem) if opts else norm_full

                # Standard proposal
                prop = classifier.classify(q.id, q.original_text) if classifier else None
                # Distractor isolation proposal
                prop_iso = classifier_distractor_iso.classify(q.id, q.original_text) if classifier_distractor_iso else None
                # Stem-only proposal
                prop_stem = classifier.classify(q.id, stem) if (classifier and opts) else None

                # Family context & Sibling analysis
                qf = q.family
                siblings = []
                mapped_siblings = []
                if q.family_id:
                    siblings = (
                        db.query(Question)
                        .filter(Question.family_id == q.family_id, Question.id != q.id)
                        .all()
                    )
                    for sib in siblings:
                        if sib.topics:
                            mapped_siblings.append({
                                "sibling_id": sib.id,
                                "sibling_text": sib.original_text[:120],
                                "sibling_topics": [{"id": t.id, "name": t.name} for t in sib.topics],
                                "sibling_conf": (sib.classification_metadata or {}).get("confidence", "UNKNOWN"),
                                "sibling_method": (sib.classification_metadata or {}).get("method", "UNKNOWN")
                            })

                # Detailed classifier diagnosis
                guardrail_rejections = []
                candidate_topics = []
                if prop:
                    candidate_topics = prop.candidate_topics or []
                    if prop.method == "GUARDRAIL_REJECTED":
                        guardrail_rejections = prop.evidence

                # Categorization Decision
                category = "E_INSUFFICIENT"
                category_reason = ""

                # Check Insufficient first:
                if len(norm_full.split()) < 3 and not mapped_siblings:
                    category = "E_INSUFFICIENT"
                    category_reason = "Question text too short or uninformative (<3 words)"
                # Check QuestionFamily Sibling match (Category D)
                elif mapped_siblings:
                    category = "D_FAMILY_SIBLING_MAPPED"
                    sib_top_names = [st["name"] for ms in mapped_siblings for st in ms["sibling_topics"]]
                    category_reason = f"Belongs to family '{qf.canonical_name if qf else 'N/A'}' where sibling(s) mapped to: {', '.join(set(sib_top_names))}"
                # Check Ambiguous (Category C)
                elif prop and prop.confidence == "AMBIGUOUS":
                    category = "C_AMBIGUOUS_MULTI_TOPIC"
                    cand_names = [c.get("topic_name") for c in candidate_topics]
                    category_reason = f"Multiple plausible topics matched: {cand_names}"
                # Check Classifier Rejection / Negative guard / Distractor (Category B)
                elif prop and prop.method == "GUARDRAIL_REJECTED":
                    category = "B_EXISTING_TOPIC_REJECTED"
                    category_reason = f"Rejected by negative guardrail: {guardrail_rejections}"
                elif prop_iso and prop_iso.confidence in ["HIGH", "MEDIUM"]:
                    category = "B_EXISTING_TOPIC_REJECTED"
                    category_reason = f"Matches topic '{prop_iso.topic_name}' when MCQ distractors are isolated"
                elif prop_stem and prop_stem.confidence in ["HIGH", "MEDIUM"]:
                    category = "B_EXISTING_TOPIC_REJECTED"
                    category_reason = f"Stem-only matches topic '{prop_stem.topic_name}' ({prop_stem.method})"
                elif prop and prop.confidence in ["HIGH", "MEDIUM"]:
                    category = "B_EXISTING_TOPIC_REJECTED"
                    category_reason = f"Directly matches topic '{prop.topic_name}' with confidence {prop.confidence} (can be mapped directly)"
                else:
                    # Check if text matches keywords of existing course topics with relaxed boundary
                    matched_topic_hints = []
                    if rules:
                        for r in rules:
                            for sp in r.strong_phrases:
                                sp_norm = TaxonomyClassifierService.normalize_text(sp)
                                if sp_norm and sp_norm in norm_full:
                                    matched_topic_hints.append((r.topic_name, sp, "strong_phrase_partial"))
                            for kw in r.specific_keywords:
                                kw_norm = TaxonomyClassifierService.normalize_text(kw)
                                if kw_norm and kw_norm in norm_full:
                                    matched_topic_hints.append((r.topic_name, kw, "keyword_token"))

                    if matched_topic_hints:
                        # Group by topic
                        topics_hinted = set(h[0] for h in matched_topic_hints)
                        if len(topics_hinted) == 1:
                            category = "B_EXISTING_TOPIC_REJECTED"
                            category_reason = f"Vocabulary overlaps existing topic '{list(topics_hinted)[0]}': {[h[1] for h in matched_topic_hints[:3]]}"
                        else:
                            category = "C_AMBIGUOUS_MULTI_TOPIC"
                            category_reason = f"Partial vocabulary overlaps multiple topics: {list(topics_hinted)}"
                    else:
                        category = "A_GENUINE_TAXONOMY_GAP"
                        category_reason = "No vocabulary match with current course topics; represents missing syllabus topic or distinct subconcept"

                course_cat_counts[category] += 1
                report["summary"]["category_counts"][category] += 1

                q_entry = {
                    "question_id": q.id,
                    "course_id": cid,
                    "course_name": course.name,
                    "course_code": course.canonical_code or course.code,
                    "semester": course.semester,
                    "exam_id": exam.id,
                    "assessment_type": exam.assessment_type,
                    "year": exam.year,
                    "track_id": exam.track_id,
                    "question_type": q.question_type,
                    "marks": q.marks,
                    "text": q.original_text,
                    "has_mcq_options": bool(opts),
                    "stem": stem if opts else None,
                    "options": opts if opts else None,
                    "family": {
                        "family_id": q.family_id,
                        "canonical_name": qf.canonical_name if qf else None,
                        "total_siblings": len(siblings),
                        "mapped_siblings_count": len(mapped_siblings),
                        "mapped_siblings": mapped_siblings,
                    },
                    "classifier_diagnosis": {
                        "confidence": prop.confidence if prop else "UNMAPPED",
                        "method": prop.method if prop else "NO_CLASSIFIER",
                        "topic_id": prop.topic_id if prop else None,
                        "topic_name": prop.topic_name if prop else None,
                        "evidence": prop.evidence if prop else [],
                        "guardrail_rejections": guardrail_rejections,
                        "candidate_topics": candidate_topics,
                        "distractor_iso_proposal": {
                            "topic_name": prop_iso.topic_name if prop_iso else None,
                            "confidence": prop_iso.confidence if prop_iso else None,
                        } if prop_iso else None,
                        "stem_proposal": {
                            "topic_name": prop_stem.topic_name if prop_stem else None,
                            "confidence": prop_stem.confidence if prop_stem else None,
                        } if prop_stem else None,
                    },
                    "category": category,
                    "category_reason": category_reason,
                }
                all_unmapped.append(q_entry)

            report["summary"]["by_course"][cid] = {
                "course_name": course.name,
                "code": course.canonical_code,
                "total": total_c_q,
                "mapped": len(mapped_c_q),
                "unmapped": len(unmapped_c_q),
                "coverage_pct": round(len(mapped_c_q) / total_c_q * 100, 1) if total_c_q else 0.0,
                "categories": dict(course_cat_counts)
            }

        report["questions"] = all_unmapped
        report["summary"]["category_counts"] = dict(report["summary"]["category_counts"])

        # Write to JSON
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 90)
        print("PHASE 6.1 SECOND-YEAR UNMAPPED QUESTION FORENSIC DIAGNOSTIC REPORT")
        print("=" * 90)
        print(f"Total Questions Analyzed: {report['summary']['total_questions']}")
        print(f"Total Mapped:            {report['summary']['total_mapped']} ({report['summary']['total_mapped']/report['summary']['total_questions']*100:.1f}%)")
        print(f"Total Unmapped:          {report['summary']['total_unmapped']} ({report['summary']['total_unmapped']/report['summary']['total_questions']*100:.1f}%)")
        print("-" * 90)
        print("Category Breakdown:")
        for cat, cnt in sorted(report["summary"]["category_counts"].items()):
            pct = cnt / report['summary']['total_unmapped'] * 100 if report['summary']['total_unmapped'] else 0
            print(f"  {cat:<35}: {cnt:>4} ({pct:>5.1f}%)")
        print("-" * 90)
        print("Course-by-Course Breakdown:")
        print(f"{'Course':<36} | {'Total':<5} | {'Mapped':<6} | {'Unmapped':<8} | {'Cov%':<6} | {'Cat A':<5} | {'Cat B':<5} | {'Cat C':<5} | {'Cat D':<5} | {'Cat E':<5}")
        print("-" * 100)
        for cid, cs in report["summary"]["by_course"].items():
            cats = cs["categories"]
            print(f"{cs['course_name'][:34]:<36} | {cs['total']:<5} | {cs['mapped']:<6} | {cs['unmapped']:<8} | {cs['coverage_pct']:<5}% | {cats.get('A_GENUINE_TAXONOMY_GAP', 0):<5} | {cats.get('B_EXISTING_TOPIC_REJECTED', 0):<5} | {cats.get('C_AMBIGUOUS_MULTI_TOPIC', 0):<5} | {cats.get('D_FAMILY_SIBLING_MAPPED', 0):<5} | {cats.get('E_INSUFFICIENT', 0):<5}")
        print("=" * 90)
        print(f"Diagnostic report exported to: {output_file}\n")

        return report

    finally:
        db.close()

if __name__ == "__main__":
    diagnose_unmapped_questions()
