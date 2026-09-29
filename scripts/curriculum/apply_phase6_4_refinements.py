"""
Phase 6.4 Authoritative Implementation Script.
Applies validated taxonomy additions and refinements to definitions and database,
executes remapping pipeline, and verifies idempotency and integrity.
"""
import os
import sys
import json
import shutil
import sqlite3
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from scripts.audit.test_rules_in_memory import PROPOSED_UPDATES
from scripts.curriculum.map_s3_s4_topics import map_s3_s4_questions

DB_PATH = os.path.join(BASE_DIR, "production_corpus.db")
BACKUP_PATH = os.path.join(BASE_DIR, "production_corpus.db.pre_phase6_4_backup")
DEFS_DIR = os.path.join(BASE_DIR, "backend", "services", "taxonomy_registry", "definitions")

COURSE_FILES = {
    22: "course_22_prob.json",
    24: "course_24_dsa.json",
    25: "course_25_os.json",
    26: "course_26_coa.json",
    27: "course_27_daa.json",
    28: "course_28_dbms.json",
    29: "course_29_ai.json",
}

def apply_refinements():
    print("==================================================")
    print("PHASE 6.4 REFINEMENT & EXPANSION EXECUTION")
    print("==================================================")

    # 1. Back up database
    if not os.path.exists(BACKUP_PATH):
        print(f"Creating database backup at {BACKUP_PATH}...")
        shutil.copy2(DB_PATH, BACKUP_PATH)
    else:
        print(f"Backup already exists at {BACKUP_PATH}.")

    # 2. Add new topics to database if not present
    new_db_topics = [
        (934, 159, "Red-Black Trees: Properties and Balance"),
        (935, 173, "All-Pairs Shortest Paths: Floyd-Warshall Algorithm"),
        (936, 178, "Query Processing and Optimization: Parsing, Evaluation and Relational Plans"),
    ]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for tid, uid, name in new_db_topics:
        cur.execute("SELECT id FROM topics WHERE id = ?", (tid,))
        if not cur.fetchone():
            print(f"Inserting new topic {tid} into database: {name} (Unit {uid})...")
            cur.execute("INSERT INTO topics (id, unit_id, name) VALUES (?, ?, ?)", (tid, uid, name))
        else:
            print(f"Topic {tid} already exists in database.")
    conn.commit()
    conn.close()

    # 3. Update JSON definitions
    for cid, updates in PROPOSED_UPDATES.items():
        fname = COURSE_FILES[cid]
        fpath = os.path.join(DEFS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        units = data.get("units", [])
        unit_map = {u["id"]: u for u in units}
        topic_map = {}
        for u in units:
            for t in u.get("topics", []):
                topic_map[t["id"]] = t

        # Add new topics
        for nt in updates["new_topics"]:
            uid = nt["unit_id"]
            if uid in unit_map:
                existing_tids = [t["id"] for t in unit_map[uid]["topics"]]
                if nt["id"] not in existing_tids:
                    print(f"Adding Topic {nt['id']} ({nt['name']}) to Course {cid}, Unit {uid} in {fname}...")
                    new_topic_def = {
                        "id": nt["id"],
                        "name": nt["name"],
                        "canonical_name": nt.get("canonical_name", nt["name"]),
                        "aliases": nt.get("aliases", []),
                        "strong_phrases": nt.get("strong_phrases", []),
                        "specific_keywords": nt.get("specific_keywords", []),
                        "negative_guards": nt.get("negative_guards", []),
                        "context_hints": nt.get("context_hints", [])
                    }
                    unit_map[uid]["topics"].append(new_topic_def)
                    topic_map[nt["id"]] = new_topic_def

        # Update phrases
        for tid, phrases in updates["phrase_updates"].items():
            if tid in topic_map:
                t = topic_map[tid]
                curr_phrases = set(p.lower().strip() for p in t.get("strong_phrases", []))
                for p in phrases:
                    if p.lower().strip() not in curr_phrases:
                        t.setdefault("strong_phrases", []).append(p)
                        curr_phrases.add(p.lower().strip())

        # Update guards
        for tid, guards in updates.get("guards", {}).items():
            if tid in topic_map:
                t = topic_map[tid]
                curr_guards = set(g.lower().strip() for g in t.get("negative_guards", []))
                for g in guards:
                    if g.lower().strip() not in curr_guards:
                        t.setdefault("negative_guards", []).append(g)
                        curr_guards.add(g.lower().strip())

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated {fname} successfully.")

    # 4. Invalidate registry cache and validate against database
    print("\nValidating updated taxonomy registry against database...")
    # Force reload of registry
    import backend.services.taxonomy_registry.registry as reg_module
    reg_module._taxonomy_registry = None
    registry = get_taxonomy_registry()

    db = SessionLocal()
    for cid in COURSE_FILES.keys():
        val = registry.validate_against_database(cid, db)
        if not val["valid"]:
            print(f"FATAL: Course {cid} validation failed! {val['mismatches']}")
            sys.exit(1)
        print(f"  Course {cid} valid: {val['units_verified']} units, {val['topics_verified']} topics verified.")

    # 5. Execute authoritative remapping
    print("\nExecuting authoritative remapping via map_s3_s4_topics.py...")
    map_s3_s4_questions(apply_changes=True)

    # 6. Invalidate intelligence caches
    print("\nInvalidating intelligence caches for updated courses...")
    try:
        from backend.services.course_intelligence import get_course_intelligence_service
        intel_service = get_course_intelligence_service()
        if hasattr(intel_service, "invalidate_course_cache"):
            for cid in COURSE_FILES.keys():
                intel_service.invalidate_course_cache(cid)
            print("Caches invalidated via CourseIntelligenceService.")
        elif hasattr(intel_service, "_cache"):
            intel_service._cache.clear()
            print("CourseIntelligenceService internal cache cleared.")
    except Exception as e:
        print(f"Note on cache invalidation: {e}")

    # 7. Check idempotency (dry run)
    print("\nVerifying mapping idempotency (dry-run rerun)...")
    map_s3_s4_questions(apply_changes=False)

    print("\nPhase 6.4 application and verification completed successfully!")

if __name__ == "__main__":
    apply_refinements()
