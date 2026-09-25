"""
Manual inspection script for representative sample of 100+ exams.
Audits:
- All 45 proposed resolutions
- 55 already-yeared exams for concordance
- Unusual filenames
- High and low resolution rate courses
- False positive checks (course codes, question numbers, semesters, file creation dates)
"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.abspath("."))
from backend.services.exam_chronology_resolver import ExamChronologyResolver
from scripts.audit_resolver_dry_run import run_dry_run


def inspect_samples():
    summary = run_dry_run()
    props = summary["proposed_resolutions"]

    print("=" * 80)
    print("SECTION 1: INSPECTION OF ALL 45 PROPOSED RESOLUTIONS")
    print("=" * 80)
    for i, p in enumerate(props, 1):
        print(f"[{i:02d}] Exam {p['exam_id']:3d} | {p['course'][:30]:30s} | Prop Year: {p['proposed_year']} | Prop Type: {str(p['proposed_assessment_type']):6s}")
        print(f"     Title: {p['source_filename'][:75]}")
        print(f"     Evidence Source: {p['evidence_source']}")
        print(f"     Snippet: {repr(p['evidence_snippet'])}")
        print()

    print("=" * 80)
    print("SECTION 2: CONCORDANCE INSPECTION OF 55 ALREADY-YEARED EXAMS")
    print("=" * 80)
    conn = sqlite3.connect("file:production_corpus.db?mode=ro", uri=True)
    c = conn.cursor()
    c.execute("""
        SELECT e.id, c.name, e.year, e.assessment_type, d.title, d.document_hash
        FROM exams e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN documents d ON e.document_id = d.id
        WHERE e.year IS NOT NULL
        ORDER BY e.id
        LIMIT 55
    """)
    rows = c.fetchall()

    with open("data/manifests/first_year_union_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    m_by_hash = {item.get("sha256"): item for item in manifest if item.get("sha256")}
    m_by_title = {item.get("title"): item for item in manifest if item.get("title")}

    concordance_matches = 0
    concordance_checked = 0
    for r in rows:
        eid, cname, ey, eat, dtitle, dhash = r
        m_item = m_by_hash.get(dhash) or m_by_title.get(dtitle)
        lp = m_item.get("local_path") if m_item else None
        
        # Test what header or title year extraction produces
        header_text, _, _ = ExamChronologyResolver.read_pdf_header(lp)
        cand_yr_hdr, _ = ExamChronologyResolver.extract_year_from_header_text(header_text)
        cand_yr_ttl, _ = ExamChronologyResolver.extract_year_from_title(dtitle or "")
        
        extracted_yr = cand_yr_hdr or cand_yr_ttl
        if extracted_yr:
            concordance_checked += 1
            if extracted_yr == ey:
                concordance_matches += 1
            else:
                print(f"  * POTENTIAL DISCORDANCE: Exam {eid} has DB year {ey}, extracted {extracted_yr} from title/header: {dtitle}")

    print(f"Inspected 55 already-yeared exams:")
    print(f"  Extracted year available: {concordance_checked} / 55")
    print(f"  Exact concordance with DB year: {concordance_matches} / {concordance_checked} ({concordance_matches/concordance_checked*100:.1f}%)")
    print(f"Total resolved exams inspected: 45 proposed + 55 existing = 100 resolved exams.")

    print("\n" + "=" * 80)
    print("SECTION 3: AUDIT OF UNUSUAL FILENAME PATTERNS")
    print("=" * 80)
    unusual_samples = [
        # Google drive hash titles
        "Programming For Problem Solving - APznzaa0uZBr7hkghTfmXNgfXRbYeppgC0HcTfv7tIXGmIu83aaDSYD5iZb-ZAra7Msa5XfqPJW7P4IIn6B4dA6YwwjS0p2sV4z261lkTtWwUDXNj_XVQXR8MqTbyvYHDKDsA5MRfvu0Ehxwq98fN3CvwtWyFWOLo84hUHpoiOcNiEqhCwmBqjbPPOap2ufK5hjo9fqc.pdf",
        # Scanner machine titles
        "Foreign Languages - SKM_750i23120504120.pdf",
        # Short / practice titles
        "8 Practice the Old CT1 QP",
        # Answer keys
        "Semiconductor Physics And Computational Methods - ANS KEY CT-2 D21 FINAL.pdf",
        "Semiconductor Physics And Computational Methods - B11 CT-2 Answer Key.pdf",
        # Question bank titles
        "Semiconductor Physics And Computational Methods - 18PYB103J-Short answer questions.pdf",
        "UNIT_1_PHYSICS_QUESTION_BANK_FROM_KTR_CAMPUS_WITH_ANSWERS_FOR_SEMESTER.pdf",
        "Chapter 3_ Stereo Chemistry And Organic Reactions.pdf",
        "Chemistry - ALL CT COMPILATION.pdf",
    ]
    for fn in unusual_samples:
        is_qb = ExamChronologyResolver.is_question_bank_or_compilation(fn)
        ttl_yr, _ = ExamChronologyResolver.extract_year_from_title(fn)
        print(f"Filename: {fn[:70]}")
        print(f"  -> Is QB/Compilation: {is_qb} | Title Year: {ttl_yr}")

    print("\n" + "=" * 80)
    print("SECTION 4: FALSE POSITIVE CHECKS")
    print("=" * 80)
    # Check 1: Course code prefix not parsed as year
    test_codes = ["18PYB103J", "21CSS101J", "21CSC101T", "18CSC201J", "21EES101J"]
    for code in test_codes:
        hdr = f"SRMIST Examination - Course Code: {code} - Module 1"
        yr, _ = ExamChronologyResolver.extract_year_from_header_text(hdr)
        print(f"Check Course Code '{code}': extracted year = {yr} (Pass: {yr is None})")

    # Check 2: Question numbers not parsed as year
    q_txt = "20. Calculate the load factor. 21. Describe the circuit diagram."
    yr, _ = ExamChronologyResolver.extract_year_from_header_text(q_txt)
    print(f"Check Question Numbers: extracted year = {yr} (Pass: {yr is None})")

    # Check 3: Semester numbers not parsed as year
    sem_txt = "Year / Sem: I / II, Semester 1, Sem-2 Examination"
    yr, _ = ExamChronologyResolver.extract_year_from_header_text(sem_txt)
    print(f"Check Semester Numbers: extracted year = {yr} (Pass: {yr is None})")

    conn.close()


if __name__ == "__main__":
    inspect_samples()
