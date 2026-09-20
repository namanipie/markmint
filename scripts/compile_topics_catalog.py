"""
Compiles canonical topic catalog from production_corpus.db into src/lib/topics-catalog.json.
Only includes legitimate canonical taxonomy topics with verified historical question evidence (>= 1 question).
Strictly separates foreign language tracks.
"""
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.core.database import SessionLocal
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Exam, Section, Question, QuestionFamily, Document, question_topic
)
from sqlalchemy import func

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = text.lower()
    text = text.replace('ß', 'ss')
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text or 'topic'

COURSE_SLUGS = {
    1: 'calculus-and-linear-algebra',
    2: 'chemistry',
    3: 'philosophy-of-engineering',
    4: 'introduction-to-computational-biology',
    5: 'programming-for-problem-solving',
    6: 'fundamental-of-economics',
    7: 'biomedical-sensors',
    8: 'foreign-languages',
    9: 'cell-biology',
    10: 'microbiology',
    11: 'physical-and-analytical-chemistry',
    12: 'biochemistry',
    13: 'semiconductor-physics-and-computational-methods',
    14: 'electrical-and-electronics-engineering',
    15: 'communicative-english',
    16: 'advanced-calculus-and-complex-analysis',
    17: 'object-oriented-design-and-programming',
    18: 'electronic-system-and-pcb-design',
    19: 'electromagnetic-theory-and-quantum-mechanics',
    20: 'physics-mechanics',
    21: 'engineering-mechanics',
    22: 'probability-and-statistics',
    23: 'building-materials-in-the-built-environment',
    24: 'data-structures-and-algorithms',
    25: 'operating-systems',
    26: 'computer-organization-and-architecture',
    27: 'design-and-analysis-of-algorithms',
    28: 'database-management-systems'
}

def clean_question_snippet(text: str, max_len: int = 180) -> str:
    if not text:
        return ""
    # Remove leading question numbers like "1. ", "Q2: ", "PART B 12. "
    cleaned = re.sub(r'^(?:[Qq]uestion\s*\d+|[Pp]art\s*[A-Da-d]\s*\d*|\d+[\.\)]\s*)', '', text.strip())
    cleaned = re.sub(r'\s+', ' ', cleaned)
    if len(cleaned) > max_len:
        return cleaned[:max_len].rsplit(' ', 1)[0] + '...'
    return cleaned

