import json
import sys
import os
from pathlib import Path

# Add the root directory to the python path so we can import backend modules
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from backend.core.database import SessionLocal
from backend.models.core import Course, Unit, Topic

def ingest_data():
    dump_file = Path(__file__).parent / "competitor_dump.json"
    
    if not dump_file.exists():
        print(f"[-] Error: Could not find {dump_file}")
        print("[-] Please run competitor_scraper.py first to generate the data.")
        return

    print("="*50)
    print("MARK-MINT DATA INGESTION PROTOCOL INITIALIZED")
    print("="*50)

    try:
        with open(dump_file, "r") as f:
            courses_data = json.load(f)
    except Exception as e:
        print(f"[-] Failed to load JSON: {e}")
        return

    print(f"[*] Loaded {len(courses_data)} courses from dump file.")
    
    db = SessionLocal()
    try:
        success_count = 0
        for data in courses_data:
            course_title = data.get('title', 'Unknown Course')
            
            # Check if course already exists to prevent duplicates
            existing = db.query(Course).filter(Course.name == course_title).first()
            if existing:
                print(f"  [~] Skipping '{course_title}' - Already exists in database.")
                continue
                
            print(f"  [+] Injecting: {course_title}")
            
            # Create the new course
            # Note: We assign a default branch/semester or leave them blank for manual sorting later
            new_course = Course(
                name=course_title,
                code=course_title[:10].upper().replace(" ", ""), # Generate a temporary code
                credits=3, # Default
                is_active=True
            )
            db.add(new_course)
            db.flush() # Flush to get the course ID
            
            # In a full implementation, we would iterate through data['units'] and add Unit/Topic rows here
            # using new_course.id
            
            success_count += 1
            
        db.commit()
        print(f"\n[+] Successfully ingested {success_count} new courses into the database.")
        print("[*] The AI is now ready to process the new CT1/CT2 historical evidence.")
        
    except Exception as e:
        print(f"\n[-] Database injection failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ingest_data()
