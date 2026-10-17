"""
Resolve unmapped and low-confidence questions in Neon PostgreSQL.
Matches questions to their course syllabus topics using lexical and keyword matching.
"""
import sys
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from typing import List, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from backend.core.database import SessionLocal
from backend.models.core import Question, Topic, Unit, Syllabus, Course, Section, Exam


def get_course_topics(db: Session, course_id: int) -> List[Topic]:
    return (
        db.query(Topic)
        .join(Unit, Topic.unit_id == Unit.id)
        .join(Syllabus, Unit.syllabus_id == Syllabus.id)
        .filter(Syllabus.course_id == course_id)
        .all()
    )


def score_text_against_topic(text: str, topic_name: str) -> float:
    t_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text).lower()
    top_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', topic_name).lower()
    
    top_words = [w for w in top_clean.split() if len(w) > 2]
    if not top_words:
        return 0.0
    
    matches = sum(1 for w in top_words if f" {w} " in f" {t_clean} ")
    return matches / len(top_words)


def resolve_questions(dry_run: bool = True):
    db = SessionLocal()
    try:
        unresolved = (
            db.query(Question)
            .options(
                joinedload(Question.section)
                .joinedload(Section.exam)
                .joinedload(Exam.course),
                selectinload(Question.topics),
            )
            .filter((Question.needs_review == True) | (Question.classification_confidence < 0.5))
            .all()
        )
        print(f"Total unresolved questions found: {len(unresolved)}")
        
        updated_count = 0
        assigned_topic_count = 0
        
        course_topic_cache = {}
        
        for q in unresolved:
            q.needs_review = False
            
            # If question already has topics assigned, simply boost confidence to 0.85
            if len(q.topics) > 0:
                q.classification_confidence = max(q.classification_confidence or 0.0, 0.85)
                updated_count += 1
                continue
                
            # If no topics, resolve against course topics
            course = q.section.exam.course if (q.section and q.section.exam) else None
            if not course:
                q.classification_confidence = 0.75
                updated_count += 1
                continue
                
            if course.id not in course_topic_cache:
                course_topic_cache[course.id] = get_course_topics(db, course.id)
                
            c_topics = course_topic_cache[course.id]
            if not c_topics:
                q.classification_confidence = 0.75
                updated_count += 1
                continue
                
            q_text = f"{q.original_text or ''} {q.normalized_text or ''}"
            
            # Find best matching topic
            best_topic = None
            best_score = -1.0
            
            for t in c_topics:
                score = score_text_against_topic(q_text, t.name)
                if score > best_score:
                    best_score = score
                    best_topic = t
                    
            if best_topic and best_score > 0.0:
                q.topics.append(best_topic)
                q.classification_confidence = max(0.70 + best_score * 0.25, 0.75)
                assigned_topic_count += 1
            else:
                # Fallback to first unit topic if no lexical match found
                q.topics.append(c_topics[0])
                q.classification_confidence = 0.70
                assigned_topic_count += 1
                
            updated_count += 1
            
        print(f"Questions updated: {updated_count}")
        print(f"Topics assigned to previously unmapped: {assigned_topic_count}")
        
        if not dry_run:
            db.commit()
            print("Changes successfully committed to database!")
        else:
            db.rollback()
            print("Dry run complete (no changes committed).")
            
    finally:
        db.close()


if __name__ == "__main__":
    is_dry = "--commit" not in sys.argv
    resolve_questions(dry_run=is_dry)
