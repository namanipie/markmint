import os, re, json
import fitz # PyMuPDF
from collections import defaultdict, Counter

print("--- FULL SCAN OF ALL QUESTION PAPER PDFS ON DISK ---")

# Gather all PDFs that could be exam papers
exam_pdfs = []

# Scan corpus
for root, dirs, files in os.walk('corpus'):
    for f in files:
        if f.lower().endswith('.pdf'):
            path = os.path.join(root, f)
            lower_path = path.lower()
            if any(k in lower_path for k in ['pyq', 'examination_papers', 'cycle_test', 'ct1', 'ct2']):
                exam_pdfs.append(('corpus', path))

# Scan data
for root, dirs, files in os.walk('data'):
    for f in files:
        if f.lower().endswith('.pdf'):
            path = os.path.join(root, f)
            lower_path = path.lower()
            if any(k in lower_path for k in ['priority_pyqs', 'cycle_tests', 'more_cycle_tests']):
                exam_pdfs.append(('data', path))

print(f"Total candidate PDF exam papers found: {len(exam_pdfs)}")

# Function to extract header details
def analyze_pdf_header(path):
    try:
        doc = fitz.open(path)
        if len(doc) == 0:
            return {"error": "empty", "page_count": 0}
        
        # Read up to first 3 pages
        full_text = ""
        for i in range(min(3, len(doc))):
            full_text += doc[i].get_text("text") + "\n"
        
        doc.close()
        
        header_text = full_text[:2000].strip()
        
        # Detect Course Code (e.g. 21MAB101T, 18CSC304J, 21CYB101J)
        code_match = re.search(r'\b(18[A-Z]{2,4}\d{3}[A-Z]|21[A-Z]{2,4}\d{3}[A-Z])\b', header_text, re.IGNORECASE)
        course_code = code_match.group(1).upper() if code_match else None
        
        # Detect Max Marks
        marks_match = re.search(r'(?:Total\s*Marks|Max(?:imum)?\s*Marks)\s*[:=-]?\s*(\d+)', header_text, re.IGNORECASE)
        max_marks = int(marks_match.group(1)) if marks_match else None
        
        # Detect Duration / Time
        time_match = re.search(r'(?:Time|Duration)\s*[:=-]?\s*([0-9.]+\s*(?:Hours?|Hrs?|Minutes?|Mins?))', header_text, re.IGNORECASE)
        duration = time_match.group(1).strip() if time_match else None
        
        # Detect Exam String written on paper
        exam_string = None
        for pat in [
            r'(B\.Tech\.?\s*(?:/\s*M\.Tech\.?)?\s*DEGREE\s*EXAMINATION[^\n]*)',
            r'(SEMESTER\s*EXAMINATION[^\n]*)',
            r'(END\s*SEMESTER\s*EXAMINATION[^\n]*)',
            r'(CYCLE\s*TEST\s*[-–—]?\s*(?:I|II|III|1|2|3)[^\n]*)',
            r'(CONTINUOUS\s*(?:LEARNING\s*)?ASSESSMENT\s*[-–—]?\s*(?:I|II|III|1|2|3)[^\n]*)',
            r'(FORMATIVE\s*ASSESSMENT\s*[-–—]?\s*(?:I|II|III|IV|1|2|3|4)[^\n]*)',
            r'(MODEL\s*EXAMINATION[^\n]*)',
            r'(CLA\s*[-–—]?\s*(?:1|2|3|I|II|III)[^\n]*)',
            r'(FT\s*[-–—]?\s*(?:1|2|3|4|I|II|III|IV)[^\n]*)'
        ]:
            m = re.search(pat, header_text, re.IGNORECASE)
            if m:
                exam_string = m.group(1).strip()
                break
                
        return {
            "page_count": len(doc),
            "course_code": course_code,
            "max_marks": max_marks,
            "duration": duration,
            "exam_string": exam_string,
            "has_text": len(full_text.strip()) > 50,
            "preview": header_text[:300].replace('\n', ' ')
        }
    except Exception as e:
        return {"error": str(e), "page_count": 0}

# Process all PDFs
pdf_results = []
exam_str_counts = Counter()
category_counts = Counter()

for src, p in exam_pdfs:
    fname = os.path.basename(p)
    folder = os.path.dirname(p)
    info = analyze_pdf_header(p)
    
    # Classify into standard SRMIST assessment cycles
    exam_str = (info.get("exam_string") or "").upper()
    comb = (exam_str + " " + fname + " " + folder).upper()
    
    if any(k in comb for k in ['CT1', 'CT-1', 'CYCLE TEST - I', 'CYCLE TEST - 1', 'CYCLE TEST 1', 'CYCLE TEST I', 'CLA-1', 'CLA1', 'FT1', 'FT-1', 'FT-I', 'CONTINUOUS ASSESSMENT TEST - I']):
        if 'COMPILATION' in comb or '1,2' in comb or '1, 2' in comb:
            cat = 'CT_COMPILATION'
        else:
            cat = 'CT1'
    elif any(k in comb for k in ['CT2', 'CT-2', 'CYCLE TEST - II', 'CYCLE TEST - 2', 'CYCLE TEST 2', 'CYCLE TEST II', 'CLA-2', 'CLA2', 'CLAT-2', 'CLA-T2', 'FT2', 'FT-2', 'FT-II', 'FT 2', 'CONTINUOUS ASSESSMENT TEST - II']):
        cat = 'CT2'
    elif any(k in comb for k in ['CT3', 'CT-3', 'CYCLE TEST - III', 'CYCLE TEST - 3', 'CYCLE TEST 3', 'CYCLE TEST III', 'FT IV', 'FT-IV', 'CLA-3']):
        cat = 'CT3'
    elif any(k in comb for k in ['MODEL', 'PRE-SEMESTER', 'MOCK']):
        cat = 'MODEL_EXAM'
    elif any(k in comb for k in ['END_SEM', 'ENDSEM', 'END SEMESTER', 'SEMESTER EXAMINATION', 'DEGREE EXAMINATION', 'UNIVERSITY EXAMINATION', 'PYQ']):
        cat = 'END_SEMESTER'
    else:
        cat = 'OTHER'
        
    category_counts[cat] += 1
    if info.get("exam_string"):
        exam_str_counts[info["exam_string"][:40]] += 1
        
    pdf_results.append({
        "source": src,
        "filename": fname,
        "path": p,
        "category": cat,
        "detected_course_code": info.get("course_code"),
        "max_marks": info.get("max_marks"),
        "duration": info.get("duration"),
        "exam_string_on_paper": info.get("exam_string"),
        "has_embedded_text": info.get("has_text")
    })

print(f"\nCategorization of all {len(exam_pdfs)} candidate PDF files:")
for cat, cnt in category_counts.most_common():
    print(f"  {cat:20}: {cnt} PDFs")

print(f"\nTop Exam Strings physically printed on paper headers:")
for s, cnt in exam_str_counts.most_common(15):
    print(f"  '{s}': {cnt}")

with open('data/disk_pdf_audit_results.json', 'w') as f:
    json.dump({
        'categories': dict(category_counts),
        'top_exam_strings': dict(exam_str_counts.most_common(30)),
        'results': pdf_results
    }, f, indent=2)

print("\nWrote disk audit results to data/disk_pdf_audit_results.json")
