import sys, os
import re
import json
from collections import defaultdict, Counter
import fitz # PyMuPDF

sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import SessionLocal
from backend.models.core import Document, Exam, Question, Course, Unit, Topic, Section, question_topic
from sqlalchemy.orm import joinedload

print("--- STARTING COMPREHENSIVE QUESTION PAPER AUDIT ---")

# Step 1: Collect all PDF question papers on disk
corpus_pyqs = []
for root, dirs, files in os.walk('corpus'):
    for f in files:
        if f.lower().endswith('.pdf'):
            parts = root.split(os.sep)
            # check if it's in a PYQ or EXAMINATION_PAPERS folder or has pyq/ct in name
            lower_name = f.lower()
            lower_path = root.lower()
            if 'pyq' in lower_path or 'examination_papers' in lower_path or 'pyq' in lower_name or 'ct' in lower_name:
                corpus_pyqs.append(os.path.join(root, f))

data_pyqs = []
for root, dirs, files in os.walk('data'):
    for f in files:
        if f.lower().endswith('.pdf'):
            lower_path = root.lower()
            lower_name = f.lower()
            if 'priority_pyqs' in lower_path or 'cycle_tests' in lower_path or 'more_cycle_tests' in lower_path:
                data_pyqs.append(os.path.join(root, f))

all_disk_papers = sorted(list(set(corpus_pyqs + data_pyqs)))
print(f"Total physical paper PDFs identified on disk: {len(all_disk_papers)}")
print(f"  From corpus: {len(corpus_pyqs)}")
print(f"  From data downloads: {len(data_pyqs)}")

# Let's inspect headers of disk papers to see what text is printed on page 1
def inspect_pdf_text(path):
    try:
        doc = fitz.open(path)
        if len(doc) == 0:
            return ""
        text = ""
        # Check first 2 pages (in case page 1 is a cover or blank)
        for page_idx in range(min(2, len(doc))):
            text += doc[page_idx].get_text("text") + "\n"
        doc.close()
        return text
    except Exception as e:
        return ""

# Classify based on text written on the paper or filename
def classify_exam_text(header_text, filename):
    combined = (header_text + " " + filename).upper()
    
    # 1. Look for explicit Cycle Test / CT / CLA patterns
    # Check for Cycle Test 1 / CT1 / CLA 1
    is_ct1 = False
    is_ct2 = False
    is_ct3 = False
    is_endsem = False
    is_model = False
    
    if re.search(r'\b(CYCLE\s*TEST\s*[-–—]?\s*(?:1|I)\b|CT\s*[-–—]?\s*1\b|CLA\s*[-–—]?\s*(?:1|I)\b|CONTINUOUS\s*(?:LEARNING\s*)?ASSESSMENT\s*[-–—]?\s*(?:1|I)\b|CAT\s*[-–—]?\s*(?:1|I)\b|FORMATIVE\s*ASSESSMENT\s*[-–—]?\s*(?:1|I)\b|FT\s*[-–—]?\s*(?:1|I)\b)', combined):
        is_ct1 = True
    if re.search(r'\b(CYCLE\s*TEST\s*[-–—]?\s*(?:2|II)\b|CT\s*[-–—]?\s*2\b|CLA\s*[-–—]?\s*(?:2|II)\b|CONTINUOUS\s*(?:LEARNING\s*)?ASSESSMENT\s*[-–—]?\s*(?:2|II)\b|CAT\s*[-–—]?\s*(?:2|II)\b|FORMATIVE\s*ASSESSMENT\s*[-–—]?\s*(?:2|II)\b|FT\s*[-–—]?\s*(?:2|II)\b)', combined):
        is_ct2 = True
    if re.search(r'\b(CYCLE\s*TEST\s*[-–—]?\s*(?:3|III)\b|CT\s*[-–—]?\s*3\b|CLA\s*[-–—]?\s*(?:3|III)\b|CONTINUOUS\s*(?:LEARNING\s*)?ASSESSMENT\s*[-–—]?\s*(?:3|III)\b|CAT\s*[-–—]?\s*(?:3|III)\b|FORMATIVE\s*ASSESSMENT\s*[-–—]?\s*(?:3|III|IV)\b|FT\s*[-–—]?\s*(?:3|III|IV)\b)', combined):
        is_ct3 = True
        
    if re.search(r'\b(MODEL\s*EXAM|MODEL\s*EXAMINATION|PRE[- ]SEMESTER)\b', combined):
        is_model = True
        
    # Check for End Semester / University Examination / Degree Examination
    if re.search(r'\b(END\s*SEMESTER|SEMESTER\s*EXAMINATION|DEGREE\s*EXAMINATION|UNIVERSITY\s*EXAMINATION|SEMESTER\s*END|FINAL\s*EXAMINATION|ANNUAL\s*EXAMINATION)\b', combined):
        is_endsem = True
    if re.search(r'\b(MAY\s*20\d\d|DEC\s*20\d\d|NOV\s*20\d\d|JAN\s*20\d\d|JULY?\s*20\d\d|JUNE?\s*20\d\d)\b', filename.upper()) and not (is_ct1 or is_ct2 or is_ct3):
        # SRM End Sem papers are routinely named "PYQ 2023 Dec.pdf", "PYQ May 2022.pdf"
        is_endsem = True

    # Resolving ambiguities:
    if is_ct1 and not is_ct2 and not is_ct3:
        return "CT1"
    elif is_ct2 and not is_ct1 and not is_ct3:
        return "CT2"
    elif is_ct3:
        return "CT3_OR_FORMATIVE"
    elif is_ct1 and is_ct2:
        return "CT_COMPILATION"
    elif is_model:
        return "MODEL_EXAM"
    elif is_endsem:
        return "END_SEMESTER"
    else:
        return "UNKNOWN_OR_UNCLASSIFIED"

print("\nSampling classification of disk papers...")
disk_classifications = Counter()
sample_results = []
for p in all_disk_papers[:30]:
    txt = inspect_pdf_text(p)
    cat = classify_exam_text(txt, os.path.basename(p))
    disk_classifications[cat] += 1
    sample_results.append((os.path.basename(p), cat, txt[:100].replace('\n', ' ')))

for name, cat, preview in sample_results[:10]:
    print(f"[{cat:15}] {name[:40]:40} | Text: {preview[:60]}")
