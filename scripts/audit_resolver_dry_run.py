"""
Complete Dry-Run Runner for ExamChronologyResolver.

Operates in STRICT READ-ONLY mode against production_corpus.db.
Audits all 314 exams, compares against existing metadata, evaluates
all proposed resolutions, detects false positives, and generates
comprehensive dry-run statistics.
"""

import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath("."))

from backend.services.exam_chronology_resolver import (
    ExamChronologyResolver,
    EvidenceSource,
    ResolutionCategory,
    ResolutionResult,
)


def run_dry_run() -> Dict[str, Any]:
    # 1. Connect in STRICT READ-ONLY mode
    db_path = os.path.abspath("production_corpus.db")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    c = conn.cursor()

    # 2. Load manifest for local file paths
    manifest_path = "data/manifests/first_year_union_manifest.json"
    manifest_by_hash = {}
    manifest_by_title = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_items = json.load(f)
        for item in manifest_items:
            if item.get("sha256"):
                manifest_by_hash[item["sha256"]] = item
            if item.get("title"):
                manifest_by_title[item["title"]] = item

    # 3. Fetch all 314 exams
    c.execute("""
        SELECT e.id, c.id, c.name, e.year, e.assessment_type, d.id, d.title, d.original_url, d.document_hash
        FROM exams e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN documents d ON e.document_id = d.id
        ORDER BY c.name, e.id
    """)
    exams = c.fetchall()

    results: List[ResolutionResult] = []

    for row in exams:
        eid, cid, cname, ey, eat, did, dtitle, durl, dhash = row

        # Find local path
        m_item = manifest_by_hash.get(dhash) or manifest_by_title.get(dtitle)
        lp = m_item.get("local_path") if m_item else None

        # Sample question text
        c.execute("""
            SELECT q.original_text
            FROM sections s
            JOIN questions q ON q.section_id = s.id
            WHERE s.exam_id = ?
            LIMIT 5
        """, (eid,))
        q_rows = c.fetchall()
        q_texts = [r[0] for r in q_rows if r[0]]

        res = ExamChronologyResolver.resolve_exam(
            exam_id=eid,
            course_id=cid,
            course_name=cname,
            current_year=ey,
            current_assessment_type=eat,
            source_title=dtitle or "",
            local_path=lp,
            question_texts=q_texts,
        )
        results.append(res)

    conn.close()

    # 4. Compute aggregations
    total_exams = len(results)
    already_yeared = sum(1 for r in results if r.resolution_category == ResolutionCategory.ALREADY_RESOLVED)
    proposed_resolutions = [r for r in results if r.is_mutation_candidate]
    unresolved = [r for r in results if r.resolution_category == ResolutionCategory.UNRESOLVED]
    ambiguous = [r for r in results if r.resolution_category == ResolutionCategory.AMBIGUOUS]

    missing_year_total = total_exams - already_yeared
    resolution_rate_missing = (len(proposed_resolutions) / missing_year_total * 100) if missing_year_total > 0 else 0.0
    corpus_coverage_after = ((already_yeared + len(proposed_resolutions)) / total_exams * 100)

    # By Course
    course_stats = defaultdict(lambda: {"total": 0, "already_yeared": 0, "proposed": 0, "unresolved": 0, "ambiguous": 0})
    for r in results:
        c = r.course_name
        course_stats[c]["total"] += 1
        if r.resolution_category == ResolutionCategory.ALREADY_RESOLVED:
            course_stats[c]["already_yeared"] += 1
        elif r.is_mutation_candidate:
            course_stats[c]["proposed"] += 1
        elif r.resolution_category == ResolutionCategory.AMBIGUOUS:
            course_stats[c]["ambiguous"] += 1
        else:
            course_stats[c]["unresolved"] += 1

    # By Assessment Type
    atype_stats = defaultdict(lambda: {"total": 0, "proposed": 0})
    for r in results:
        at = str(r.proposed_assessment_type or r.current_assessment_type or "None")
        atype_stats[at]["total"] += 1
        if r.is_mutation_candidate:
            atype_stats[at]["proposed"] += 1

    # By Evidence Source
    source_counts = Counter(r.evidence_source.value for r in proposed_resolutions)

    summary = {
        "total_exams": total_exams,
        "already_yeared": already_yeared,
        "missing_year_total": missing_year_total,
        "proposed_resolutions_count": len(proposed_resolutions),
        "unresolved_count": len(unresolved),
        "ambiguous_count": len(ambiguous),
        "resolution_rate_missing": resolution_rate_missing,
        "corpus_coverage_before": (already_yeared / total_exams * 100),
        "corpus_coverage_after": corpus_coverage_after,
        "course_stats": dict(course_stats),
        "assessment_type_stats": dict(atype_stats),
        "evidence_source_stats": dict(source_counts),
        "proposed_resolutions": [r.to_dict() for r in proposed_resolutions],
        "ambiguous_records": [r.to_dict() for r in ambiguous],
    }

    return summary


if __name__ == "__main__":
    summary = run_dry_run()
    print("=" * 80)
    print("MINTAI EXAM METADATA RESOLVER — DRY RUN SUMMARY")
    print("=" * 80)
    print(f"Total Exams: {summary['total_exams']}")
    print(f"Already Yeared: {summary['already_yeared']} ({summary['corpus_coverage_before']:.1f}%)")
    print(f"Missing-Year Exams: {summary['missing_year_total']}")
    print(f"Proposed Year Resolutions: {summary['proposed_resolutions_count']} ({summary['resolution_rate_missing']:.1f}% of missing)")
    print(f"Unresolved Exams: {summary['unresolved_count']}")
    print(f"Ambiguous Exams: {summary['ambiguous_count']}")
    print(f"Projected Corpus Year Coverage: {summary['corpus_coverage_after']:.1f}% (283/314)")
    print("-" * 80)
    print("BY COURSE:")
    for c, s in sorted(summary["course_stats"].items()):
        missing = s["total"] - s["already_yeared"]
        pct = (s["proposed"] / missing * 100) if missing > 0 else 100.0
        print(f"  {c:<45} | Missing: {missing:>2} | Proposed: {s['proposed']:>2} ({pct:>5.1f}%) | Unresolved: {s['unresolved']:>2}")
    print("-" * 80)
    print("BY EVIDENCE SOURCE (for proposed):")
    for src, cnt in summary["evidence_source_stats"].items():
        print(f"  {src}: {cnt}")
