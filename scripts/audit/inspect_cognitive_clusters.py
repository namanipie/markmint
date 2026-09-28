import os
import sys
import sqlite3
import json
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.cognitive_demand_classifier import (
    CognitiveDemand,
    DemandConfidence,
    DeterministicCognitiveDemandClassifier,
)

def inspect_corpus():
    conn = sqlite3.connect("production_corpus.db")
    c = conn.cursor()
    c.execute("""
        SELECT 
            q.id, q.original_text, q.question_type, q.marks, q.structured_content,
            co.name as course_name,
            e.assessment_type, e.year, s.name as section_name
        FROM questions q
        JOIN sections s ON q.section_id = s.id
        JOIN exams e ON s.exam_id = e.id
        JOIN courses co ON e.course_id = co.id
        ORDER BY q.id ASC
    """)
    rows = c.fetchall()
    conn.close()

    total = len(rows)
    print(f"Loaded {total} questions from production corpus.")

    # 1. Overall distribution
    demand_counts = Counter()
    by_qtype = defaultdict(Counter)
    by_course = defaultdict(Counter)
    by_cycle = defaultdict(Counter)
    by_section = defaultdict(Counter)
    by_year = defaultdict(Counter)
    signal_counts = Counter()

    # Suspicious buckets
    mcqs_as_analytical = []
    derivations_as_recall = []
    programming_as_recall = []
    definitions_as_procedural = []
    ocr_garbage_classified = []

    for qid, text, qtype, marks, sc, cname, cycle, year, sec_name in rows:
        prop = DeterministicCognitiveDemandClassifier.classify(
            text=text,
            question_type=qtype,
            structured_content=sc,
            marks=marks,
            section_name=sec_name
        )
        dem = prop.demand
        dem_val = dem.value
        demand_counts[dem_val] += 1
        by_qtype[qtype or "None"][dem_val] += 1
        by_course[cname][dem_val] += 1
        by_cycle[cycle or "None"][dem_val] += 1
        
        # Normalize section name for grouping
        norm_sec = (sec_name or "Unknown").strip()
        by_section[norm_sec][dem_val] += 1
        
        yr_str = str(year) if year is not None else "Unknown"
        by_year[yr_str][dem_val] += 1

        for sig in prop.signals:
            rule_prefix = sig.split(":")[0] if ":" in sig else sig
            signal_counts[rule_prefix] += 1

        # Check suspicious clusters
        # A. MCQs classified as analytical
        if qtype == "Objective / MCQ" and dem == CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN:
            mcqs_as_analytical.append((qid, cname, text[:120], prop.signals))

        # B. Derivations classified as recall
        if qtype == "Derivation / Proof" and dem == CognitiveDemand.RECALL_AND_CONCEPT:
            derivations_as_recall.append((qid, cname, text[:120], prop.signals))

        # C. Programming classified as recall
        if qtype == "Programming & Implementation" and dem == CognitiveDemand.RECALL_AND_CONCEPT:
            programming_as_recall.append((qid, cname, text[:120], prop.signals))

        # D. Definitions classified as procedural
        if qtype == "Short Answer / Definition" and dem == CognitiveDemand.PROCEDURAL_COMPUTATION:
            definitions_as_procedural.append((qid, cname, text[:120], prop.signals))

    print("\n--- 1. OVERALL DISTRIBUTION ---")
    for k, v in demand_counts.most_common():
        print(f"  {k:30s}: {v:5d} ({v/total*100:5.2f}%)")

    print("\n--- TOP SIGNALS / RULES ---")
    for k, v in signal_counts.most_common(20):
        print(f"  {k:35s}: {v:5d}")

    print(f"\n--- SUSPICIOUS CLUSTERS ---")
    print(f"MCQs classified as Analytical: {len(mcqs_as_analytical)}")
    for qid, cname, snip, sigs in mcqs_as_analytical[:5]:
        print(f"  [QID {qid}] ({cname}): {snip} -> {sigs}")

    print(f"\nDerivations classified as Recall: {len(derivations_as_recall)}")
    for qid, cname, snip, sigs in derivations_as_recall[:5]:
        print(f"  [QID {qid}] ({cname}): {snip} -> {sigs}")

    print(f"\nProgramming classified as Recall: {len(programming_as_recall)}")
    for qid, cname, snip, sigs in programming_as_recall[:5]:
        print(f"  [QID {qid}] ({cname}): {snip} -> {sigs}")

    print(f"\nDefinitions classified as Procedural: {len(definitions_as_procedural)}")
    for qid, cname, snip, sigs in definitions_as_procedural[:5]:
        print(f"  [QID {qid}] ({cname}): {snip} -> {sigs}")

    return {
        "demand_counts": demand_counts,
        "by_qtype": by_qtype,
        "by_course": by_course,
        "by_cycle": by_cycle,
        "by_section": by_section,
        "by_year": by_year,
        "mcqs_as_analytical": mcqs_as_analytical,
        "derivations_as_recall": derivations_as_recall,
        "programming_as_recall": programming_as_recall,
        "definitions_as_procedural": definitions_as_procedural,
    }

if __name__ == "__main__":
    inspect_corpus()
