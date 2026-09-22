"""
Representative Audit Script: Paper-Derived Assessment Scope & Coverage.

Audits representative MarkMint courses resolved dynamically by canonical code/name:
- 21MAB101T Calculus And Linear Algebra
- 21CYB101J Chemistry
- SPCM (Semiconductor Physics and Computational Methods)
- 21EEB101J EEE (Electrical and Electronics Engineering)
- 21CSC102J OODP (Object Oriented Design and Programming)

Outputs for each course:
- Canonical course metadata & resolved course_id
- Canonical syllabus units (from Syllabus authority)
- Historical exam papers
- Raw assessment type vs normalized assessment
- Assessment identification source & confidence
- Total, mapped, and unmapped questions per paper
- Paper-derived observed units and topics
- Authoritative intended scope (if documented)
- Out-of-intended-scope paper observations (anomalies)
- Paper-level auditability provenance
"""

import sys
import os
from typing import List, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import selectinload
from backend.core.database import SessionLocal
from backend.models.core import Course, Syllabus, Unit, Topic, Exam, Section, Question
from backend.services.assessment_plan_registry import get_course_assessment_plan
from backend.services.observed_assessment_coverage import (
    identify_exam_assessment,
    compute_paper_observed_coverage,
    compute_cycle_observed_coverage,
    build_coverage_audit_chain,
)


COURSE_QUERIES = [
    {"label": "Calculus", "canonical_code": "21MAB101T", "name_pattern": "%Calculus%"},
    {"label": "Chemistry", "canonical_code": "21CYB101J", "name_pattern": "%Chemistry%"},
    {"label": "SPCM", "canonical_code": "21PYB102J", "name_pattern": "%Semiconductor%"},
    {"label": "EEE", "canonical_code": "21EEB101J", "name_pattern": "%Electrical%"},
    {"label": "OODP", "canonical_code": "21CSC102J", "name_pattern": "%Object Oriented%"},
]


def resolve_course(db, query_def) -> Optional[Course]:
    """Resolves a course dynamically by canonical_code or name pattern. Never assumes a numeric ID."""
    course = None
    if query_def.get("canonical_code"):
        course = db.query(Course).filter(Course.canonical_code == query_def["canonical_code"]).first()
    if not course and query_def.get("name_pattern"):
        course = db.query(Course).filter(Course.name.ilike(query_def["name_pattern"])).first()
    return course


