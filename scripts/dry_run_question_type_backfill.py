"""
Full Production Dry Run and Analysis for Question Type Classifier.

Reads all historical questions from production_corpus.db without modifying the database.
Generates full dry-run CSV in data/reports/question_type_dryrun.csv and outputs
comprehensive analysis covering overall stats, course distributions, marks breakdowns,
assessment cycles, historical years, collision audits, and a 150-question representative sample.
"""

import os
import sys
import csv
import json
import sqlite3
from collections import defaultdict, Counter
from typing import Dict, Any, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.services.question_type_classifier import (
    DeterministicQuestionTypeClassifier,
    QuestionType,
    ClassificationConfidence,
)

DB_PATH = "production_corpus.db"
OUTPUT_DIR = os.path.join("data", "reports")
CSV_PATH = os.path.join(OUTPUT_DIR, "question_type_dryrun.csv")
JSON_PATH = os.path.join(OUTPUT_DIR, "question_type_dryrun_summary.json")


def run_dry_run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT 
        q.id AS question_id,
        c.id AS course_id,
        c.name AS course_name,
        e.id AS exam_id,
        e.year AS exam_year,
        e.assessment_type AS assessment_cycle,
        s.name AS section_name,
        q.marks AS marks,
        q.original_text AS text
    FROM questions q
    JOIN sections s ON q.section_id = s.id
    JOIN exams e ON s.exam_id = e.id
    JOIN courses c ON e.course_id = c.id
    ORDER BY q.id ASC
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"Loaded {len(rows)} questions from {DB_PATH}.")

    results = []
    
    for row in rows:
        q_id = row["question_id"]
        c_id = row["course_id"]
        c_name = row["course_name"]
        e_id = row["exam_id"]
        e_year = row["exam_year"]
        cycle = row["assessment_cycle"] or "UNKNOWN"
        sec_name = row["section_name"] or ""
        marks = row["marks"]
        text = row["text"] or ""

        proposal = DeterministicQuestionTypeClassifier.classify(
            text=text,
            marks=marks,
            section_name=sec_name
        )

        clean_preview = " ".join(text.split())[:120]

        record = {
            "question_id": q_id,
            "course_id": c_id,
            "course_name": c_name,
            "exam_id": e_id,
            "exam_year": e_year if e_year is not None else "UNKNOWN",
            "assessment_cycle": cycle,
            "marks": marks if marks is not None else "NONE",
            "predicted_type": proposal.question_type.value,
            "confidence": proposal.confidence.value,
            "signals": ";".join(proposal.signals),
            "text_preview": clean_preview,
            "raw_text": text
        }
        results.append(record)

    conn.close()

    # Write CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "question_id", "course_id", "course_name", "exam_id", "exam_year",
            "assessment_cycle", "marks", "predicted_type", "confidence",
            "signals", "text_preview"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"Dry-run CSV successfully saved to {CSV_PATH} ({len(results)} rows).")
    return results


