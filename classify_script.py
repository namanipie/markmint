"""Run course-scoped classification. Use after taxonomy_insert.py.
Command: .\.venv\Scripts\python.exe classify_script.py"""
import sys
sys.path.insert(0, '.')
from backend.core.database import SessionLocal
from backend.models.core import Course, Question, Topic, Unit, Syllabus
from backend.services.canonical import CanonicalRepresentationBuilder
from backend.services.question_classifier import ClassificationService, LocalTransformerProvider
from sqlalchemy import text

db = SessionLocal()
try:
    provider = LocalTransformerProvider()
    cs = ClassificationService(provider)
    
    # Before mapping count
    mappings_before = db.execute(text("SELECT COUNT(*) FROM question_topic")).fetchone()[0]
    print("BEFORE MAPPINGS:", mappings_before)
    
    # Clear prior mappings for idempotency
    db.execute(text("DELETE FROM question_topic"))
    db.commit()
    
    # Classify by course scope
    calc = db.query(Course).filter(Course.name == "Calculus And Linear Algebra").first()
    chem = db.query(Course).filter(Course.name == "Chemistry").first()
    
    for course in [calc, chem]:
        if not course:
            continue
        topics = db.query(Topic).join(Unit).join(Syllabus).filter(Syllabus.course_id == course.id).all()
        topic_names = [t.name for t in topics]
        if not topic_names:
            print("NO TOPICS for", course.name)
            continue
        
        from backend.models.core import Section, Exam
        questions = db.query(Question).join(Question.section).join(Section.exam).filter(Exam.course_id == course.id).all()
        
        assigned = 0
        unresolved = 0
        for q in questions:
            q_text = CanonicalRepresentationBuilder.build(q)
            result = cs.classify_question(q_text, topic_names, q.marks)
            assigned_name = result.topics[0] if result.topics else None
            score = result.confidence
            q.classification_confidence = score
            q.classification_input = q_text
            q.classification_metadata = {
                "classifier_version": cs.CLASSIFIER_VERSION,
                "provider": provider.__class__.__name__,
                "model": "all-MiniLM-L6-v2",
                "threshold": cs.SIMILARITY_THRESHOLD,
                "selected_topic": assigned_name,
                "resolved": bool(assigned_name),
                "guardrail_reason": result.guardrail_reason,
                "review_status": "AUTO_CLASSIFIED" if assigned_name else "UNRESOLVED",
            }
            if assigned_name:
                topic_obj = next(t for t in topics if t.name == assigned_name)
                q.topics.append(topic_obj)
                assigned += 1
            else:
                unresolved += 1
        db.commit()
        print("COURSE:", course.name, "questions:", len(questions), "assigned:", assigned, "unresolved:", unresolved, "threshold: 0.45")
    
    # After counts
    mappings_after = db.execute(text("SELECT COUNT(*) FROM question_topic")).fetchone()[0]
    print("AFTER MAPPINGS:", mappings_after)
    
except Exception as e:
    db.rollback()
    print("ERROR:", type(e).__name__, str(e)[:200])
finally:
    db.close()
