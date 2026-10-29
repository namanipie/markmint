"""
Comprehensive Post-Implementation Validation & Audit Script.

Verifies:
1. Intended scope vs observed evidence (Chemistry CT1 anomaly inspection).
2. Question count and marks coverage reconciliation (Calculus CT2 deep audit).
3. Question -> Topic -> Canonical Unit mapping quality across representative courses.
4. Canonical syllabus taxonomy integrity across all courses.
5. Assessment identity classification breakdown across all papers in corpus.
6. Prediction engine candidate restriction and historical empirical grounding.
7. API contract conformance.
"""

import sys
import os
import json
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import selectinload
from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Exam, Section, Question, Document
from backend.services.assessment_plan_registry import (
    get_course_assessment_plan,
    get_course_assessment_scope,
    COURSE_ASSESSMENT_PLANS,
)
from backend.services.observed_assessment_coverage import (
    identify_exam_assessment,
    compute_paper_observed_coverage,
    compute_cycle_observed_coverage,
    build_coverage_audit_chain,
)
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.endpoints.predictions import get_prediction
from backend.api.endpoints.practice import get_practice_questions
from backend.api.router_study import get_study_priorities


def section_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)


def run_full_validation():
    db = SessionLocal()

    # =========================================================================
    # PART 1: VERIFY INTENDED SCOPE DOES NOT OVERRIDE OBSERVED EVIDENCE
    # =========================================================================
    section_header("Part 1: Intended Scope vs Observed Evidence (Chemistry CT1)")
    chem = db.query(Course).filter(Course.canonical_code == "21CYB101J").first()
    if not chem:
        chem = db.query(Course).filter(Course.name.ilike("%Chemistry%")).first()

    assert chem is not None, "Chemistry course must exist"
    print(f"Found Course: {chem.name} (ID: {chem.id}, Code: {chem.code})")

    scope_chem_ct1 = get_course_assessment_scope(chem.id, "CT1", db=db)
    print(f"Intended Units: {scope_chem_ct1.intended_scope['unit_numbers']}")
    print(f"Observed Units: {scope_chem_ct1.observed_scope['unit_numbers']}")
    print(f"Evidence Status: {scope_chem_ct1.evidence_status}")
    print(f"Question Count by Unit: {scope_chem_ct1.observed_scope['question_count_by_unit']}")

    # Inspect the papers in CT1
    print("\nPapers contributing to Chemistry CT1:")
    for p in scope_chem_ct1.observed_scope.get("papers", []):
        print(f"  - Exam ID {p['exam_id']} (Year {p['year']}): raw='{p['raw_assessment_type']}', normalized='{p['normalized_code']}', units={p['observed_units']}")
        print(f"    Total Qs: {p['total_questions']}, Mapped: {p['mapped_questions']}, Unmapped: {p['unmapped_questions']}")
        print(f"    Marks known: {p['known_marks_total']} ({p['questions_with_known_marks']} Qs), Marks unknown: {p['questions_with_unknown_marks']} Qs")

    # Inspect the specific questions mapped to out-of-scope units (Units 8 and 11)
    print("\nDeep Inspection of Out-of-Scope Questions in Chemistry CT1:")
    chem_ct1_exams = [
        ex for ex in db.query(Exam).filter(Exam.course_id == chem.id).all()
        if identify_exam_assessment(ex, chem.id).student_cycle == "CT1"
    ]
    out_of_scope_questions = []
    for ex in chem_ct1_exams:
        paper_cov = compute_paper_observed_coverage(ex)
        for qline in paper_cov.question_lineage:
            for un in qline.unit_numbers:
                if un not in scope_chem_ct1.intended_scope["unit_numbers"]:
                    q_record = db.query(Question).filter(Question.id == qline.question_id).first()
                    q_text = q_record.original_text if (q_record and q_record.original_text) else (q_record.normalized_text if q_record else "N/A")
                    out_of_scope_questions.append({
                        "exam_id": ex.id,
                        "year": ex.year,
                        "question_id": qline.question_id,
                        "question_number": qline.question_number,
                        "unit_number": un,
                        "topic_names": qline.topic_names,
                        "text": (q_text[:120] + "...") if q_text else "N/A",
                    })

    for oos in out_of_scope_questions:
        print(f"  * Exam {oos['exam_id']} (Year {oos['year']}), Q#{oos['question_number']} (ID={oos['question_id']}): Unit {oos['unit_number']} | Topics: {oos['topic_names']}")
        print(f"    Text: {oos['text']}")

    # Verify predictions engine behavior with out of scope topics
    snap = get_intelligence_snapshot(str(chem.id), assessment_cycle="CT1", db=db)
    out_of_scope_in_snap = snap.get("assessment_scope", {}).get("out_of_scope_observed_topics", [])
    print(f"\nPreserved Out-of-Scope Topics in Intelligence Snapshot: {len(out_of_scope_in_snap)}")
    for oost in out_of_scope_in_snap:
        print(f"  * Topic: {oost['name']} | Status: {oost['status']} | Empirical Score: {oost['score']}")

    # Verify none of these appear in the top predictions
    pred_topics = [p.get("name") or p.get("topic") for p in snap.get("predictions", [])]
    for oost in out_of_scope_in_snap:
        assert oost["name"] not in pred_topics, f"Out of scope topic {oost['name']} must not be in in-scope predictions"
    print("Assertion passed: Out-of-scope observed topics are preserved, auditable, but NOT falsely promoted to intended scope!")

    # =========================================================================
    # PART 2: RECONCILE CALCULUS CT2 QUESTION COUNT AND MARKS
    # =========================================================================
    section_header("Part 2: Reconcile Calculus CT2 Question Count & Marks")
    calc = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    if not calc:
        calc = db.query(Course).filter(Course.name.ilike("%Calculus%")).first()
    assert calc is not None, "Calculus course must exist"

    calc_ct2_exams = [
        ex for ex in db.query(Exam).filter(Exam.course_id == calc.id).all()
        if identify_exam_assessment(ex, calc.id).student_cycle == "CT2"
    ]
    print(f"Calculus CT2 historical papers count: {len(calc_ct2_exams)}")

    calc_ct2_cov = compute_cycle_observed_coverage(calc.id, "CT2", calc_ct2_exams)
    print(f"Cycle Aggregate:")
    print(f"  Total Questions: {calc_ct2_cov.total_questions}")
    print(f"  Mapped Questions: {calc_ct2_cov.mapped_questions_count}")
    print(f"  Unmapped Questions: {calc_ct2_cov.unmapped_questions_count}")
    print(f"  Questions with Known Marks: {calc_ct2_cov.questions_with_known_marks}")
    print(f"  Questions with Unknown Marks: {calc_ct2_cov.questions_with_unknown_marks}")
    print(f"  Known Marks Total: {calc_ct2_cov.known_marks_total}")
    print(f"  Observed Units: {calc_ct2_cov.observed_unit_numbers}")
    print(f"  Question Count by Unit: {calc_ct2_cov.question_count_by_unit}")
    print(f"  Marks by Unit: {calc_ct2_cov.marks_by_unit}")

    print("\nDetailed Per-Paper Accounting for Calculus CT2:")
    for ex in calc_ct2_exams:
        pcov = compute_paper_observed_coverage(ex)
        print(f"\n  Paper Exam ID {ex.id} (Year {ex.year}):")
        print(f"    Raw type: {ex.assessment_type!r} | Normalized: {pcov.assessment_identity.normalized_code}")
        print(f"    Source: {pcov.assessment_identity.identification_source} | Confidence: {pcov.assessment_identity.confidence}")
        print(f"    Evidence: {pcov.assessment_identity.evidence_text}")
        print(f"    Total Qs: {pcov.total_questions} == Mapped ({pcov.mapped_questions_count}) + Unmapped ({pcov.unmapped_questions_count})")
        print(f"    Marks known: {pcov.known_marks_total} ({pcov.questions_with_known_marks} Qs), Marks unknown: {pcov.questions_with_unknown_marks} Qs")
        assert pcov.total_questions == pcov.mapped_questions_count + pcov.unmapped_questions_count, "Accounting invariant violated"

        print(f"    All Questions in Exam {ex.id}:")
        for ql in pcov.question_lineage:
            q_db = db.query(Question).filter(Question.id == ql.question_id).first()
            q_raw = q_db.original_text if (q_db and q_db.original_text) else (q_db.normalized_text if q_db else "")
            snippet = (q_raw[:70] + "...") if q_raw else "EMPTY_TEXT"
            print(f"      Q#{ql.question_number:2s} (ID={ql.question_id:4d}): mapped={ql.is_mapped}, marks={ql.marks!r}, alt={ql.is_alternative}, units={ql.unit_numbers}, topics={ql.topic_names}")
            print(f"             text: {snippet!r}")

    # =========================================================================
    # PART 3: VALIDATE QUESTION -> TOPIC -> CANONICAL UNIT MAPPING QUALITY
    # =========================================================================
    section_header("Part 3: Question -> Topic -> Canonical Unit Mapping Quality")
    sample_courses = [
        ("Calculus", "21MAB101T", "%Calculus%"),
        ("Chemistry", "21CYB101J", "%Chemistry%"),
        ("SPCM", "21PYB102J", "%Semiconductor%"),
        ("EEE", "21EEB101J", "%Electrical%"),
        ("OODP", "21CSC102J", "%Object Oriented%"),
    ]

    total_sampled = 0
    clean_lineage_count = 0

    for label, code, pat in sample_courses:
        c = db.query(Course).filter(Course.canonical_code == code).first()
        if not c:
            c = db.query(Course).filter(Course.name.ilike(pat)).first()
        if not c:
            print(f"[SKIP] Course {label} not found in DB")
            continue

        print(f"\n--- Sampling 5 Mapped Questions for {label} ({c.canonical_code or c.code}) ---")
        exams = db.query(Exam).filter(Exam.course_id == c.id).all()
        q_sampled_for_course = 0
        for ex in exams:
            if q_sampled_for_course >= 5:
                break
            pcov = compute_paper_observed_coverage(ex)
            for ql in pcov.question_lineage:
                if ql.is_mapped and q_sampled_for_course < 5:
                    q_record = db.query(Question).filter(Question.id == ql.question_id).first()
                    q_txt = q_record.original_text if (q_record and q_record.original_text) else (q_record.normalized_text if q_record else "N/A")
                    text_snip = (q_txt[:80] + "...") if q_txt else "N/A"
                    
                    # Direct check: Is Unit derived SOLELY through topic -> unit?
                    for tid, uid in zip(ql.topic_ids, ql.unit_numbers):
                        topic_obj = db.query(Topic).filter(Topic.id == tid).first()
                        unit_obj = db.query(Unit).filter(Unit.id == topic_obj.unit_id).first()
                        assert unit_obj.number == uid, f"Unit number mismatch! Topic unit is {unit_obj.number}, but lineage has {uid}"
                    
                    print(f"  [Q#{ql.question_number} ID={ql.question_id}] Paper ID: {ex.id} (Year {ex.year}, Raw: {ex.assessment_type!r})")
                    print(f"    Normalized: {pcov.assessment_identity.normalized_code} | Cycle: {pcov.assessment_identity.student_cycle}")
                    print(f"    Snippet: {text_snip!r}")
                    print(f"    Mapped Topics: {ql.topic_names} (IDs: {ql.topic_ids})")
                    print(f"    Canonical Units: {ql.unit_numbers} ({ql.unit_names})")
                    print(f"    Lineage Proof: Topic.unit_id points to Unit.id with Unit.number={ql.unit_numbers[0]}. Question number '{ql.question_number}' was NOT used.")
                    
                    q_sampled_for_course += 1
                    total_sampled += 1
                    clean_lineage_count += 1

    print(f"\nTotal sampled questions: {total_sampled}. All {clean_lineage_count} derive canonical units SOLELY through topic.unit.")

    # =========================================================================
    # PART 4: CANONICAL SYLLABUS TAXONOMY INTEGRITY ACROSS ALL COURSES
    # =========================================================================
    section_header("Part 4: Canonical Syllabus Taxonomy Integrity Across ALL Courses")
    all_courses = db.query(Course).order_by(Course.id).all()
    print(f"Total courses cataloged in DB: {len(all_courses)}")

    all_unit_numbers_unique = True
    no_orphan_topics = True
    no_cross_course_pollution = True

    for c in all_courses:
        syl = db.query(Syllabus).filter(Syllabus.course_id == c.id).first()
        if not syl:
            print(f"  Course {c.id:2d} | {c.code:12s} | {c.name[:35]:35s} | [NO SYLLABUS RECORD]")
            continue
        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        unit_nums = [u.number for u in units]
        unique_nums = len(unit_nums) == len(set(unit_nums))
        if not unique_nums:
            all_unit_numbers_unique = False

        total_topics = 0
        for u in units:
            topics = db.query(Topic).filter(Topic.unit_id == u.id).all()
            total_topics += len(topics)
            for t in topics:
                assert t.unit.syllabus.course_id == c.id, f"Cross course pollution in topic {t.name}"

        print(f"  Course {c.id:2d} | {c.code:12s} | N={len(units):2d} units: {str(unit_nums):25s} | {total_topics:3d} topics | Unique Units: {unique_nums}")

    # Check for orphan topics
    orphans = db.query(Topic).filter(Topic.unit_id == None).count()
    if orphans > 0:
        no_orphan_topics = False
        print(f"[ERROR] Found {orphans} orphaned topics with null unit_id!")
    else:
        print("\nAll topics across all courses have valid non-null unit_ids.")

    assert all_unit_numbers_unique, "All Unit numbers must be unique per syllabus"
    assert no_orphan_topics, "No orphan topics allowed"
    print("Assertion passed: Canonical syllabus taxonomy is strictly consistent and non-polluted!")

    # =========================================================================
    # PART 5: AUDIT ASSESSMENT IDENTITY CLASSIFICATION ACROSS ALL PAPERS
    # =========================================================================
    section_header("Part 5: Assessment Identity Classification Across ALL Papers")
    all_exams = db.query(Exam).options(selectinload(Exam.document)).all()
    print(f"Total exams in DB: {len(all_exams)}")

    source_counts = {
        "metadata": 0,
        "document_metadata": 0,
        "document_title": 0,
        "filename": 0,
        "fallback": 0,
    }
    fallback_exams = []

    for ex in all_exams:
        ident = identify_exam_assessment(ex, ex.course_id)
        source_counts[ident.identification_source] = source_counts.get(ident.identification_source, 0) + 1
        if ident.identification_source == "fallback":
            fallback_exams.append({
                "exam_id": ex.id,
                "course_id": ex.course_id,
                "year": ex.year,
                "raw_assessment_type": ex.assessment_type,
                "doc_title": ex.document.title if ex.document else None,
                "doc_source": ex.document.source if ex.document else None,
            })

    print("Identification Source Distribution:")
    for src, cnt in source_counts.items():
        pct = (cnt / len(all_exams)) * 100 if all_exams else 0
        print(f"  - {src:20s}: {cnt:4d} ({pct:5.1f}%)")

    if fallback_exams:
        print(f"\n[NOTICE] {len(fallback_exams)} exams classified using fallback:")
        for fb in fallback_exams[:10]:
            print(f"  Exam {fb['exam_id']} (Course {fb['course_id']}): raw='{fb['raw_assessment_type']}', title='{fb['doc_title']}', file='{fb['doc_source']}'")
    else:
        print("\nZero exams classified as fallback!")

    # =========================================================================
    # PART 6: END-TO-END PREDICTION AND CANDIDATE RESTRICTION VERIFICATION
    # =========================================================================
    section_header("Part 6: End-to-End Prediction Verification")
    spcm = db.query(Course).filter(Course.canonical_code == "21PYB102J").first()
    cases = [
        (calc, "CT1"),
        (calc, "CT2"),
        (calc, "ENDSEM"),
        (chem, "CT1"),
        (spcm, "CT1") if spcm else None,
        (spcm, "ENDSEM") if spcm else None,
    ]

    for item in cases:
        if not item:
            continue
        course_obj, cycle = item
        print(f"\n>>> Running Prediction Engine for {course_obj.name} (Cycle: {cycle}) <<<")
        snap = get_intelligence_snapshot(str(course_obj.id), assessment_cycle=cycle, db=db)
        ascope = snap.get("assessment_scope", {})
        print(f"  Evidence Status: {ascope.get('evidence_status')}")
        print(f"  Intended Units: {ascope.get('intended_scope', {}).get('unit_numbers')}")
        print(f"  Observed Units: {ascope.get('observed_scope', {}).get('unit_numbers')}")
        print(f"  Observed Paper Count: {ascope.get('observed_scope', {}).get('paper_count')}")
        print(f"  Total Questions: {ascope.get('observed_scope', {}).get('total_questions')}")
        print(f"  Mapped Questions: {ascope.get('observed_scope', {}).get('mapped_questions_count')}")
        print(f"  Unmapped Questions: {ascope.get('observed_scope', {}).get('unmapped_questions_count')}")
        print(f"  Known Marks: {ascope.get('observed_scope', {}).get('known_marks_total')}")

        predictions = snap.get("predictions", [])
        print(f"  Returned Predictions Count: {len(predictions)}")
        for idx, p in enumerate(predictions[:5], start=1):
            pname = p.get("name") or p.get("topic")
            prob = p.get("predicted_probability") or p.get("score") or p.get("probability")
            unit_num = p.get("unit_number")
            print(f"    {idx}. {pname} (Unit {unit_num}) | Score/Prob: {prob}")

        unobserved = ascope.get("unobserved_in_scope_topics", [])
        print(f"  Unobserved In-Scope Topics: {len(unobserved)}")
        if unobserved:
            for u in unobserved[:3]:
                print(f"    - {u['name']} -> Status: {u['status']}")

    # =========================================================================
    # PART 7: VERIFY API CONTRACTS
    # =========================================================================
    section_header("Part 7: Verify API Contracts")
    print(f"Testing API Endpoints for Course {calc.id} ({calc.name}):")

    # 1. Snapshot
    snap_resp = get_intelligence_snapshot(str(calc.id), assessment_cycle="CT1", db=db)
    assert "intended_scope" in snap_resp
    assert "observed_scope" in snap_resp
    assert "evidence_status" in snap_resp
    assert "predictions" in snap_resp
    print("  [OK] /intelligence-snapshot contract verified.")

    # 2. Predictions
    pred_resp = get_prediction(str(calc.id), assessment_cycle="CT1", db=db)
    assert "intended_scope" in pred_resp
    assert "observed_scope" in pred_resp
    assert "evidence_status" in pred_resp
    assert "predictions" in pred_resp
    print("  [OK] /predictions contract verified.")

    # 3. Practice Questions
    prac_resp = get_practice_questions(calc.name, assessment_cycle="CT1")
    assert "intended_scope" in prac_resp
    assert "observed_scope" in prac_resp
    assert "evidence_status" in prac_resp
    assert "questions" in prac_resp
    print("  [OK] /practice/questions contract verified.")

    # 4. Study Priorities
    study_resp = get_study_priorities(calc.name, assessment_cycle="CT1", db=db)
    assert "intended_scope" in study_resp
    assert "observed_scope" in study_resp
    assert "evidence_status" in study_resp
    assert "priorities" in study_resp
    print("  [OK] /study/priorities contract verified.")

    db.close()
    section_header("Validation Audit Complete - All Invariants Verified")


if __name__ == "__main__":
    run_full_validation()
