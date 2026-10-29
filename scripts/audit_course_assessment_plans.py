import os
import glob
import zipfile
import xml.etree.ElementTree as ET
import fitz # PyMuPDF
import json

print("=== 1. AUDITING TAXONOMY REGISTRY SOURCES ===")
defs_dir = "backend/services/taxonomy_registry/definitions"
if os.path.exists(defs_dir):
    for fn in os.listdir(defs_dir):
        if fn.endswith(".json"):
            fp = os.path.join(defs_dir, fn)
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
                course_id = data.get("course_id")
                course_name = data.get("course_name")
                src = data.get("provenance", {}).get("authoritative_source", "UNKNOWN")
                print(f"Course {course_id}: {course_name} -> {src}")

print("\n=== 2. EXTRACTING MATHS ASSESSMENT PLAN FROM DOCX ===")
math_docx = r"data/1 Year/MATHS/detailed sylabbus.docx"
if os.path.exists(math_docx):
    with zipfile.ZipFile(math_docx) as z:
        tree = ET.fromstring(z.read("word/document.xml"))
        # Group by paragraph / rows
        # Let's extract all text chunks
        texts = []
        for elem in tree.iter():
            if elem.tag.endswith('p'):
                p_text = "".join(elem.itertext()).strip()
                if p_text:
                    texts.append(p_text)
        print(f"Total paragraphs in Maths docx: {len(texts)}")
        # Look for Assessment Plan in texts
        recording = False
        assessment_lines = []
        for line in texts:
            if "assessment plan" in line.lower() or "learning assessment" in line.lower():
                recording = True
            if recording:
                assessment_lines.append(line)
                if len(assessment_lines) > 60:
                    break
        print("\n--- Maths Assessment Section Snippet ---")
        for l in assessment_lines[:40]:
            print(l)

print("\n=== 3. EXTRACTING CHEMISTRY LESSON PLAN FROM PDF ===")
chem_pdf = r"data/1 Year/CHEMISTRY/Lesson plan.pdf"
if os.path.exists(chem_pdf):
    doc = fitz.open(chem_pdf)
    print(f"Chemistry Lesson plan page count: {len(doc)}")
    for page_idx in range(min(5, len(doc))):
        page = doc[page_idx]
        text = page.get_text()
        print(f"--- Chemistry Page {page_idx + 1} ---")
        for line in text.split("\n"):
            if any(k in line.lower() for k in ["assess", "test", "cycle", "ft", "cla", "mark", "weightage", "unit"]):
                print(line)

print("\n=== 4. SEARCHING ALL PDFS IN DATA/ FOR ASSESSMENT PLANS ===")
for root, dirs, files in os.walk("data"):
    for f in files:
        if f.endswith(".pdf"):
            full_p = os.path.join(root, f)
            try:
                d = fitz.open(full_p)
                for i, page in enumerate(d):
                    txt = page.get_text()
                    low = txt.lower()
                    if "assessment plan" in low or "learning assessment" in low or "detailed test plan" in low or "overall assessment plan" in low or "course assessment plan" in low:
                        print(f"\n[FOUND MATCH] Page {i+1} in {full_p}:")
                        for line in txt.split("\n")[:25]:
                            if line.strip():
                                print("  ", line.strip())
                        break
            except Exception as e:
                pass
