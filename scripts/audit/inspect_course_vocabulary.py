"""
Inspect authentic unmapped questions for SPCM, EEE, English, ACCA, OODP, ESPCB.
Print question texts and identify missing vocabulary/phrases for each course.
"""
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.database import SessionLocal
from backend.models.core import Exam, Section, Question, Topic, Course
from backend.services.taxonomy_registry import get_taxonomy_registry
from scripts.audit.unmapped_exam_questions import determine_unmapped_reason


def inspect_course_unmapped(cid: int, limit: int = 15):
    db = SessionLocal()
    reg = get_taxonomy_registry()
    c = db.query(Course).filter(Course.id == cid).first()
    rules = reg.get_topic_rules(cid) if reg.has_course(cid) else []

    exams = db.query(Exam).filter(Exam.course_id == cid).all()
    unmapped = []
    for ex in exams:
        for s in ex.sections:
            for q in s.questions:
                if len(q.topics) == 0:
                    reason = determine_unmapped_reason(q, ex)
                    if "PENDING_CLASSIFICATION" in reason:
                        unmapped.append((ex.id, ex.year, q.id, q.question_number, (q.original_text or "").strip()))

    print("=" * 80)
    print(f"Course {cid} ({c.name}): {len(unmapped)} authentic unmapped questions")
    print("=" * 80)
    for eid, yr, qid, qnum, txt in unmapped[:limit]:
        snip = txt[:120].replace("\n", " ")
        print(f"  Exam {eid} ({yr}) Q#{qnum} (ID {qid}): {snip!r}")

    db.close()


if __name__ == "__main__":
    for cid in [13, 14, 15, 16, 17, 18]:
        inspect_course_unmapped(cid, limit=12)
