import os
import fitz # PyMuPDF

def extract_pdf_header(pdf_path, max_chars=1200):
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return "EMPTY_PDF"
        page = doc[0]
        text = page.get_text("text")
        doc.close()
        return text[:max_chars].strip()
    except Exception as e:
        return f"ERROR: {e}"

# Test with a few sample PDFs
sample_pdfs = [
    r"corpus\Semester_1\Calculus And Linear Algebra\PYQ\Calculus and Linear Algebra - PYQ 2023 July.pdf",
    r"corpus\Semester_1\Calculus And Linear Algebra\PYQ\Calculus And Linear Algebra - CT1 Papers 2025.pdf",
    r"corpus\Semester_1\Calculus And Linear Algebra\PYQ\Calculus And Linear Algebra - CT 1,2,3 Compilation PYQ.pdf",
    r"corpus\Semester_1\Chemistry\PYQ\Chemistry - PYQ 2023 Dec.pdf",
]

for p in sample_pdfs:
    if os.path.exists(p):
        print(f"=== {os.path.basename(p)} ===")
        header = extract_pdf_header(p, 600)
        print(header)
        print("-" * 50)
