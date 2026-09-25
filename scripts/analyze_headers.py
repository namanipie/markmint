import json
import re

def analyze():
    with open('scratch_missing_headers.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    print(f"Total missing exams: {len(items)}\n")
    
    resolved_count = 0
    unresolved_count = 0
    
    for it in items:
        eid = it['exam_id']
        cname = it['course']
        atype = it['current_atype']
        title = it['title']
        pages = it['pages']
        header = it['header_sample']
        
        # Improved patterns
        # 1. Academic Year e.g. Academic Year: 2022-2023 or AcademicYear:2022-23
        ay_match = re.search(r'Academic\s*Year\s*[:\-]?\s*(20\d\d)\s*[-–/]\s*(\d{2,4})', header, re.IGNORECASE)
        
        # 2. Month Year e.g. November 2022, Nov 2023, May 2024, Sep 2023, etc.
        month_match = re.search(r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,\.\s\-/]+(20[12]\d)\b', header, re.IGNORECASE)
        
        # 3. Explicit date DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY
        date_match = re.search(r'\b(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](20[12]\d)\b', header)
        
        # 4. Exam header year e.g. "Cycle Test - I - 2023", "Semester Examination - November / December - 2021"
        exam_yr_match = re.search(r'(?:Semester\s+Examination|Cycle\s+Test|Model\s+Examination|Assessment\s+Test)[\s\w\-/–—,]+(20[12]\d)\b', header, re.IGNORECASE)

        # 5. Title / filename explicit year
        title_ay = re.search(r'\b(20\d\d)\s*[-–/]\s*(\d{2,4})\b', title)
        title_yr = re.search(r'\b(20[12]\d)\b', title)

        # Evidence gathering
        evidences = []
        cand_year = None
        cand_atype = atype
        status = "UNRESOLVED"

        if ay_match:
            y1 = int(ay_match.group(1))
            cand_year = y1  # We will evaluate calendar vs academic year semantics
            evidences.append(f"AY_in_header: '{ay_match.group(0)}' (starts {y1})")
            status = "RESOLVED_EXPLICIT"
        elif date_match:
            cand_year = int(date_match.group(3))
            evidences.append(f"Date_in_header: '{date_match.group(0)}' (year {cand_year})")
            status = "RESOLVED_EXPLICIT"
        elif month_match:
            cand_year = int(month_match.group(2))
            evidences.append(f"Month_in_header: '{month_match.group(0)}' (year {cand_year})")
            status = "RESOLVED_EXPLICIT"
        elif exam_yr_match:
            cand_year = int(exam_yr_match.group(1))
            evidences.append(f"Exam_header_year: '{exam_yr_match.group(0)}' (year {cand_year})")
            status = "RESOLVED_EXPLICIT"
        elif title_ay:
            cand_year = int(title_ay.group(1))
            evidences.append(f"AY_in_title: '{title_ay.group(0)}'")
            status = "RESOLVED_STRONG"
        elif title_yr:
            # Check if title_yr is part of course code like 21CSC101T or 18PYB103J
            course_code_match = re.search(r'\b(18|21)[A-Z]{2,4}\d{3,4}[A-Z]?\b', title)
            if not course_code_match or str(title_yr.group(1)) not in course_code_match.group(0):
                cand_year = int(title_yr.group(1))
                evidences.append(f"Year_in_title: '{title_yr.group(0)}'")
                status = "RESOLVED_STRONG"

        if status.startswith("RESOLVED"):
            resolved_count += 1
        else:
            unresolved_count += 1

        print(f"[{status}] Exam {eid} | {cname}")
        print(f"  Title: {title}")
        print(f"  Cand Year: {cand_year} | Current Type: {atype}")
        if evidences:
            print(f"  Evidence: {'; '.join(evidences)}")
        else:
            print(f"  Header Snippet: {header[:140]}")
        print()

    print(f"\nSUMMARY: Resolved = {resolved_count}, Unresolved = {unresolved_count}, Total = {len(items)}")

if __name__ == '__main__':
    analyze()
