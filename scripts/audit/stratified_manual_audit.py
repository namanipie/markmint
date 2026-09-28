import os
import sys
import sqlite3
import json
from collections import defaultdict, Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.cognitive_demand_classifier import (
    CognitiveDemand,
    DemandConfidence,
    DeterministicCognitiveDemandClassifier,
)

def build_stratified_sample():
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

    # Stratified selection buckets:
    # We want ~60 items:
    # 15 RECALL_AND_CONCEPT
    # 15 PROCEDURAL_COMPUTATION
    # 15 ANALYTICAL_PROOF_AND_DESIGN
    # 15 UNCLASSIFIED (ambiguous, conflicting, short, unseparated)
    # Spanning Calculus, Chemistry, PPS, DBMS, various cycles, short & long, math & code.
    canonical_courses = [
        "Calculus And Linear Algebra",
        "Chemistry",
        "Programming For Problem Solving",
        "Database Management Systems"
    ]

    proposals = []
    for r in rows:
        qid, text, qtype, marks, sc, cname, cycle, year, sec_name = r
        prop = DeterministicCognitiveDemandClassifier.classify(
            text=text,
            question_type=qtype,
            structured_content=sc,
            marks=marks,
            section_name=sec_name
        )
        proposals.append((r, prop))

    # Stratified selection
    target_per_demand = 16
    sampled = {
        CognitiveDemand.RECALL_AND_CONCEPT: [],
        CognitiveDemand.PROCEDURAL_COMPUTATION: [],
        CognitiveDemand.ANALYTICAL_PROOF_AND_DESIGN: [],
        CognitiveDemand.UNCLASSIFIED: []
    }

    # Gather items from canonical courses first
    for r, prop in proposals:
        qid, text, qtype, marks, sc, cname, cycle, year, sec_name = r
        dem = prop.demand
        if len(sampled[dem]) < target_per_demand:
            # Spread across canonical courses
            courses_in_bucket = [x[0][5] for x in sampled[dem]]
            if courses_in_bucket.count(cname) < 4 or (cname not in canonical_courses and len(sampled[dem]) >= 12):
                sampled[dem].append((r, prop))

    sample_list = []
    for dem, items in sampled.items():
        sample_list.extend(items)

    print(f"Total Stratified Sample Size: {len(sample_list)}")
    return sample_list

if __name__ == "__main__":
    sample = build_stratified_sample()
    for (r, prop) in sample:
        qid, text, qtype, marks, sc, cname, cycle, year, sec_name = r
        print(f"[{qid}] ({cname} | {qtype} | {cycle} | {year}) -> {prop.demand.value} (conf={prop.confidence.value})")
        print(f"    Text: {text[:110].strip()}")
        print(f"    Signals: {prop.signals[:2]}")
