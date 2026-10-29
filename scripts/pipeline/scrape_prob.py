"""
Download Course 22 (Probability and Statistics) study materials and PYQs from Studique.
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.pipeline.scrape_tbvp_pqt import download_gdrive, compute_sha256
from backend.services.scraper.downloader import sanitize_filesystem_name

COURSE_NAME = "Probability and Statistics"
SEM = 2

RESOURCES = [
    # PPTs
    ("STUDY_MATERIAL", "Unit 1", "1dEu4Lux4S4w8eOIkTD9tWxFNxt8hVfxJ"),
    ("STUDY_MATERIAL", "Unit 2", "1X4wr35kRQaNDrUHTNEZNSPbzMBqonOhL"),
    ("STUDY_MATERIAL", "Unit 3.1", "10MlLfIUYCuQ8pGSgFOE_ywkwG4Q094at"),
    ("STUDY_MATERIAL", "Unit 3.2", "1FH6M2ciesM32X7pEJnz_RVHo8l-UyzkP"),
    ("STUDY_MATERIAL", "Unit 4", "1MsuHOJMBeQHao6nbuS2TAmmAYYDqcdhA"),
    ("STUDY_MATERIAL", "Unit 5", "1L97HIeUFa99MMlLNwLdxS1GDCRh4y0lu"),
    # PYQs
    ("EXAMINATION_PAPERS", "PYQ 2023 Dec", "1vhGf3yXrXiA0es2eEcA8Dhwq3Vnp4M5M"),
    ("EXAMINATION_PAPERS", "PYQ 2023 July", "1PzrH2s41hNz-8QnvxB1t1EBdv0FT0B6l"),
    ("EXAMINATION_PAPERS", "PYQ 2023 May", "1eEMW52S34A6bUsMOvcaq4SnghJplJWOv"),
]

def download_prob():
    print(f"Downloading resources for {COURSE_NAME} (Course 22)...")
    success = 0
    for rtype, title, fkey in RESOURCES:
        safe_title = sanitize_filesystem_name(f"{COURSE_NAME} - {title}")
        dest = os.path.join("corpus", f"Semester_{SEM}", COURSE_NAME, rtype, f"{safe_title}.pdf")
        ok = download_gdrive(fkey, dest)
        if ok:
            success += 1
            print(f"  [OK] {title} -> {dest}")
        else:
            print(f"  [FAIL] {title}")
    print(f"Completed {success}/{len(RESOURCES)} downloads for Course 22.")

if __name__ == "__main__":
    download_prob()
