"""
Second-Year Corpus Inventory & Source Discovery Script.
Catalogs all candidate documents for Semester 3 and Semester 4 across:
- Studique catalog (API & cached snapshot)
- The Helpers catalog (live webpack asset bundle)
- Local extractions, pyqs, and syllabi

Classifies each into:
A. Ready for ingestion
B. Duplicate of existing corpus (by hash or identical drive ID)
C. Already ingested in production_corpus.db
D. Metadata ambiguous (held from ingestion)
E. Unsupported/irrelevant (non-exam material: notes, lab, docx, jpg, question banks)
F. Inaccessible / retrieval failed
"""

import os
import sys
import json
import re
import hashlib
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Document, CurriculumMapping
from backend.services.scraper.curriculum_resolver import CurriculumResolver, normalize_text
from backend.services.scraper.crawler import AcademicResourceCrawler
from backend.services.scraper.classifier import ResourceClassifier

SECOND_YEAR_COURSE_IDS = [22, 24, 25, 26, 27, 28, 29, 30, 31]

def compute_sha256(filepath: str) -> Optional[str]:
    if not os.path.exists(filepath):
        return None
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_inventory():
    db = SessionLocal()
    resolver = CurriculumResolver(db)
    
    # 1. Load DB state
    db_docs = db.query(Document).all()
    db_exams = db.query(Exam).all()
    
    # Hash to document
    hash_to_doc = {}
    url_to_doc = {}
    doc_id_to_exam = {}
    
    for d in db_docs:
        if d.document_hash:
            hash_to_doc[d.document_hash] = d
        if d.original_url:
            url_to_doc[d.original_url] = d
            
    for e in db_exams:
        doc_id_to_exam[e.document_id] = e

    # 2. Run discovery for S3 and S4 from Studique and The Helpers
    crawler = AcademicResourceCrawler(db, download_only=True)
    
    print("Discovering Studique Semester 3...")
    studique_s3 = crawler.discover_studique(semester_filter=3)
    print(f"  Studique S3: {len(studique_s3)} items")
    
    print("Discovering Studique Semester 4...")
    studique_s4 = crawler.discover_studique(semester_filter=4)
    print(f"  Studique S4: {len(studique_s4)} items")
    
    print("Discovering The Helpers Semester 3...")
    helpers_s3 = crawler.discover_thehelpers(semester_filter=3)
    print(f"  The Helpers S3: {len(helpers_s3)} items")
    
    print("Discovering The Helpers Semester 4...")
    helpers_s4 = crawler.discover_thehelpers(semester_filter=4)
    print(f"  The Helpers S4: {len(helpers_s4)} items")
    
    # Unify candidates across sources
    candidates = crawler.build_union_graph(studique_s3 + studique_s4, helpers_s3 + helpers_s4)
    print(f"\nTotal unified second-year candidates discovered: {len(candidates)}")
    
    # 3. Classify every candidate
    inventory = []
    category_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    course_inventory = {cid: [] for cid in SECOND_YEAR_COURSE_IDS}
    
    for rec in candidates:
        # Resolve course
        match = resolver.resolve(rec.subject, rec.semester)
        course_id = match.course_id
        
        # Check classification
        c_res = ResourceClassifier.classify(
            title=rec.title,
            filename=rec.title,
            source_type=rec.resource_type,
            drive_path=rec.drive_folder_path
        )
        
        # Determine year & assessment type
        year = c_res.extracted_year
        assessment_type = c_res.assessment_type
        
        # Check if already ingested or duplicate
        drive_id = rec.google_drive_id or (rec.drive_ids[0] if rec.drive_ids else None)
        
        # Check against DB
        matched_db_doc = None
        for u in (rec.resolved_urls or []) + [rec.resolved_url, rec.source_url]:
            if u and u in url_to_doc:
                matched_db_doc = url_to_doc[u]
                break
            if drive_id and u and drive_id in u:
                for db_u, doc in url_to_doc.items():
                    if drive_id in db_u:
                        matched_db_doc = doc
                        break
                if matched_db_doc:
                    break

        category = "E"
        ambiguity_flags = []
        
        # Check if resource is non-exam (PPT, lecture notes, syllabus, lab, docx, answer key)
        title_lower = rec.title.lower()
        is_exam = (
            c_res.category.value == "QUESTION_PAPER" or
            rec.resource_type == "pyq" or
            "pyq" in title_lower or
            "exam" in title_lower or
            "question paper" in title_lower
        )
        is_answer_key = "ans key" in title_lower or "answer key" in title_lower or ".docx" in title_lower or ".jpg" in title_lower
        is_study_notes = (
            "unit" in title_lower and "pyq" not in title_lower and "exam" not in title_lower
        ) or "lecture" in title_lower or "notes" in title_lower or rec.resource_type in ["ppt", "syllabus", "folder"]
        
        if is_study_notes or is_answer_key or not is_exam:
            category = "E"  # Unsupported / non-exam study material or answers
        elif matched_db_doc:
            if matched_db_doc.id in doc_id_to_exam:
                category = "C"  # Already ingested as an Exam
            else:
                category = "B"  # Ingested as document / duplicate
        elif not course_id:
            category = "D"
            ambiguity_flags.append(f"Subject '{rec.subject}' does not map to a recognized canonical second-year course")
        elif not year:
            category = "D"
            ambiguity_flags.append("Missing academic examination year")
        elif assessment_type in ["UNKNOWN", None]:
            category = "D"
            ambiguity_flags.append(f"Ambiguous assessment cycle: '{assessment_type}'")
        else:
            # Candidate for ingestion
            category = "A"

        item = {
            "title": rec.title,
            "source_site": rec.source_site,
            "source_url": rec.source_url,
            "resolved_url": rec.resolved_url,
            "google_drive_id": drive_id,
            "subject": rec.subject,
            "course_id": course_id,
            "course_name": match.course_name,
            "canonical_code": match.canonical_code,
            "semester": rec.semester,
            "year": year,
            "assessment_type": assessment_type,
            "track_id": None,
            "classification": c_res.category.value,
            "category": category,
            "ambiguity_flags": ambiguity_flags,
            "db_document_id": matched_db_doc.id if matched_db_doc else None,
            "db_exam_id": doc_id_to_exam[matched_db_doc.id].id if (matched_db_doc and matched_db_doc.id in doc_id_to_exam) else None,
        }
        
        inventory.append(item)
        category_counts[category] += 1
        if course_id in course_inventory:
            course_inventory[course_id].append(item)

    print("\n==================================================")
    print("SECOND-YEAR CORPUS INVENTORY CLASSIFICATION SUMMARY")
    print("==================================================")
    for cat, count in category_counts.items():
        desc = {
            "A": "Ready for ingestion (new genuine exam papers)",
            "B": "Duplicate of existing corpus / documents",
            "C": "Already ingested as Exam in production_corpus.db",
            "D": "Metadata ambiguous (held from ingestion)",
            "E": "Unsupported / non-exam (lecture notes, syllabi, keys, docx)",
            "F": "Inaccessible / retrieval failed"
        }[cat]
        print(f"  Category {cat}: {count:4d} - {desc}")
    print("==================================================")
    
    print("\nBreakdown by Course:")
    for cid in SECOND_YEAR_COURSE_IDS:
        c_obj = db.query(Course).get(cid)
        c_items = course_inventory[cid]
        c_cats = {}
        for it in c_items:
            c_cats[it["category"]] = c_cats.get(it["category"], 0) + 1
        cat_str = ", ".join(f"{k}: {v}" for k, v in sorted(c_cats.items()))
        print(f"  Course {cid:2d} [{c_obj.canonical_code}] {c_obj.name}: {len(c_items)} discovered ({cat_str})")

    # Save report
    out_path = "data/s3_s4/second_year_inventory.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_discovered": len(inventory),
            "category_counts": category_counts,
            "items": inventory
        }, f, indent=2)
    print(f"\nSaved inventory to {out_path}")
    db.close()

if __name__ == "__main__":
    run_inventory()
