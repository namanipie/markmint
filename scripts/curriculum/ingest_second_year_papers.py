"""
Authoritative ingestion script for newly verified Second-Year exam papers:
1. Course 26 (SEM3-COA): Computer Organization and Architecture - NOV 2024 (32 questions)
2. Course 29 (SEM4-AI):  Artificial Intelligence - MAY 2025 (32 questions)

Guarantees:
- Document record creation with strict SHA-256 deduplication and source provenance
- Exam, Section, Question records creation preserving full hierarchy and marks
- Topic mapping through authoritative declarative TaxonomyRegistry
- QuestionFamily assignment enforcing course-scoped isolation and UNIQUE question_id
- Intelligence cache invalidation across Tier 1 (memory) and Tier 2 (DB)
- Transaction atomicity: commit only on full success
"""

import os
import sys
import json
from typing import Dict, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Document, Exam, Section, Question
from backend.services.document import DocumentService
from backend.services.scraper.post_processor import PostIngestionPipeline

PAPERS_TO_INGEST = [
    {
        "course_id": 26,
        "course_code": "SEM3-COA",
        "subject_name": "Computer Organization and Architecture",
        "title": "Computer Organization and Architecture - NOV 2024 Examination Paper",
        "source": "TheHelpers",
        "source_url": "https://thehelpers.tech/semesters/3/subjects/Computer%20Organization%20And%20Architecture",
        "resolved_url": "https://drive.google.com/uc?export=download&id=1xME6KQsvbfb1ykeBReHxtDI2f-Le7Iiv",
        "document_hash": "28b1c826639891823eb41a1eb757970d49488a033f2cfdf44a86fa0d15e21937",
        "semester": "3",
        "year": 2024,
        "term": "NOV",
        "assessment_type": "END_SEM",
        "extraction_file": "data/s3_s4/extractions/COA_2024_Nov.json",
    },
    {
        "course_id": 29,
        "course_code": "SEM4-AI",
        "subject_name": "Artificial Intelligence",
        "title": "Artificial Intelligence (AI) - PYQ 2025 May",
        "source": "Studique",
        "source_url": "https://www.studique.in/unitwise#Artificial%20Intelligence%20%28AI%29",
        "resolved_url": "https://drive.google.com/uc?export=download&id=1cUcovEHJw87bAWBs5KTYuUFY9ml7PUvd",
        "document_hash": "3f69052a1d44d73a2d784a9a10d142c3e619d43edf1823bb13e3b367f8b4deed",
        "semester": "4",
        "year": 2025,
        "term": "MAY",
        "assessment_type": "END_SEM",
        "extraction_file": "data/curriculum/ai_extractions/AI_2025_May.json",
    },
    {
        "course_id": 24,
        "course_code": "SEM3-DSA",
        "subject_name": "Data Structures and Algorithms",
        "title": "Data Structures and Algorithms - NOV 2024 Examination Paper",
        "source": "TheHelpers",
        "source_url": "https://thehelpers.tech/semesters/3/subjects/Data%20Structures%20And%20Algorithm",
        "resolved_url": "https://drive.google.com/uc?export=download&id=15tLL8TPKLzANOT0A5dvfR4VPSIGZ7dcs",
        "document_hash": "203b4aa1de915b24731dd7206fb75350721f41e5af781cda232d5ab550a044b4",
        "semester": "3",
        "year": 2024,
        "term": "NOV",
        "assessment_type": "END_SEM",
        "extraction_file": "data/s3_s4/extractions/DSA_2024_Nov.json",
    },
    {
        "course_id": 25,
        "course_code": "SEM3-OS",
        "subject_name": "Operating Systems",
        "title": "Operating Systems - NOV 2024 Examination Paper",
        "source": "TheHelpers",
        "source_url": "https://thehelpers.tech/semesters/3/subjects/Operating%20Systems",
        "resolved_url": "https://drive.google.com/uc?export=download&id=1IvpFfDutXhVFu_JmvnB13qK7E0F1eQQU",
        "document_hash": "e4896aaffcf5f34b4fa3d1f08e5b74db7f8c58819c3d543292e6ed81d30b6e04",
        "semester": "3",
        "year": 2024,
        "term": "NOV",
        "assessment_type": "END_SEM",
        "extraction_file": "data/s3_s4/extractions/OS_2024_Nov.json",
    },
    {
        "course_id": 27,
        "course_code": "SEM4-DAA",
        "subject_name": "Design and Analysis of Algorithms",
        "title": "Design and Analysis of Algorithms - MAY 2025 Examination Paper",
        "source": "TheHelpers",
        "source_url": "https://thehelpers.tech/semesters/4/subjects/Design%20And%20Analysis%20Of%20Algorithms",
        "resolved_url": "https://drive.google.com/uc?export=download&id=1bjjVF4ZY8KT0FwOb7Z-yU5isqnupo_Xx",
        "document_hash": "2f8d329ae3dacfed15444feab69925a6b254eeea0f2944484b99595841ffb437",
        "semester": "4",
        "year": 2025,
        "term": "MAY",
        "assessment_type": "END_SEM",
        "extraction_file": "data/s3_s4/extractions/DAA_2025_May.json",
    },
    {
        "course_id": 22,
        "course_code": "SEM4-PROB",
        "subject_name": "Probability and Statistics",
        "title": "Probability and Statistics - MAY 2024 Examination Paper",
        "source": "TheHelpers",
        "source_url": "https://thehelpers.tech/semesters/4/subjects/Probability%20%26%20Applied%20Statistics",
        "resolved_url": "https://drive.google.com/uc?export=download&id=1Pz6a_Pdpg1QUqQ8dbaRtpW5fB6V2XF6Q",
        "document_hash": "6ba2687c7f0f3145ea049a1f432c3f141bf4898cfa2694c223a3912c0d8d4a5c",
        "semester": "4",
        "year": 2024,
        "term": "MAY",
        "assessment_type": "END_SEM",
        "extraction_file": "data/s3_s4/extractions/PROB_2024_May.json",
    },
]

