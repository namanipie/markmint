import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import json
from backend.core.database import SessionLocal
from backend.models.core import Question
from backend.services.taxonomy_registry.registry import get_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService

db = SessionLocal()
registry = get_taxonomy_registry()
rules = registry.get_topic_rules(25)
classifier = TaxonomyClassifierService(rules)

qids = [9071, 9092, 9127, 9132, 9133, 9141, 9157, 9158, 9159, 9169, 9184, 9185, 9204, 9239, 10051]

print(f"=== Diagnosing Course 25 Specific Questions ===")
for qid in qids:
    q = db.query(Question).filter(Question.id == qid).first()
    norm = classifier.normalize_text(q.original_text)
    padded = f" {norm} "
    print(f"\nQID {qid}: {repr(q.original_text[:90])}")
    
    # Check all rules for matches
    matched = []
    rejected = []
    for r in rules:
        # Check guards
        for g in r.negative_guards:
            g_norm = classifier.normalize_text(g)
            if g_norm and f" {g_norm} " in padded:
                rejected.append((r.topic_name, g))
                break
        
        # Check strong
        s_matches = [s for s in r.strong_phrases if classifier.normalize_text(s) and f" {classifier.normalize_text(s)} " in padded]
        k_matches = [k for k in r.specific_keywords if classifier.normalize_text(k) and f" {classifier.normalize_text(k)} " in padded]
        if s_matches or k_matches:
            matched.append((r.topic_name, s_matches, k_matches))
            
    print(f"  Matched rules: {matched}")
    print(f"  Guards tripped: {rejected[:3]}")

db.close()
