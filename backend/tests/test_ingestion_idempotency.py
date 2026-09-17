from backend.models.core import Course, Document, DocumentProvenance, Exam, Section, Question
from backend.services.document import DocumentService

def test_ingest_same_document_twice(db_session):
    svc = DocumentService(db_session)
    course = db_session.query(Course).first()
    
    doc = svc.get_or_create_document(document_hash="hash123")
    extraction = {
        "sections": [
            {"name": "A", "questions": [{"marks": 5}]}
        ]
    }
    
    # First ingest
    svc.import_exam_extraction(doc.id, course.id, 2023, "Fall", extraction)
    assert db_session.query(Exam).count() == 1
    assert db_session.query(Section).count() == 1
    assert db_session.query(Question).count() == 1

    # Second ingest (simulate rerunning feeder script)
    svc.import_exam_extraction(doc.id, course.id, 2023, "Fall", extraction)

    # Verify exactly one exam and no duplicate questions
    assert db_session.query(Exam).count() == 1
    assert db_session.query(Section).count() == 1
    assert db_session.query(Question).count() == 1


def test_same_hash_different_source_adds_provenance(db_session):
    svc = DocumentService(db_session)
    first = svc.get_or_create_document(
        document_hash="shared_hash", source="Studique", original_url="https://studique.test/paper"
    )
    second = svc.get_or_create_document(
        document_hash="shared_hash", source="TheHelpers", original_url="https://helpers.test/paper"
    )

    assert first.id == second.id
    assert db_session.query(Document).count() == 1
    assert db_session.query(DocumentProvenance).count() == 2

def test_ingest_duplicate_url(db_session):
    svc = DocumentService(db_session)
    course = db_session.query(Course).first()

    # First doc with hash_a and url
    doc1 = svc.get_or_create_document(document_hash="hash_a", original_url="http://test.com/exam.pdf")
    svc.import_exam_extraction(doc1.id, course.id, 2023, "Fall", {})

    # Second doc with different hash but same url
    doc2 = svc.get_or_create_document(document_hash="hash_b", original_url="http://test.com/exam.pdf")
    svc.import_exam_extraction(doc2.id, course.id, 2023, "Fall", {})

    # Different SHA256 => different documents
    assert doc1.id != doc2.id
    assert db_session.query(Document).count() == 2
    assert db_session.query(Exam).count() == 2

    # Provenance: each document should have one provenance with the source_url
    provs = db_session.query(DocumentProvenance).all()
    assert len(provs) == 2
    assert {p.document_id for p in provs} == {doc1.id, doc2.id}
    assert all(p.source_url == "http://test.com/exam.pdf" for p in provs)

    # Re-ingest the second doc (should be a no-op)
    svc.import_exam_extraction(doc2.id, course.id, 2023, "Fall", {})
    assert db_session.query(Document).count() == 2
    assert db_session.query(Exam).count() == 2
    assert db_session.query(DocumentProvenance).count() == 2

def test_simulate_partial_failure_and_rerun(db_session):
    svc = DocumentService(db_session)
    course = db_session.query(Course).first()
    
    doc = svc.get_or_create_document(document_hash="hash_fail")
    
    # Simulate a partial failure (e.g., crashed during section insertion)
    partial_exam = Exam(course_id=course.id, document_id=doc.id, year=2023, term="Fall")
    db_session.add(partial_exam)
    db_session.commit()
    
    assert db_session.query(Exam).count() == 1
    assert db_session.query(Section).count() == 0
    
    # Rerun ingestion properly
    extraction = {
        "sections": [
            {"name": "A", "questions": [{"marks": 10}]}
        ]
    }
    svc.import_exam_extraction(doc.id, course.id, 2023, "Fall", extraction)
    
    # Should clean up the partial exam and insert fully
    assert db_session.query(Exam).count() == 1
    assert db_session.query(Section).count() == 1
    assert db_session.query(Question).count() == 1
