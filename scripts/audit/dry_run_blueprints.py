import time
import json
from collections import defaultdict
from backend.core.database import SessionLocal
from backend.services.dna.blueprint import BlueprintExtractor

def run_dry_run():
    db = SessionLocal()
    try:
        canonical_courses = [
            (1, "Calculus And Linear Algebra"),
            (2, "Chemistry"),
            (5, "Programming For Problem Solving"),
            (28, "Database Management Systems")
        ]

        print("=" * 70)
        print("MINTAI HISTORICAL ASSESSMENT BLUEPRINTS: CANONICAL DRY RUN")
        print("=" * 70)

        for cid, cname in canonical_courses:
            t0 = time.perf_counter()
            res = BlueprintExtractor.extract_course_blueprints_from_db(cid, db=db)
            latency_ms = (time.perf_counter() - t0) * 1000

            print(f"\n######################################################################")
            print(f"COURSE {cid}: {cname}")
            print(f"Total Papers Analyzed: {res.total_papers_analyzed} | Extraction Latency: {latency_ms:.2f} ms")
            print(f"Distinct Assessment Cycles Discovered: {list(res.cycles.keys())}")
            print(f"######################################################################")

            for cycle_name, cycle_bp in res.cycles.items():
                print(f"\n--- CYCLE: {cycle_name} (Total Papers: {cycle_bp.total_cycle_papers}, Unique Blueprints: {cycle_bp.unique_blueprints_count}) ---")
                if cycle_bp.dominant_signature:
                    print(f"  DOMINANT TEMPLATE FOUND: {cycle_bp.dominant_signature}")
                else:
                    print(f"  NO DOMINANT TEMPLATE (Multiple distinct variants with count < 2 or equal distribution)")

                for idx, cluster in enumerate(cycle_bp.clusters):
                    rep = cluster.representative_blueprint
                    sec_desc = " | ".join(
                        f"{s.name}: {s.total_questions}Q (alts={s.alternative_questions_count}, m={s.marks_per_question or 'unscored'}, choice={s.choice_type})"
                        for s in rep.sections
                    )
                    print(f"\n  [{idx+1}] Cluster Status: {cluster.status} ({cluster.matching_paper_count}/{cycle_bp.total_cycle_papers} papers, {cluster.percentage_of_cycle}%)")
                    print(f"      Label: {cluster.label}")
                    print(f"      Sections: {sec_desc}")
                    print(f"      Years Observed: {cluster.years_observed} | First: {cluster.first_observed_year}, Latest: {cluster.latest_observed_year}")
                    print(f"      Paper IDs: {cluster.exam_ids}")
                    print(f"      Total Scored Marks: {rep.total_scored_marks} | Total Offered Marks: {rep.total_offered_marks} | Has Unscored: {rep.has_unscored_questions}")

                    # Detailed reconciliation verification
                    q_reconciled = (rep.total_questions == sum(s.total_questions for s in rep.sections))
                    m_scored_reconciled = (abs(rep.total_scored_marks - sum(s.scored_marks_sum for s in rep.sections)) < 0.01)
                    m_offered_reconciled = (abs(rep.total_offered_marks - sum(s.total_offered_marks for s in rep.sections)) < 0.01)
                    print(f"      Reconciliation: Questions={q_reconciled}, Scored Marks={m_scored_reconciled}, Offered Marks={m_offered_reconciled}")

                    # Print section unit and question type composition
                    for s in rep.sections:
                        print(f"        -> {s.name}: QRange={s.question_number_range} | Units={s.unit_distribution} | QTypes={s.question_types}")

    finally:
        db.close()

if __name__ == '__main__':
    run_dry_run()
