import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.core.database import engine
from sqlalchemy import text

print("==================================================================")
print("     RAW, UNFILTERED EXAMINATION TYPES PRESENT IN THE DATABASE     ")
print("==================================================================")

with engine.connect() as conn:
    print("\n--- 1. TABLE: exams -> COLUMN: assessment_type ---")
    exams_types = conn.execute(text("""
        SELECT 
            assessment_type, 
            COUNT(*) as exam_count
        FROM exams
        GROUP BY assessment_type
        ORDER BY exam_count DESC
    """)).fetchall()
    
    total_exams = sum(r[1] for r in exams_types)
    print(f"Total Exam Rows in 'exams' table: {total_exams}")
    for val, count in exams_types:
        val_repr = repr(val) if val is not None else "NULL / None"
        print(f"  {val_repr:35s} : {count:4d} exams")

    print("\n--- 2. TABLE: documents -> COLUMN: exam_type ---")
    doc_exam_types = conn.execute(text("""
        SELECT 
            exam_type, 
            COUNT(*) as doc_count
        FROM documents
        GROUP BY exam_type
        ORDER BY doc_count DESC
    """)).fetchall()
    
    total_docs = sum(r[1] for r in doc_exam_types)
    print(f"Total Document Rows in 'documents' table: {total_docs}")
    for val, count in doc_exam_types:
        val_repr = repr(val) if val is not None else "NULL / None"
        print(f"  {val_repr:35s} : {count:4d} documents")

    print("\n--- 3. TABLE: documents -> COLUMN: resource_type ---")
    doc_resource_types = conn.execute(text("""
        SELECT 
            resource_type, 
            COUNT(*) as doc_count
        FROM documents
        GROUP BY resource_type
        ORDER BY doc_count DESC
    """)).fetchall()
    for val, count in doc_resource_types:
        val_repr = repr(val) if val is not None else "NULL / None"
        print(f"  {val_repr:35s} : {count:4d} documents")

    print("\n--- 4. TABLE: assessment_components -> COLUMNS: code, role, canonical_label ---")
    components = conn.execute(text("""
        SELECT 
            code, 
            role, 
            canonical_label, 
            COUNT(*) as comp_count
        FROM assessment_components
        GROUP BY code, role, canonical_label
        ORDER BY code, comp_count DESC
    """)).fetchall()
    print(f"Total Assessment Components: {len(components)} distinct definitions")
    for code, role, label, count in components:
        print(f"  Code: {code:10s} | Role: {role:20s} | Label: {label:40s} | Count: {count}")

    print("\n--- 5. SAMPLE DOCUMENTS AND EXAMS FOR EVERY DISTINCT assessment_type ---")
    distinct_types = [r[0] for r in exams_types]
    for dtype in distinct_types:
        if dtype is None:
            sample = conn.execute(text("""
                SELECT e.id, c.code, d.title 
                FROM exams e 
                JOIN courses c ON e.course_id = c.id 
                LEFT JOIN documents d ON e.document_id = d.id 
                WHERE e.assessment_type IS NULL 
                LIMIT 2
            """)).fetchall()
        else:
            sample = conn.execute(text("""
                SELECT e.id, c.code, d.title 
                FROM exams e 
                JOIN courses c ON e.course_id = c.id 
                LEFT JOIN documents d ON e.document_id = d.id 
                WHERE e.assessment_type = :atype 
                LIMIT 2
            """), {"atype": dtype}).fetchall()
        
        dtype_str = repr(dtype) if dtype is not None else "NULL / None"
        print(f"\nType: {dtype_str}")
        for s in sample:
            print(f"   Exam ID {s[0]} | Course: {s[1]} | Title: {s[2]}")
