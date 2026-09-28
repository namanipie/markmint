"""
Corpus Benchmark & Audit Runner for Deterministic Cognitive Demand Classifier.

Executes over the full 9,013-question corpus in production_corpus.db WITHOUT
mutating any tables, columns, or rows.

Produces comprehensive distributions, breakdown by question type,
canonical courses, and conflict/ambiguity logs.
"""

from collections import Counter, defaultdict
import json
import os
import sqlite3
import sys
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.cognitive_demand_classifier import (
    CognitiveDemand,
    DemandConfidence,
    DeterministicCognitiveDemandClassifier,
)


def run_cognitive_demand_benchmark(db_path: str = "production_corpus.db") -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT q.id, q.original_text, q.question_type, q.marks, q.structured_content, co.name 
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN courses co ON e.course_id = co.id
        ORDER BY q.id ASC
    """)
    rows = c.fetchall()
    conn.close()

    total = len(rows)
    demand_counts = Counter()
    by_qtype = defaultdict(Counter)
    by_course = defaultdict(Counter)
    conflicts = []
    composite_counts = Counter()

    for qid, text, qtype, marks, sc, cname in rows:
        proposal = DeterministicCognitiveDemandClassifier.classify(
            text=text,
            question_type=qtype,
            structured_content=sc,
            marks=marks
        )
        dem_val = proposal.demand.value
        demand_counts[dem_val] += 1
        by_qtype[qtype or "None"][dem_val] += 1
        by_course[cname][dem_val] += 1
        if proposal.is_composite:
            composite_counts[dem_val] += 1

        if proposal.demand == CognitiveDemand.UNCLASSIFIED and any("conflict" in s for s in proposal.signals):
            conflicts.append({
                "id": qid,
                "course": cname,
                "question_type": qtype,
                "signals": proposal.signals,
                "text_snippet": (text or "")[:140]
            })

    classified_count = total - demand_counts[CognitiveDemand.UNCLASSIFIED.value]
    classified_pct = (classified_count / total) * 100
    unclassified_pct = (demand_counts[CognitiveDemand.UNCLASSIFIED.value] / total) * 100

    canonical_courses = [
        "Calculus And Linear Algebra",
        "Chemistry",
        "Programming For Problem Solving",
        "Database Management Systems"
    ]

    report = {
        "total_questions": total,
        "classified_count": classified_count,
        "classified_pct": round(classified_pct, 2),
        "unclassified_count": demand_counts[CognitiveDemand.UNCLASSIFIED.value],
        "unclassified_pct": round(unclassified_pct, 2),
        "demand_distribution": dict(demand_counts),
        "composite_distribution": dict(composite_counts),
        "by_question_type": {k: dict(v) for k, v in sorted(by_qtype.items())},
        "by_canonical_course": {cname: dict(by_course[cname]) for cname in canonical_courses},
        "conflicts_count": len(conflicts),
        "sample_conflicts": conflicts[:15]
    }

    return report


def print_benchmark_report(report: Dict[str, Any]) -> None:
    total = report["total_questions"]
    print("=" * 72)
    print("MINTAI HISTORICAL COGNITIVE DEMAND CORPUS BENCHMARK")
    print("=" * 72)
    print(f"Total Corpus Questions Audited: {total}")
    print(f"Classified Questions:           {report['classified_count']} ({report['classified_pct']}%)")
    print(f"Unclassified / Ambiguous:       {report['unclassified_count']} ({report['unclassified_pct']}%)")
    print(f"Conflicting Evidence Cases:     {report['conflicts_count']}")
    print("-" * 72)
    print("DEMAND ARCHETYPE DISTRIBUTION:")
    for dem, count in sorted(report["demand_distribution"].items(), key=lambda x: -x[1]):
        pct = (count / total) * 100
        print(f"  {dem:32s}: {count:5d} ({pct:5.2f}%)")

    print("-" * 72)
    print("BREAKDOWN BY EXISTING QUESTION TYPE:")
    for qt, counts in sorted(report["by_question_type"].items()):
        subtotal = sum(counts.values())
        print(f"\n[{qt}] (N={subtotal}):")
        for dem, count in sorted(counts.items(), key=lambda x: -x[1]):
            pct = (count / subtotal) * 100
            print(f"    {dem:30s}: {count:5d} ({pct:5.2f}%)")

    print("-" * 72)
    print("BREAKDOWN BY CANONICAL COURSES:")
    for cname, counts in sorted(report["by_canonical_course"].items()):
        subtotal = sum(counts.values())
        print(f"\n[{cname}] (N={subtotal}):")
        for dem, count in sorted(counts.items(), key=lambda x: -x[1]):
            pct = (count / subtotal) * 100
            print(f"    {dem:30s}: {count:5d} ({pct:5.2f}%)")

    print("-" * 72)
    print("SAMPLE CONFLICTING / AMBIGUOUS EVIDENCE CASES:")
    for item in report["sample_conflicts"][:5]:
        print(f"  [QID {item['id']}] ({item['course']} - {item['question_type']}):")
        print(f"    Text: {item['text_snippet']}")
        print(f"    Signals: {item['signals']}")


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "production_corpus.db"
    rep = run_cognitive_demand_benchmark(db_file)
    print_benchmark_report(rep)