def analyze_predictions(results: List[Dict[str, Any]]):
    total = len(results)
    
    # ---------------------------------------------------------
    # Overall Metrics
    # ---------------------------------------------------------
    cat_counts = Counter(r["predicted_type"] for r in results)
    conf_counts = Counter(r["confidence"] for r in results)
    missing_text_count = sum(1 for r in results if not r["text_preview"] or len(r["text_preview"].strip()) < 6)
    missing_marks_count = sum(1 for r in results if r["marks"] == "NONE")
    unclassified_count = cat_counts[QuestionType.UNCLASSIFIED.value]

    print("\n" + "="*80)
    print("PHASE 2: FULL-CORPUS PREDICTIONS ANALYSIS")
    print("="*80)
    print(f"Total Questions Analyzed: {total}")
    print(f"Missing Text Count: {missing_text_count} ({missing_text_count/total*100:.2f}%)")
    print(f"Missing Marks Count: {missing_marks_count} ({missing_marks_count/total*100:.2f}%)")
    print(f"Overall Unclassified Count: {unclassified_count} ({unclassified_count/total*100:.2f}%)")

    print("\n--- Overall Category Distribution ---")
    for cat, count in cat_counts.most_common():
        pct = count / total * 100
        print(f"  {cat:<35}: {count:>5} ({pct:>5.2f}%)")

    print("\n--- Confidence Distribution ---")
    for conf, count in conf_counts.most_common():
        pct = count / total * 100
        print(f"  {conf:<15}: {count:>5} ({pct:>5.2f}%)")

    # ---------------------------------------------------------
    # By Course
    # ---------------------------------------------------------
    by_course = defaultdict(list)
    for r in results:
        by_course[r["course_name"]].append(r)

    print("\n" + "="*80)
    print("ANALYSIS BY COURSE")
    print("="*80)
    course_stats = {}
    for c_name, c_records in sorted(by_course.items(), key=lambda x: len(x[1]), reverse=True):
        c_total = len(c_records)
        c_cats = Counter(r["predicted_type"] for r in c_records)
        c_unclass = c_cats[QuestionType.UNCLASSIFIED.value]
        c_unclass_pct = c_unclass / c_total * 100
        
        # numeric score for confidence
        conf_map = {"high": 1.0, "medium": 0.7, "low": 0.3}
        avg_conf = sum(conf_map.get(r["confidence"], 0.3) for r in c_records) / c_total

        course_stats[c_name] = {
            "total": c_total,
            "unclass_pct": c_unclass_pct,
            "avg_conf": avg_conf,
            "categories": dict(c_cats)
        }

        print(f"\nCourse: {c_name} (Total Qs: {c_total}, Avg Conf: {avg_conf:.2f}, Unclassified: {c_unclass_pct:.1f}%)")
        for cat, count in c_cats.most_common():
            print(f"    {cat:<32}: {count:>4} ({count/c_total*100:>5.1f}%)")

    # ---------------------------------------------------------
    # By Marks Tier
    # ---------------------------------------------------------
    def get_mark_tier(m_val):
        if m_val == "NONE":
            return "Unscored / Missing"
        try:
            m = float(m_val)
            if m == 1.0:
                return "1 mark"
            elif 2.0 <= m <= 4.0:
                return "2–4 marks"
            elif 5.0 <= m <= 7.0:
                return "5–7 marks"
            elif 8.0 <= m <= 10.0:
                return "8–10 marks"
            elif 12.0 <= m <= 15.0:
                return "12–15 marks"
            else:
                return f"Other ({m:g}m)"
        except ValueError:
            return "Unscored / Missing"

    by_mark_tier = defaultdict(list)
    for r in results:
        tier = get_mark_tier(r["marks"])
        by_mark_tier[tier].append(r)

    print("\n" + "="*80)
    print("ANALYSIS BY MARKS TIER")
    print("="*80)
    for tier in ["1 mark", "2–4 marks", "5–7 marks", "8–10 marks", "12–15 marks", "Unscored / Missing"]:
        tier_records = by_mark_tier.get(tier, [])
        t_total = len(tier_records)
        if t_total == 0:
            continue
        t_cats = Counter(r["predicted_type"] for r in tier_records)
        print(f"\nMarks Tier: {tier} (Total Qs: {t_total})")
        for cat, count in t_cats.most_common():
            print(f"    {cat:<32}: {count:>4} ({count/t_total*100:>5.1f}%)")

    # ---------------------------------------------------------
    # By Assessment Type
    # ---------------------------------------------------------
    by_cycle = defaultdict(list)
    for r in results:
        by_cycle[r["assessment_cycle"]].append(r)

    print("\n" + "="*80)
    print("ANALYSIS BY ASSESSMENT CYCLE")
    print("="*80)
    for cycle, cyc_records in sorted(by_cycle.items(), key=lambda x: len(x[1]), reverse=True):
        cyc_total = len(cyc_records)
        cyc_cats = Counter(r["predicted_type"] for r in cyc_records)
        print(f"\nCycle: {cycle} (Total Qs: {cyc_total})")
        for cat, count in cyc_cats.most_common():
            print(f"    {cat:<32}: {count:>4} ({count/cyc_total*100:>5.1f}%)")

    # ---------------------------------------------------------
    # By Historical Year
    # ---------------------------------------------------------
    by_year = defaultdict(list)
    for r in results:
        by_year[r["exam_year"]].append(r)

    print("\n" + "="*80)
    print("ANALYSIS BY HISTORICAL YEAR")
    print("="*80)
    for yr in sorted(by_year.keys(), key=lambda y: (str(y) == "UNKNOWN", str(y))):
        yr_records = by_year[yr]
        y_total = len(yr_records)
        y_cats = Counter(r["predicted_type"] for r in yr_records)
        y_unclass = y_cats[QuestionType.UNCLASSIFIED.value]
        conf_map = {"high": 1.0, "medium": 0.7, "low": 0.3}
        y_avg_conf = sum(conf_map.get(r["confidence"], 0.3) for r in yr_records) / y_total
        print(f"Year {yr:<8} (Total: {y_total:>4}, Unclass: {y_unclass/y_total*100:>4.1f}%, Avg Conf: {y_avg_conf:.2f}) -> Top: {y_cats.most_common(2)}")

    return course_stats


