import os
import json
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

client = genai.Client()

all_sections = [
    {"name": "PART - A", "instructions": "Answer all questions", "questions": []},
    {"name": "PART - B", "instructions": "Answer all questions", "questions": []},
    {"name": "PART - C", "instructions": "Answer all questions", "questions": []}
]

prompt_template = """Extract all examination questions from this page into a JSON array of objects.
Each object must have:
- "number": string, question number (e.g. "1", "11a", "11b")
- "text": string, full question text with options or math formulas
- "marks": float or null, marks allocated
- "is_or_choice": boolean, true if this is an OR alternative question
- "section": string, either "PART - A", "PART - B", or "PART - C"
"""

for page_idx in range(1, 5):
    img_path = f"data/s3_s4/pyqs/dsa_dec_imgs/page_{page_idx}.png"
    print(f"Extracting page {page_idx}...")
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            prompt_template
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    items = json.loads(res.text)
    print(f"  Page {page_idx}: extracted {len(items)} items")

    for item in items:
        sec_name = item.get("section", "").upper()
        target_sec = all_sections[0]
        if "B" in sec_name or (isinstance(item.get("number"), str) and any(item["number"].startswith(str(n)) for n in range(11, 16))):
            target_sec = all_sections[1]
        elif "C" in sec_name or (isinstance(item.get("number"), str) and any(item["number"].startswith(str(n)) for n in range(16, 21))):
            target_sec = all_sections[2]

        q_dict = {
            "number": str(item.get("number", "?")).strip("."),
            "text": item.get("text", ""),
            "marks": float(item["marks"]) if item.get("marks") and str(item["marks"]).replace('.','',1).isdigit() else None,
            "subquestions": []
        }
        if item.get("is_or_choice"):
            if target_sec["questions"]:
                target_sec["questions"][-1]["or_alternative"] = q_dict
            else:
                target_sec["questions"].append(q_dict)
        else:
            target_sec["questions"].append(q_dict)

result_doc = {
    "metadata": {
        "assessment_type": "END_SEM",
        "year": 2023
    },
    "sections": [s for s in all_sections if s["questions"]]
}

out_path = "data/s3_s4/extractions/DSA_2023_Dec.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result_doc, f, indent=2)

print(f"SUCCESS: Written {out_path} with {sum(len(s['questions']) for s in result_doc['sections'])} questions.")
