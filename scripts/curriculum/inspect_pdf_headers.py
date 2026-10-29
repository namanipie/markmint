import json
import os
import re
import fitz

def main():
    with open("data/s3_s4/verified_new_candidates.json", "r") as f:
        data = json.load(f)

    for idx in [0, 6, 8, 10]:
        p = data["truly_new_papers"][idx]
        doc = fitz.open(p["local_temp_path"])
        print(f"=== [{idx+1}] {p['title']} ({len(doc)} pages, {p['file_size']} bytes) ===")
        doc.close()

if __name__ == "__main__":
    main()
