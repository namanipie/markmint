import json
import re

with open("src/lib/course-resources.json", "r", encoding="utf-8") as f:
    resources = json.load(f)

# List of verified CT papers to inject into courses
CT_PAPERS_TO_ADD = [
    # Compiler Design
    {
        "courseSlug": "compiler-design",
        "title": "CT1 Faculty Question Bank (Units 1 & 2)",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1AneYgWczqDwJWZHN2bWZzX4D_x1s2tS-/view?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    {
        "courseSlug": "compiler-design",
        "title": "CT2 Core Problem Set & Important Questions (Units 3 & 4)",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1XPsCvtVbJ65ExXeqTUrPhTNEsLBiPkHR/view?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    # Discrete Mathematics
    {
        "courseSlug": "discrete-mathematics",
        "title": "CT1 Exam Papers 2024 (Units 1 & 2)",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1bYWTTc_VH3_onAAQLF5wqdReHKGhfAUW/view?usp=sharing",
        "source": "TheHelper CT Archive"
    },
    {
        "courseSlug": "discrete-mathematics",
        "title": "CT2 Exam Papers 2025 (Units 3 & 4)",
        "examType": "CT2",
        "year": 2025,
        "url": "https://drive.google.com/file/d/11AYA6S8SsDgS2gOi9RZzHCVAIxCJWsbj/view?usp=sharing",
        "source": "TheHelper CT Archive"
    },
    # Operating Systems
    {
        "courseSlug": "operating-systems",
        "title": "CT1 Authentic Exam Papers (Processes & CPU Scheduling)",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1PO-afGBfv4lTbzYTyo4lSDeVggL3ydUq/view?usp=sharing",
        "source": "GradeX CT Deck"
    },
    {
        "courseSlug": "operating-systems",
        "title": "CT2 Verified Exam Questions Archive",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1fxfimDbmsaBdgExWGSPA-B0v18zjU9Di/view",
        "source": "TheHelper CT Archive"
    },
    # Object Oriented Design and Programming
    {
        "courseSlug": "object-oriented-design-and-programming",
        "title": "CT1 Question Bank (Classes, Objects, Inheritance - Units 1 & 2)",
        "examType": "CT1",
        "year": 2023,
        "url": "https://drive.google.com/file/d/19Ej9QRZcqDCrN_1qOPCxu0gsTvVvfj98/view?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    {
        "courseSlug": "object-oriented-design-and-programming",
        "title": "CT2 Important Exam Questions (Polymorphism & Templates - Units 3 & 4)",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/14pwsNMxHBLdd2T57GuInfIJK032JDxmt/view?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    # Fundamental of Economics
    {
        "courseSlug": "fundamental-of-economics-foe",
        "title": "CT1 Question Bank with Answer Keys (Microeconomics - Units 1 & 2)",
        "examType": "CT1",
        "year": 2024,
        "url": "https://docs.google.com/document/d/1HW-C1-X8DRIdmMUOB2APuuq8YCKV1RtH/edit?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    # Philosophy of Engineering
    {
        "courseSlug": "philosophy-of-engineering",
        "title": "CT1 MCQ Test & Authentic Exam Questions 2025",
        "examType": "CT1",
        "year": 2025,
        "url": "https://drive.google.com/file/d/1locHTKR_KMWMiUWPvRvfkdtc5xOGdixF/view?usp=sharing",
        "source": "TheHelper CT Archive"
    },
    # Probability and Queueing Theory
    {
        "courseSlug": "probability-and-queueing-theory",
        "title": "CT Papers Comprehensive Compilation",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1zQh4mtmGc7YuIYe0IbfOzbjGUIH1crrz/view?usp=sharing",
        "source": "GradeX CT Deck"
    },
    # Advanced Calculus and Complex Analysis
    {
        "courseSlug": "advanced-calculus-and-complex-analysis",
        "title": "CT Exam Papers Compilation (Vector Calculus & Laplace)",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1EPidinguoZeL9azdQzBy20iik9YSaVoH/view?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    # Artificial Intelligence
    {
        "courseSlug": "artificial-intelligence",
        "title": "CT1 Question Papers & Problem Sets",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1pCG0pKs4m1zvgIs8fgLpRzcbzAm-hh3D/view?usp=sharing",
        "source": "TheHelper CT Archive"
    },
    {
        "courseSlug": "artificial-intelligence",
        "title": "CT2 Question Paper & Concept Problems",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1EsSF6vd9pbfXWPE4w3VKgxFNcsLo7mse/view?usp=sharing",
        "source": "TheHelper CT Archive"
    },
    # Electromagnetic Theory
    {
        "courseSlug": "electromagnetic-theory-quantum-mechanics-waves-and-optics",
        "title": "CT1 Exam Paper 2025",
        "examType": "CT1",
        "year": 2025,
        "url": "https://drive.google.com/file/d/1VHarprAMKjnmZda8ZxKSlf7iGYBzo70Z/view?usp=sharing",
        "source": "GradeX CT Deck"
    },
    {
        "courseSlug": "electromagnetic-theory-quantum-mechanics-waves-and-optics",
        "title": "CT2 Question Bank (Quantum Mechanics & Wave Optics)",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/18ubPMug4jRVTf36oTVcFbG7BJMwYOSPs/view?usp=drive_link",
        "source": "TheHelper CT Archive"
    },
    # Computer Networks
    {
        "courseSlug": "computer-networks",
        "title": "CT1 Important Topics & Examination Questions",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1-9uZ5Hg61AWdyCEKcJvndyeR0OH4bc9V/view",
        "source": "TheHelper CT Archive"
    },
    {
        "courseSlug": "computer-networks",
        "title": "CT2 Routing & Transport Layer Problems Archive",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1S_7_fuW3bLzUqet746meoDW8AK_e9Ovu/view",
        "source": "TheHelper CT Archive"
    },
    # Internet of Things
    {
        "courseSlug": "internet-of-things",
        "title": "CT1 Authentic PYQs & Problem Sets",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1Iizy1bV8yNpDemFB5ZMxsipzR_5xsvBC/view?usp=sharing",
        "source": "TheHelper CT Archive"
    },
    # Communicative English
    {
        "courseSlug": "communicative-english",
        "title": "CT1 Faculty Key & Exam Paper Set 1",
        "examType": "CT1",
        "year": 2024,
        "url": "https://drive.google.com/file/d/157DoB8pFlDq_SZnJxgUx2_Pp58JxcH0C/view",
        "source": "TheHelper CT Archive"
    },
    {
        "courseSlug": "communicative-english",
        "title": "CT2 Faculty Key & Exam Paper Set 2",
        "examType": "CT2",
        "year": 2024,
        "url": "https://drive.google.com/file/d/1ca1_TaELLbeS0-OYwx5SgMzvOoWbd3k0/view",
        "source": "TheHelper CT Archive"
    }
]

added_count = 0
for paper in CT_PAPERS_TO_ADD:
    slug = paper["courseSlug"]
    if slug not in resources:
        # Try finding by loose match
        for s, c in resources.items():
            if slug.replace("-", "") in s.replace("-", ""):
                slug = s
                break
    
    if slug in resources:
        course = resources[slug]
        pyqs = course.setdefault("pyqs", [])
        
        # Check if already present by url or title
        existing_urls = {p.get("url") for p in pyqs}
        existing_titles = {p.get("title", "").lower() for p in pyqs}
        
        if paper["url"] not in existing_urls and paper["title"].lower() not in existing_titles:
            m = re.search(r'/d/([a-zA-Z0-9_-]{25,})', paper["url"])
            if not m:
                m = re.search(r'id=([a-zA-Z0-9_-]{25,})', paper["url"])
            drive_id = m.group(1) if m else None
            
            new_p = {
                "title": paper["title"],
                "examType": paper["examType"],
                "year": paper["year"],
                "url": paper["url"],
                "source": paper["source"],
                "driveId": drive_id
            }
            # Prepend CT papers so they appear prominently at the top of the list
            pyqs.insert(0, new_p)
            course["pyqsCount"] = len(pyqs)
            added_count += 1
            print(f"  + Added to {course['courseName']}: {paper['title']} ({paper['examType']})")

with open("src/lib/course-resources.json", "w", encoding="utf-8") as f:
    json.dump(resources, f, indent=2, ensure_ascii=False)

print(f"\nSuccessfully added {added_count} verified CT papers into src/lib/course-resources.json")
