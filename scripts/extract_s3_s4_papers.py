import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import time
from dotenv import load_dotenv

load_dotenv()

from backend.services.extraction.vision_extractor import VisionExtractor

INPUT_DIR = "data/s3_s4/pyqs"
OUTPUT_DIR = "data/s3_s4/extractions"
os.makedirs(OUTPUT_DIR, exist_ok=True)

papers = sorted(os.listdir(INPUT_DIR))
print(f"Total papers to extract: {len(papers)}")

for idx, p in enumerate(papers, 1):
    base_name = os.path.splitext(p)[0]
    out_file = os.path.join(OUTPUT_DIR, f"{base_name}.json")
    if os.path.exists(out_file):
        print(f"[{idx}/{len(papers)}] Already extracted: {base_name}")
        continue

    pdf_path = os.path.join(INPUT_DIR, p)
    print(f"[{idx}/{len(papers)}] Extracting {p} ({os.path.getsize(pdf_path)} bytes)...")
    try:
        res = VisionExtractor.extract_pdf(pdf_path)
        if res.successful:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(res.model_dump(), f, indent=2)
            q_count = sum(len(s.questions) for s in res.sections)
            print(f"  -> SUCCESS: {res.assessment_type} {res.year} | {len(res.sections)} sections | {q_count} questions")
        else:
            print(f"  -> FAILED: {res.error_message}")
        # Brief pause between Gemini API calls
        time.sleep(2)
    except Exception as e:
        print(f"  -> EXCEPTION: {e}")
        time.sleep(5)