def audit_representative_courses():
    db = SessionLocal()
    print("=" * 80)
    print("MARKMINT REPRESENTATIVE AUDIT: PAPER-DERIVED ASSESSMENT SCOPE")
    print("=" * 80)

    for qdef in COURSE_QUERIES:
        course = resolve_course(db, qdef)
        if not course:
            print(f"\n[ERROR] Course '{qdef['label']}' could not be resolved by query {qdef}!")
            continue

        print(f"\n" + "#" * 80)
        print(f"COURSE: {course.name}")
        print(f"  Resolved ID: {course.id}")
        print(f"  Code: {course.code} | Canonical Code: {course.canonical_code}")
        print(f"  Department: {course.department} | Regulation Year: {course.regulation_year}")

        # 1. Canonical Syllabus Taxonomy
        syl = db.query(Syllabus).filter(Syllabus.course_id == course.id).first()
        if not syl:
            print("  [WARNING] No canonical syllabus record found for course!")
            units = []
        else:
            units = (
                db.query(Unit)
                .filter(Unit.syllabus_id == syl.id)
                .order_by(Unit.number)
                .all()
            )

        print(f"\n  [CANONICAL SYLLABUS TAXONOMY] ({len(units)} units total):")
        for u in units:
            t_count = db.query(Topic).filter(Topic.unit_id == u.id).count()
            print(f"    - Unit {u.number}: {u.name!r} ({t_count} cataloged topics)")

        # 2. Authoritative Intended Plan
        plan = get_course_assessment_plan(course.id)
        if plan:
            print(f"\n  [INTENDED ASSESSMENT PLAN] Source: {plan.source_document}")
            for comp in plan.components:
                print(f"    - Component {comp.code} ({comp.canonical_label}):")
                print(f"        Role: {comp.role} | Student Cycle: {comp.student_label} | Marks: {comp.marks}")
                print(f"        Intended Syllabus Units: {comp.syllabus_units}")
                print(f"        Accepted Raw Labels: {comp.raw_labels}")
        else:
            print("\n  [INTENDED ASSESSMENT PLAN] No authoritative course plan registered.")

        # 3. Historical Exam Papers & Observed Scope
        exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.document),
                selectinload(Exam.sections)
                .selectinload(Section.questions)
                .selectinload(Question.topics)
                .selectinload(Topic.unit),
            )
            .filter(Exam.course_id == course.id)
            .order_by(Exam.year.desc().nullslast(), Exam.id.asc())
            .all()
        )

        print(f"\n  [HISTORICAL EXAM PAPERS & OBSERVED COVERAGE] ({len(exams)} papers total):")
        for ex in exams:
            cov = compute_paper_observed_coverage(ex)
            ident = cov.assessment_identity

            # Check for anomalies vs intended plan if component recognized
            intended_units_for_comp = None
            if plan:
                for c in plan.components:
                    if c.code == ident.normalized_code or c.student_label == ident.student_cycle:
                        intended_units_for_comp = set(c.syllabus_units)
                        break

            out_of_scope_units = []
            if intended_units_for_comp is not None and ident.student_cycle != "ALL":
                out_of_scope_units = [u for u in cov.observed_unit_numbers if u not in intended_units_for_comp]

            print(f"\n    ------------------------------------------------------------")
            print(f"    Paper ID: {ex.id} | Year: {ex.year} | Document: {cov.document_title or 'N/A'}")
            print(f"    Assessment Identity:")
            print(f"      - Raw assessment_type: {ident.raw_type!r}")
            print(f"      - Normalized Code: {ident.normalized_code} (Cycle: {ident.student_cycle})")
            print(f"      - Identification Source: {ident.identification_source} (Confidence: {ident.confidence})")
            print(f"      - Evidence: {ident.evidence_text}")
            print(f"    Questions Breakdown:")
            print(f"      - Total Questions: {cov.total_questions}")
            print(f"      - Mapped Questions: {cov.mapped_questions_count}")
            print(f"      - Unmapped Questions: {cov.unmapped_questions_count}")
            print(f"    Observed Syllabus Scope:")
            print(f"      - Observed Units: {cov.observed_unit_numbers}")
            print(f"      - Question Count by Unit: {cov.question_count_by_unit}")
            print(f"      - Marks by Unit: {cov.marks_by_unit}")
            print(f"      - Observed Topics Count: {len(cov.observed_topic_names)}")

            if out_of_scope_units:
                print(f"      - [ANOMALY DETECTED] Out-of-Intended-Scope Units Observed: {out_of_scope_units} (Intended: {sorted(list(intended_units_for_comp))})")
            elif intended_units_for_comp is not None and ident.student_cycle != "ALL":
                print(f"      - [SCOPE MATCH] Observed units {cov.observed_unit_numbers} fall within intended scope {sorted(list(intended_units_for_comp))}")

        # 4. Cycle-level Aggregations
        print(f"\n  [CYCLE-LEVEL AGGREGATED COVERAGE]:")
        for cycle in ["CT1", "CT2", "ENDSEM"]:
            cycle_exams = [
                ex for ex in exams
                if identify_exam_assessment(ex, course.id).student_cycle == cycle
            ]
            if not cycle_exams:
                print(f"    Cycle {cycle:6s}: 0 historical exam papers available.")
                continue

            cycle_cov = compute_cycle_observed_coverage(course.id, cycle, cycle_exams)
            print(f"    Cycle {cycle:6s}: {cycle_cov.paper_count} papers | {cycle_cov.total_questions} Qs ({cycle_cov.mapped_questions_count} mapped) | Observed Units: {cycle_cov.observed_unit_numbers} | Qs by Unit: {cycle_cov.question_count_by_unit}")

    # 5. Auditability chain demonstration
    print(f"\n" + "=" * 80)
    print("PROVENANCE AUDIT CHAIN DEMONSTRATION (Sample Paper from Calculus):")
    calc_course = db.query(Course).filter(Course.canonical_code == "21MAB101T").first()
    if calc_course:
        calc_exam = db.query(Exam).filter(Exam.course_id == calc_course.id).first()
        if calc_exam:
            chain = build_coverage_audit_chain(calc_course.id, calc_exam.id, db)
            print(f"  Course: {calc_course.name} (ID: {calc_course.id}) | Exam ID: {calc_exam.id}")
            print(f"  Raw Assessment Type: {chain.get('raw_assessment_type')}")
            print(f"  Identified As: {chain.get('assessment_identity')}")
            print(f"  Document: {chain.get('document')}")
            print(f"  Observed Units: {chain.get('observed_units')}")
            print(f"  Lineage (first 3 questions):")
            for q in chain.get("question_lineage", [])[:3]:
                print(f"    Q#{q['question_number']} (ID={q['question_id']}): Mapped={q['is_mapped']} | Topics={[t['name'] for t in q['mapped_topics']]} | Units={[u['number'] for u in q['canonical_units']]}")

    db.close()
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    audit_representative_courses()
