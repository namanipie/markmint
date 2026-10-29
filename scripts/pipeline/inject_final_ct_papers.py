import json
import re

with open("src/lib/course-resources.json", "r", encoding="utf-8") as f:
    cr = json.load(f)

more_ct_papers = [
    ("compiler-design", "CT1 Question Bank (Units 1 & 2)", "CT1", 2024, "https://drive.google.com/file/d/1AneYgWczqDwJWZHN2bWZzX4D_x1s2tS-/view?usp=drive_link"),
    ("compiler-design", "CT2 Important Problem Set (Units 3 & 4)", "CT2", 2024, "https://drive.google.com/file/d/1XPsCvtVbJ65ExXeqTUrPhTNEsLBiPkHR/view?usp=drive_link"),
    ("object-oriented-design-and-programming", "CT1 Question Bank (Units 1 & 2)", "CT1", 2024, "https://drive.google.com/file/d/19Ej9QRZcqDCrN_1qOPCxu0gsTvVvfj98/view?usp=drive_link"),
    ("object-oriented-design-and-programming", "CT2 Important Exam Questions (Units 3 & 4)", "CT2", 2024, "https://drive.google.com/file/d/14pwsNMxHBLdd2T57GuInfIJK032JDxmt/view?usp=drive_link"),
    ("fundamental-of-economics", "CT1 Question Bank with Answer Keys", "CT1", 2024, "https://docs.google.com/document/d/1HW-C1-X8DRIdmMUOB2APuuq8YCKV1RtH/edit?usp=drive_link"),
    ("philosophy-of-engineering", "CT1 MCQ Test & Exam Questions 2025", "CT1", 2025, "https://drive.google.com/file/d/1locHTKR_KMWMiUWPvRvfkdtc5xOGdixF/view?usp=sharing"),
    ("internet-of-things", "CT1 Authentic PYQs & Problem Sets", "CT1", 2024, "https://drive.google.com/file/d/1Iizy1bV8yNpDemFB5ZMxsipzR_5xsvBC/view?usp=sharing"),
    ("electromagnetic-theory-and-quantum-mechanics", "CT1 Exam Paper 2025", "CT1", 2025, "https://drive.google.com/file/d/1VHarprAMKjnmZda8ZxKSlf7iGYBzo70Z/view?usp=sharing"),
    ("electromagnetic-theory-and-quantum-mechanics", "CT2 Question Bank (Quantum Mechanics & Wave Optics)", "CT2", 2024, "https://drive.google.com/file/d/18ubPMug4jRVTf36oTVcFbG7BJMwYOSPs/view?usp=drive_link"),
    ("operating-systems", "CT2 Verified Exam Questions Archive", "CT2", 2024, "https://drive.google.com/file/d/1fxfimDbmsaBdgExWGSPA-B0v18zjU9Di/view",),
    ("discrete-mathematics", "CT2 Exam Papers 2025 (Units 3 & 4)", "CT2", 2025, "https://drive.google.com/file/d/11AYA6S8SsDgS2gOi9RZzHCVAIxCJWsbj/view?usp=sharing",),
]

added = 0
for slug, title, cyc, yr, url in more_ct_papers:
    if slug in cr:
        c = cr[slug]
        pyqs = c.setdefault("pyqs", [])
        existing_urls = {p.get("url") for p in pyqs}
        if url not in existing_urls:
            drive_id = url.split("/d/")[1].split("/")[0] if "/d/" in url else None
            pyqs.insert(0, {
                "title": title,
                "examType": cyc,
                "year": yr,
                "url": url,
                "source": "TheHelper CT Archive",
                "driveId": drive_id
            })
            c["pyqsCount"] = len(pyqs)
            added += 1
            print(f"Added {cyc} to {c['courseName']}: {title}")

with open("src/lib/course-resources.json", "w", encoding="utf-8") as f:
    json.dump(cr, f, indent=2, ensure_ascii=False)

print(f"Added {added} additional verified papers. Total courses with CT papers:")
for slug, c in sorted(cr.items()):
    ct1 = sum(1 for p in c.get("pyqs", []) if p.get("examType") == "CT1")
    ct2 = sum(1 for p in c.get("pyqs", []) if p.get("examType") == "CT2")
    if ct1 + ct2 > 0:
        print(f"  {c['courseName']:<48} | CT1: {ct1:<2} | CT2: {ct2:<2} | Total: {ct1+ct2}")