def audit_anomalies_and_collisions(results: List[Dict[str, Any]]):
    print("\n" + "="*80)
    print("PHASE 3: COLLISION AND ANOMALY AUDIT")
    print("="*80)

    suspicious = []

    # 1. Programming in non-programming courses
    non_prog_keywords = ["ethics", "chemistry", "english", "biology", "constitution", "calculus", "biochem"]
    for r in results:
        c_lower = r["course_name"].lower()
        if r["predicted_type"] == QuestionType.PROGRAMMING.value:
            if any(k in c_lower for k in non_prog_keywords):
                suspicious.append({
                    "issue": "programming_in_non_programming_course",
                    "reason": f"Programming detected in non-programming course {r['course_name']}",
                    "record": r
                })

    # 2. Objective on high marks (>= 8 marks)
    for r in results:
        if r["predicted_type"] == QuestionType.OBJECTIVE_MCQ.value:
            try:
                m = float(r["marks"])
                if m >= 8.0:
                    suspicious.append({
                        "issue": "objective_on_high_marks",
                        "reason": f"Objective / MCQ with {m} marks",
                        "record": r
                    })
            except (ValueError, TypeError):
                pass

    # 3. Numerical in strictly non-numerical courses
    strictly_non_num = ["ethics", "constitution", "english"]
    for r in results:
        c_lower = r["course_name"].lower()
        if r["predicted_type"] == QuestionType.NUMERICAL.value:
            if any(k in c_lower for k in strictly_non_num):
                suspicious.append({
                    "issue": "numerical_in_non_numerical_course",
                    "reason": f"Numerical calculation in conceptual course {r['course_name']}",
                    "record": r
                })

    # 4. Design classification on 1-mark questions
    for r in results:
        if r["predicted_type"] == QuestionType.DESIGN.value:
            try:
                m = float(r["marks"])
                if m <= 1.0:
                    suspicious.append({
                        "issue": "design_on_low_marks",
                        "reason": f"Design & Application with {m} mark",
                        "record": r
                    })
            except (ValueError, TypeError):
                pass

    # 5. High-confidence contradictory signals
    for r in results:
        sigs = r["signals"].split(";")
        has_calc = any("calc" in s for s in sigs)
        has_explain = any("explain" in s or "describe" in s for s in sigs)
        if has_calc and has_explain and r["confidence"] == "high":
            suspicious.append({
                "issue": "high_conf_contradictory_signals",
                "reason": "Both calculation and explanation signals active with high confidence",
                "record": r
            })

    print(f"Total Suspicious / Anomaly Cases Flagged: {len(suspicious)}")
    issue_counts = Counter(s["issue"] for s in suspicious)
    for issue, cnt in issue_counts.items():
        print(f"  {issue:<40}: {cnt}")

    print("\n--- Sample Suspicious Cases (Up to 15) ---")
    for i, s in enumerate(suspicious[:15]):
        rec = s["record"]
        print(f"[{i+1}] Issue: {s['issue']} | Course: {rec['course_name']} | Marks: {rec['marks']}")
        print(f"    Predicted: {rec['predicted_type']} (Conf: {rec['confidence']})")
        print(f"    Text: {rec['text_preview']}")
        print(f"    Signals: {rec['signals']}")
        print("-" * 60)

    return suspicious


