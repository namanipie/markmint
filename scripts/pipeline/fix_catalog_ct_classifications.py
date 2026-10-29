import json
import re

with open("src/lib/course-resources.json", "r", encoding="utf-8") as f:
    cr = json.load(f)

updated_count = 0
for slug, c in cr.items():
    for p in c.get("pyqs", []):
        t = p.get("title", "")
        old_type = p.get("examType")
        
        # Check CT patterns
        if re.search(r'\b(ct\s*1|cycle\s*test\s*1|cat\s*1|cla\s*1)\b', t, re.IGNORECASE):
            if old_type != "CT1":
                p["examType"] = "CT1"
                updated_count += 1
        elif re.search(r'\b(ct\s*2|cycle\s*test\s*2|cat\s*2|cla\s*2)\b', t, re.IGNORECASE):
            if old_type != "CT2":
                p["examType"] = "CT2"
                updated_count += 1
        elif re.search(r'\b(ct\s*3|cycle\s*test\s*3|cat\s*3)\b', t, re.IGNORECASE):
            if old_type != "CT2":
                p["examType"] = "CT2"
                updated_count += 1
        elif re.search(r'\b(ct\s*papers?|cycle\s*test)\b', t, re.IGNORECASE):
            if old_type not in ["CT1", "CT2"]:
                # Default general CT papers to CT1
                p["examType"] = "CT1"
                updated_count += 1
        elif re.search(r'\b(model\s*qp|model\s*paper)\b', t, re.IGNORECASE):
            if old_type not in ["CT1", "CT2"]:
                if any(k in t.lower() for k in ["set 1", "set a", "set 2", "set 3", "set 4"]):
                    p["examType"] = "CT1"
                else:
                    p["examType"] = "CT2"
                updated_count += 1

print(f"Updated {updated_count} examType classifications in course-resources.json")

# Now check CT papers per course
for slug, c in sorted(cr.items()):
    ct1 = sum(1 for p in c.get("pyqs", []) if p.get("examType") == "CT1")
    ct2 = sum(1 for p in c.get("pyqs", []) if p.get("examType") == "CT2")
    if ct1 + ct2 > 0:
        print(f"  {c['courseName']:<48} | CT1: {ct1:<2} | CT2: {ct2:<2} | Total CTs: {ct1+ct2}")

with open("src/lib/course-resources.json", "w", encoding="utf-8") as f:
    json.dump(cr, f, indent=2, ensure_ascii=False)