def ingest_papers():
    db = SessionLocal()
    doc_service = DocumentService(db, auto_commit=False)
    pipeline = PostIngestionPipeline(db)
    
    summary = []
    
    try:
        print("==================================================")
        print("AUTHORITATIVE SECOND-YEAR EXAM INGESTION PIPELINE")
        print("==================================================\n")
        
        for p in PAPERS_TO_INGEST:
            print(f"--> Ingesting Course {p['course_id']} [{p['course_code']}]: {p['title']}")
            
            # 1. Document record (deduplication check)
            existing_doc = db.query(Document).filter(Document.document_hash == p["document_hash"]).first()
            if existing_doc:
                doc = existing_doc
                print(f"    Document already exists (ID: {doc.id})")
            else:
                doc = doc_service.get_or_create_document(
                    document_hash=p["document_hash"],
                    source=p["source"],
                    original_url=p["source_url"],
                    title=p["title"],
                    semester=p["semester"],
                    subject=p["subject_name"],
                    resource_type="QUESTION_PAPER",
                    year=p["year"],
                    exam_type=p["assessment_type"]
                )
                db.flush()
                print(f"    Created Document #{doc.id}")
                
            # Provenance
            doc_service.add_provenance(
                document_id=doc.id,
                source_site=p["source"],
                source_url=p["source_url"],
                resolved_url=p["resolved_url"],
                source_priority="PRIMARY_SOURCE"
            )
            
            # 2. Check if Exam already imported
            existing_exam = db.query(Exam).filter(Exam.document_id == doc.id).first()
            if existing_exam:
                exam = existing_exam
                print(f"    Exam already exists (ID: {exam.id})")
            else:
                # Load extraction data
                with open(p["extraction_file"], "r", encoding="utf-8") as f:
                    ext_data = json.load(f)
                    
                # Import exam extraction
                exam = doc_service.import_exam_extraction(
                    document_id=doc.id,
                    course_id=p["course_id"],
                    year=p["year"],
                    term=p["term"],
                    extraction_data={
                        **ext_data,
                        "year": p["year"],
                        "assessment_type": p["assessment_type"]
                    }
                )
                print(f"    Imported Exam #{exam.id} with {len(exam.sections)} sections")
            
            # Count questions
            q_count = db.query(Question).join(Section).filter(Section.exam_id == exam.id).count()
            print(f"    Total questions created: {q_count}")
            
            # 4. Authoritative post-ingestion: topic mapping, families, cache invalidation
            print("    Running PostIngestionPipeline...")
            post_summary = pipeline.process_exam(
                exam_id=exam.id,
                course_id=p["course_id"],
                track_id=None,
                auto_commit=False # We commit transaction at the end!
            )
            print(f"    PostIngestion summary: {post_summary}")
            
            summary.append({
                "course_id": p["course_id"],
                "course_code": p["course_code"],
                "exam_id": exam.id,
                "document_id": doc.id,
                "questions_count": q_count,
                "post_summary": post_summary
            })
            print()
            
        # Commit transaction atomically
        db.commit()
        print("==================================================")
        print("INGESTION COMMITTED SUCCESSFULLY!")
        print("==================================================")
        
        # Post-commit cache invalidation across tiers
        for p in PAPERS_TO_INGEST:
            evicted = pipeline.invalidate_cache(p["course_id"])
            print(f"Cache invalidated for Course {p['course_id']} [{p['course_code']}]: {evicted} entries evicted")
            
        return summary
        
    except Exception as e:
        db.rollback()
        print(f"FATAL: Ingestion failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    ingest_papers()