def compile_topics():
    db = SessionLocal()
    courses = db.query(Course).order_by(Course.id).all()

    topics_catalog = []
    total_canonical_scanned = 0
    total_excluded_no_evidence = 0

    for c in courses:
        course_slug = COURSE_SLUGS.get(c.id, c.code.lower())
        has_tracks = len(c.tracks) > 0

        if has_tracks:
            for t in c.tracks:
                syl = (
                    db.query(Syllabus)
                    .filter(Syllabus.course_id == c.id, Syllabus.track_id == t.id)
                    .order_by(Syllabus.id.desc())
                    .first()
                )
                if not syl:
                    continue

                for u in syl.units:
                    for top in u.topics:
                        total_canonical_scanned += 1

                        # Query questions mapped to this topic strictly isolated to this track
                        q_rows = (
                            db.query(Question, Exam)
                            .join(question_topic, question_topic.c.question_id == Question.id)
                            .join(Section, Question.section_id == Section.id)
                            .join(Exam, Section.exam_id == Exam.id)
                            .filter(question_topic.c.topic_id == top.id, Exam.track_id == t.id)
                            .all()
                        )

                        if not q_rows:
                            total_excluded_no_evidence += 1
                            continue

                        # Extract factual metrics
                        slug = slugify(top.name)
                        papers_map = {}
                        assessments = {"CT1": 0, "CT2": 0, "EndSem": 0, "Internal": 0, "Other": 0}
                        marks_dist = defaultdict(int)
                        fams_map = {}
                        samples = []

                        for q, ex in q_rows:
                            doc = db.query(Document).filter(Document.id == ex.document_id).first() if ex.document_id else None
                            paper_title = doc.title if doc and doc.title else f"SRMIST Exam {ex.id}"
                            paper_year = ex.year or (doc.year if doc else None) or 2023
                            
                            # Normalise assessment type
                            a_type = (ex.assessment_type or (doc.exam_type if doc else None) or "").upper()
                            if "CT1" in a_type or "CYCLE TEST 1" in a_type:
                                clean_atype = "CT1"
                                assessments["CT1"] += 1
                            elif "CT2" in a_type or "CYCLE TEST 2" in a_type:
                                clean_atype = "CT2"
                                assessments["CT2"] += 1
                            elif "END" in a_type or "SEM" in a_type or "UNIVERSITY" in a_type or "FINAL" in a_type:
                                clean_atype = "EndSem"
                                assessments["EndSem"] += 1
                            elif "INTERNAL" in a_type:
                                clean_atype = "Internal"
                                assessments["Internal"] += 1
                            else:
                                clean_atype = "Other"
                                assessments["Other"] += 1

                            papers_map[ex.id] = {
                                "id": ex.id,
                                "title": paper_title,
                                "year": paper_year,
                                "term": ex.term or "Semester",
                                "assessmentType": clean_atype
                            }

                            if q.marks:
                                marks_dist[str(int(q.marks) if q.marks.is_integer() else q.marks)] += 1

                            if q.family_id and q.family:
                                fam_name = clean_question_snippet(q.family.canonical_name, 100)
                                if q.family_id not in fams_map:
                                    fams_map[q.family_id] = {
                                        "id": q.family_id,
                                        "name": fam_name,
                                        "repetitionType": q.family.repetition_type or "standard",
                                        "count": 0
                                    }
                                fams_map[q.family_id]["count"] += 1

                            if len(samples) < 5 and q.original_text:
                                snippet = clean_question_snippet(q.original_text)
                                if snippet and not any(s["text"] == snippet for s in samples):
                                    samples.append({
                                        "id": q.id,
                                        "text": snippet,
                                        "marks": int(q.marks) if q.marks and q.marks.is_integer() else (q.marks or 0),
                                        "year": paper_year,
                                        "assessmentType": clean_atype
                                    })

                        topics_catalog.append({
                            "id": top.id,
                            "slug": slug,
                            "name": top.name,
                            "description": f"Curriculum and historical examination lineage for {top.name} under Unit {u.number} ({u.name}) of {t.track_name} ({t.track_code}) at SRMIST.",
                            "courseId": c.id,
                            "courseSlug": course_slug,
                            "courseName": f"{c.name} - {t.track_name}",
                            "courseCode": c.code,
                            "canonicalCode": t.track_code,
                            "isLanguageTrack": True,
                            "languageKey": t.track_key,
                            "languageName": t.track_name,
                            "trackCode": t.track_code,
                            "unitNumber": u.number,
                            "unitName": u.name,
                            "appearanceCount": len(q_rows),
                            "paperCount": len(papers_map),
                            "papers": list(papers_map.values())[:8],
                            "assessmentAppearances": assessments,
                            "marksDistribution": dict(marks_dist),
                            "questionFamilies": sorted(list(fams_map.values()), key=lambda x: x["count"], reverse=True)[:5],
                            "sampleQuestions": samples,
                            "practiceUrl": f"/mintai?course={c.code}&language={t.track_key}&tab=practice&topic={top.name}",
                            "mintAiUrl": f"/mintai?course={c.code}&language={t.track_key}",
                            "canonicalUrl": f"https://markmint.vercel.app/courses/foreign-languages/{t.track_key}/topics/{slug}"
                        })

        else:
            # Single-track courses
            syl = (
                db.query(Syllabus)
                .filter(Syllabus.course_id == c.id, Syllabus.version == '2021')
                .first()
                or db.query(Syllabus)
                .filter(Syllabus.course_id == c.id)
                .order_by(Syllabus.id.asc())
                .first()
            )
            if not syl:
                continue

            for u in syl.units:
                for top in u.topics:
                    total_canonical_scanned += 1

                    q_rows = (
                        db.query(Question, Exam)
                        .join(question_topic, question_topic.c.question_id == Question.id)
                        .join(Section, Question.section_id == Section.id)
                        .join(Exam, Section.exam_id == Exam.id)
                        .filter(question_topic.c.topic_id == top.id)
                        .all()
                    )

                    if not q_rows:
                        total_excluded_no_evidence += 1
                        continue

                    slug = slugify(top.name)
                    papers_map = {}
                    assessments = {"CT1": 0, "CT2": 0, "EndSem": 0, "Internal": 0, "Other": 0}
                    marks_dist = defaultdict(int)
                    fams_map = {}
                    samples = []

                    for q, ex in q_rows:
                        doc = db.query(Document).filter(Document.id == ex.document_id).first() if ex.document_id else None
                        paper_title = doc.title if doc and doc.title else f"SRMIST Past Exam Paper {ex.id}"
                        paper_year = ex.year or (doc.year if doc else None) or 2023

                        a_type = (ex.assessment_type or (doc.exam_type if doc else None) or "").upper()
                        if "CT1" in a_type or "CYCLE TEST 1" in a_type:
                            clean_atype = "CT1"
                            assessments["CT1"] += 1
                        elif "CT2" in a_type or "CYCLE TEST 2" in a_type:
                            clean_atype = "CT2"
                            assessments["CT2"] += 1
                        elif "END" in a_type or "SEM" in a_type or "UNIVERSITY" in a_type or "FINAL" in a_type:
                            clean_atype = "EndSem"
                            assessments["EndSem"] += 1
                        elif "INTERNAL" in a_type:
                            clean_atype = "Internal"
                            assessments["Internal"] += 1
                        else:
                            clean_atype = "Other"
                            assessments["Other"] += 1

                        papers_map[ex.id] = {
                            "id": ex.id,
                            "title": paper_title,
                            "year": paper_year,
                            "term": ex.term or "Semester",
                            "assessmentType": clean_atype
                        }

                        if q.marks:
                            marks_dist[str(int(q.marks) if q.marks.is_integer() else q.marks)] += 1

                        if q.family_id and q.family:
                            fam_name = clean_question_snippet(q.family.canonical_name, 100)
                            if q.family_id not in fams_map:
                                fams_map[q.family_id] = {
                                    "id": q.family_id,
                                    "name": fam_name,
                                    "repetitionType": q.family.repetition_type or "standard",
                                    "count": 0
                                }
                            fams_map[q.family_id]["count"] += 1

                        if len(samples) < 5 and q.original_text:
                            snippet = clean_question_snippet(q.original_text)
                            if snippet and not any(s["text"] == snippet for s in samples):
                                samples.append({
                                    "id": q.id,
                                    "text": snippet,
                                    "marks": int(q.marks) if q.marks and q.marks.is_integer() else (q.marks or 0),
                                    "year": paper_year,
                                    "assessmentType": clean_atype
                                })

                    topics_catalog.append({
                        "id": top.id,
                        "slug": slug,
                        "name": top.name,
                        "description": f"Curriculum and historical examination lineage for {top.name} under Unit {u.number} ({u.name}) of {c.name} ({c.canonical_code}) at SRMIST.",
                        "courseId": c.id,
                        "courseSlug": course_slug,
                        "courseName": c.name,
                        "courseCode": c.code,
                        "canonicalCode": c.canonical_code,
                        "isLanguageTrack": False,
                        "languageKey": None,
                        "languageName": None,
                        "trackCode": None,
                        "unitNumber": u.number,
                        "unitName": u.name,
                        "appearanceCount": len(q_rows),
                        "paperCount": len(papers_map),
                        "papers": list(papers_map.values())[:8],
                        "assessmentAppearances": assessments,
                        "marksDistribution": dict(marks_dist),
                        "questionFamilies": sorted(list(fams_map.values()), key=lambda x: x["count"], reverse=True)[:5],
                        "sampleQuestions": samples,
                        "practiceUrl": f"/mintai?course={c.code}&tab=practice&topic={top.name}",
                        "mintAiUrl": f"/mintai?course={c.code}",
                        "canonicalUrl": f"https://markmint.vercel.app/courses/{course_slug}/topics/{slug}"
                    })

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "lib", "topics-catalog.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(topics_catalog, f, indent=2, ensure_ascii=False)

    print(f"Total canonical topics scanned: {total_canonical_scanned}")
    print(f"Total valid topics compiled (>= 1 question evidence): {len(topics_catalog)}")
    print(f"Total topics excluded (0 question evidence): {total_excluded_no_evidence}")
    print(f"Compiled to {out_path} ({os.path.getsize(out_path) // 1024} KB).")

if __name__ == "__main__":
    compile_topics()