def select_manual_spot_audit_sample(results: List[Dict[str, Any]], suspicious: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    print("\n" + "="*80)
    print("PHASE 4: MANUAL SPOT AUDIT SAMPLE SELECTION (150 QUESTIONS)")
    print("="*80)

    sample = []
    seen_ids = set()

    def add_record(r, reason=""):
        if r["question_id"] not in seen_ids:
            seen_ids.add(r["question_id"])
            sample.append((r, reason))

    # 1. Add up to 25 suspicious/anomaly cases
    for s in suspicious[:25]:
        add_record(s["record"], f"ANOMALY: {s['issue']}")

    # 2. Add representation from every category (10 per category = 90)
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["predicted_type"]].append(r)

    for cat, recs in by_cat.items():
        # pick a mix of high and medium confidence
        highs = [r for r in recs if r["confidence"] == "high"]
        meds = [r for r in recs if r["confidence"] == "medium"]
        lows = [r for r in recs if r["confidence"] == "low"]
        
        for r in highs[:6]:
            add_record(r, f"CAT: {cat} (High Conf)")
        for r in meds[:3]:
            add_record(r, f"CAT: {cat} (Med Conf)")
        for r in lows[:2]:
            add_record(r, f"CAT: {cat} (Low Conf)")

    # 3. Add diverse mark tiers (1m, 2-4m, 5-7m, 8-10m, 12-15m, None)
    by_marks = defaultdict(list)
    for r in results:
        by_marks[str(r["marks"])].append(r)

    for m_key in ["1.0", "2.0", "3.0", "4.0", "8.0", "10.0", "12.0", "15.0", "NONE"]:
        recs = by_marks.get(m_key, [])
        for r in recs[:4]:
            add_record(r, f"MARKS: {m_key}")

    # 4. Fill to at least 150 from across courses
    by_course = defaultdict(list)
    for r in results:
        by_course[r["course_name"]].append(r)

    course_cycle = list(by_course.keys())
    c_idx = 0
    while len(sample) < 160 and c_idx < len(course_cycle) * 10:
        c_name = course_cycle[c_idx % len(course_cycle)]
        recs = by_course[c_name]
        for r in recs:
            if r["question_id"] not in seen_ids:
                add_record(r, f"COURSE: {c_name}")
                break
        c_idx += 1

    print(f"Selected {len(sample)} representative questions for spot audit.")
    
    # Print sample
    for idx, (r, reason) in enumerate(sample[:160], 1):
        print(f"\n[{idx:3d}] QID: {r['question_id']:<5} | Course: {r['course_name'][:25]:<25} | Yr: {r['exam_year']} | Cycle: {r['assessment_cycle']:<6} | Marks: {r['marks']}")
        print(f"      Type: {r['predicted_type']:<28} | Conf: {r['confidence']:<6} | Reason: {reason}")
        print(f"      Text: {r['text_preview']}")
        print(f"      Signals: {r['signals']}")

    return [s[0] for s in sample]


if __name__ == "__main__":
    results = run_dry_run()
    course_stats = analyze_predictions(results)
    suspicious = audit_anomalies_and_collisions(results)
    sample = select_manual_spot_audit_sample(results, suspicious)
