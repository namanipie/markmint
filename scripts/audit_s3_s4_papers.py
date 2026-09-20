import os
import pdfplumber
import re

pyq_dir = "data/s3_s4/pyqs"
papers = sorted(os.listdir(pyq_dir))
print(f"=== INSPECTING {len(papers)} PAPERS IN {pyq_dir} ===\n")

for p in papers:
    path = os.path.join(pyq_dir, p)
    try:
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            t1 = pdf.pages[0].extract_text() or ""
            lines = [l.strip() for l in t1.split("\n") if l.strip()]
            header_sample = " // ".join(lines[:4]) if lines else "NO_TEXT_EXTRACTED"
            print(f"{p:<22} | Pages: {pages:<2} | Text: {len(t1):<5} | {header_sample[:100]}")
    except Exception as e:
        print(f"{p:<22} | ERROR: {e}")
