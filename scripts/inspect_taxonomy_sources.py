import json
import glob

for p in sorted(glob.glob("backend/services/taxonomy_registry/definitions/*.json")):
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
        c = d.get("course", {})
        prov = d.get("provenance", {})
        print(f"Course {c.get('id')}: {c.get('canonical_code')} - {c.get('name')} | Source: {prov.get('source_document')}")
