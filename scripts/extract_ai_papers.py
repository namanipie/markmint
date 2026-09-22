import os
import sys
import json
import time
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv()

from backend.services.extraction.vision_extractor import VisionExtractor

INPUT_DIR = "corpus/Semester_1/Artificial Intelligence (AI)/PYQ"
OUTPUT_DIR = "data/curriculum/ai_extractions"
os.makedirs(OUTPUT_DIR, exist_ok=True)

papers = sorted(os.listdir(INPUT_DIR))
print(f"Total AI papers to extract: {len(papers)}")

for idx, p in enumerate(papers, 1):
    if not p.endswith(".pdf"):
        continue
    base_name = os.path.splitext(p)[0]
    # Clean file identifier for consistent naming: AI_2023_Dec.json etc.
    clean_stem = base_name.replace("Artificial Intelligence (AI) - PYQ ", "AI_").replace(" ", "_")
    out_file = os.path.join(OUTPUT_DIR, f"{clean_stem}.json")
    if os.path.exists(out_file):
        print(f"[{idx}/{len(papers)}] Already extracted: {clean_stem}")
        continue

    pdf_path = os.path.join(INPUT_DIR, p)
    print(f"[{idx}/{len(papers)}] Extracting {p} ({os.path.getsize(pdf_path)} bytes)...")
    try:
        res = VisionExtractor.extract_pdf(pdf_path)
        if res.successful:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(res.model_dump(), f, indent=2)
            q_count = sum(len(s.questions) for s in res.sections)
            print(f"  -> SUCCESS: {res.assessment_type} {res.year} | {len(res.sections)} sections | {q_count} questions saved to {out_file}")
        else:
            print(f"  -> FAILED: {res.error_message}")
        time.sleep(2)
    except Exception as e:
        print(f"  -> EXCEPTION: {e}")
        time.sleep(5)
