import os
import sys
import json
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import SessionLocal
from backend.models.core import QuestionFamily, Question, QuestionFamilyMembership, Exam, Document

def run_audit():
    db = SessionLocal()
    
    # 1. Family Distribution
    total_questions = db.query(Question).count()
    families = db.query(QuestionFamily).all()
    total_families = len(families)
    
    family_sizes = defaultdict(int)
    family_members = defaultdict(list)
    
    for f in families:
        count = len(f.questions)
        family_sizes[f.id] = count
        family_members[f.id] = f.questions
        
    counts = list(family_sizes.values())
    
    singletons = sum(1 for c in counts if c == 1)
    size_2 = sum(1 for c in counts if c == 2)
    size_3_5 = sum(1 for c in counts if 3 <= c <= 5)
    size_6_plus = sum(1 for c in counts if c >= 6)
    
    distribution = {
        "total_questions": total_questions,
        "total_families": total_families,
        "singleton_families": singletons,
        "singleton_percentage": (singletons / total_families * 100) if total_families else 0,
        "families_size_2": size_2,
        "families_size_3_5": size_3_5,
        "families_size_6_plus": size_6_plus,
        "largest_family_size": max(counts) if counts else 0,
        "average_family_size": (sum(counts) / len(counts)) if counts else 0,
        "median_family_size": sorted(counts)[len(counts)//2] if counts else 0
    }
    
    os.makedirs('data/reports', exist_ok=True)
    with open('data/reports/family_distribution.json', 'w') as f:
        json.dump(distribution, f, indent=2)

    # 2. Traceability Check
    orphans = 0
    for membership in db.query(QuestionFamilyMembership).all():
        q = membership.question
        if not q or not q.section or not q.section.exam or not q.section.exam.document:
            orphans += 1
    
    print(f"Traceability Check: {orphans} orphaned memberships found.")
    
    # 3. Human Review Sets
    conceptual_memberships = (
        db.query(QuestionFamilyMembership)
        .filter(QuestionFamilyMembership.match_type == 'conceptual')
        .order_by(QuestionFamilyMembership.similarity_score.desc())
        .all()
    )
    
    def build_review_record(m: QuestionFamilyMembership):
        q = m.question
        canonical_q = m.family.canonical_name
        return {
            "family_id": m.family.id,
            "question_a": canonical_q,
            "question_b": q.original_text,
            "match_type": m.match_type,
            "similarity_score": m.similarity_score,
            "decision_method": m.decision_method,
            "subject": m.family.subject,
            "year_a": m.family.first_seen_year,
            "year_b": q.section.exam.year if q.section.exam else None
        }

    highest = [build_review_record(m) for m in conceptual_memberships[:25]]
    lowest = [build_review_record(m) for m in conceptual_memberships[-25:] if m not in conceptual_memberships[:25]]
    
    # largest family pairs
    largest_families = sorted(families, key=lambda f: len(f.questions), reverse=True)[:20]
    largest_pairs = []
    for f in largest_families:
        canonical = f.canonical_name
        for q in f.questions[:2]: # take up to 2 members from each of the largest families
            if q.original_text != canonical:
                m = next((m for m in q.memberships if m.family_id == f.id), None)
                if m:
                    largest_pairs.append(build_review_record(m))
                    if len(largest_pairs) >= 25:
                        break
        if len(largest_pairs) >= 25:
            break

    review_set = {
        "highest_confidence_non_exact": highest,
        "lowest_confidence": lowest,
        "largest_family_member_pairs": largest_pairs
    }
    
    with open('data/reports/family_human_review.json', 'w') as f:
        json.dump(review_set, f, indent=2)

    print("Audit JSONs generated.")

if __name__ == '__main__':
    run_audit()
