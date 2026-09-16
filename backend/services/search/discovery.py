import re
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

from backend.models.core import (
    Question, Concept, StudyEvidence, Document, Exam, Section,
    Course, Topic, QuestionFamily, Unit
)
from backend.schemas import (
    SearchQuery, SearchResult, SearchResultType, ParsedIntent, SearchFilters
)

class DiscoverySearchEngine:
    def __init__(self, db: Session):
        self.db = db

    def _parse_intent(self, raw_query: str) -> ParsedIntent:
        """
        Parses natural language to extract implicit filters (e.g. '5 mark questions').
        """
        q = raw_query.lower()
        intent = ParsedIntent(clean_search_term=raw_query)
        
        # 1. Target Type
        if "course" in q or "subject" in q:
            intent.target_type = SearchResultType.COURSE
        elif "trend" in q or "increasing" in q or "decreasing" in q:
            intent.target_type = SearchResultType.ANALYSIS_FINDING
        elif "family" in q or "repeat" in q or "coming" in q:
            intent.target_type = SearchResultType.QUESTION_FAMILY
        elif "question" in q:
            intent.target_type = SearchResultType.EXAM_QUESTION
        elif "topic" in q:
            intent.target_type = SearchResultType.TOPIC
        elif "concept" in q:
            intent.target_type = SearchResultType.CONCEPT
        elif "exam" in q or "paper" in q:
            intent.target_type = SearchResultType.EXAM

        # 2. Extract Marks
        marks_match = re.search(r'(\d+)\s*mark', q)
        if marks_match:
            intent.extracted_marks = float(marks_match.group(1))
            
        # 3. Clean search term (remove boilerplate words)
        stopwords = {
            "about", "what", "keeps", "coming", "in", "on", "that", "repeat", "repeats", "recently",
            "mark", "marks", "question", "questions", "topic", "topics", "concept", "concepts",
            "course", "courses", "subject", "subjects", "exam", "exams", "paper", "papers",
            "family", "families", "give", "me", "show", "find", "all"
        }
        words = q.split()
        clean_words = [w for w in words if w not in stopwords and not w.isdigit()]
        intent.clean_search_term = " ".join(clean_words).strip() or raw_query.strip()
        
        return intent

    def _hybrid_search_courses(self, intent: ParsedIntent, filters: SearchFilters, limit: int) -> list[SearchResult]:
        if not self.db:
            return []
        term = f"%{intent.clean_search_term}%"
        query = self.db.query(Course).filter(
            or_(
                Course.name.ilike(term),
                Course.code.ilike(term),
                Course.canonical_code.ilike(term),
                Course.department.ilike(term)
            )
        )
        results = query.limit(limit).all()
        return [
            SearchResult(
                id=c.id,
                result_type=SearchResultType.COURSE,
                title=c.name,
                text_snippet=f"Code: {c.canonical_code or c.code} | Dept: {c.department or 'N/A'}",
                subject=c.name,
                relevance_score=0.98,
                metadata={"course_id": c.id, "canonical_code": c.canonical_code, "department": c.department}
            )
            for c in results
        ]

    def _hybrid_search_topics(self, intent: ParsedIntent, filters: SearchFilters, limit: int) -> list[SearchResult]:
        if not self.db:
            return []
        term = f"%{intent.clean_search_term}%"
        query = self.db.query(Topic).join(Unit, Topic.unit_id == Unit.id).filter(
            Topic.name.ilike(term)
        )
        results = query.limit(limit).all()
        return [
            SearchResult(
                id=t.id,
                result_type=SearchResultType.TOPIC,
                title=t.name,
                text_snippet=f"Academic Topic under {t.unit.name if t.unit else 'Unit'}",
                unit=t.unit.name if t.unit else None,
                topic=t.name,
                relevance_score=0.92,
                metadata={"topic_id": t.id, "unit_id": t.unit_id}
            )
            for t in results
        ]

    def _hybrid_search_families(self, intent: ParsedIntent, filters: SearchFilters, limit: int) -> list[SearchResult]:
        if not self.db:
            return []
        term = f"%{intent.clean_search_term}%"
        query = self.db.query(QuestionFamily).filter(
            or_(
                QuestionFamily.canonical_name.ilike(term),
                QuestionFamily.description.ilike(term)
            )
        )
        results = query.limit(limit).all()
        return [
            SearchResult(
                id=f.id,
                result_type=SearchResultType.QUESTION_FAMILY,
                title=f.canonical_name,
                text_snippet=f.description or f"Recurring question family in {f.subject}",
                subject=f.subject,
                relevance_score=0.90,
                metadata={"family_id": f.id, "repetition_type": f.repetition_type}
            )
            for f in results
        ]

    def _hybrid_search_questions(self, intent: ParsedIntent, filters: SearchFilters, limit: int) -> list[SearchResult]:
        if not self.db:
            return []
        query = self.db.query(Question).join(Question.section).join(Section.exam).outerjoin(Exam.document)
        
        # Exact/Metadata filters
        if intent.extracted_marks:
            query = query.filter(Question.marks == intent.extracted_marks)
        if filters.marks:
            query = query.filter(Question.marks == filters.marks)
        if filters.year:
            query = query.filter(Exam.year == filters.year)
            
        if intent.clean_search_term:
            term = f"%{intent.clean_search_term}%"
            query = query.filter(
                or_(
                    Question.original_text.ilike(term),
                    Question.normalized_text.ilike(term)
                )
            )
            
        results = query.limit(limit).all()
        
        out = []
        for q in results:
            doc_url = q.section.exam.document.original_url if (q.section and q.section.exam and q.section.exam.document) else None
            top_name = q.topics[0].name if q.topics else "General"
            out.append(SearchResult(
                id=q.id,
                result_type=SearchResultType.EXAM_QUESTION,
                title=f"Exam Question: {top_name} ({q.marks or 0:.0f} marks)",
                text_snippet=q.original_text[:200] if q.original_text else "",
                year=q.section.exam.year if q.section and q.section.exam else None,
                exam_type=q.section.exam.assessment_type if q.section and q.section.exam else None,
                topic=top_name,
                relevance_score=0.88,
                provenance_url=doc_url,
                metadata={"question_id": q.id, "marks": q.marks, "is_alternative": q.is_alternative}
            ))
        return out

    def _hybrid_search_concepts(self, intent: ParsedIntent, filters: SearchFilters, limit: int) -> list[SearchResult]:
        if not self.db:
            return []
        query = self.db.query(Concept)
        
        if filters.subject:
            query = query.filter(Concept.subject == filters.subject)
            
        if intent.clean_search_term:
            term = f"%{intent.clean_search_term}%"
            query = query.filter(
                or_(
                    Concept.canonical_name.ilike(term),
                    Concept.description.ilike(term)
                )
            )
            
        results = query.limit(limit).all()
        
        return [SearchResult(
            id=c.id,
            result_type=SearchResultType.CONCEPT,
            title=c.canonical_name,
            text_snippet=c.description or "Academic concept in syllabus graph",
            subject=c.subject,
            relevance_score=0.85,
            metadata={"concept_id": c.id}
        ) for c in results]
        
    def _hybrid_search_study_material(self, intent: ParsedIntent, filters: SearchFilters, limit: int) -> list[SearchResult]:
        if not self.db:
            return []
        query = self.db.query(StudyEvidence).join(StudyEvidence.document)
        
        if intent.clean_search_term:
            term = f"%{intent.clean_search_term}%"
            query = query.filter(StudyEvidence.content.ilike(term))
            
        results = query.limit(limit).all()
        
        return [SearchResult(
            id=s.id,
            result_type=SearchResultType.STUDY_MATERIAL,
            title=f"Study Extract: {s.document.title if s.document else 'Untitled'}",
            text_snippet=s.content[:200] if s.content else "",
            subject=s.document.subject if s.document else None,
            relevance_score=0.82,
            provenance_url=s.document.original_url if s.document else None,
            attribution=s.document.source if s.document else "Local Resource",
            metadata={"document_id": s.document_id, "page_number": s.page_number}
        ) for s in results]

    def search(self, query: SearchQuery) -> list[SearchResult]:
        intent = self._parse_intent(query.raw_query)
        filters = query.filters or SearchFilters()
        
        # Route to specific handler if intent target is explicit
        if intent.target_type == SearchResultType.COURSE:
            return self._hybrid_search_courses(intent, filters, query.limit)
        elif intent.target_type == SearchResultType.TOPIC:
            return self._hybrid_search_topics(intent, filters, query.limit)
        elif intent.target_type == SearchResultType.QUESTION_FAMILY:
            return self._hybrid_search_families(intent, filters, query.limit)
        elif intent.target_type == SearchResultType.EXAM_QUESTION:
            return self._hybrid_search_questions(intent, filters, query.limit)
        elif intent.target_type == SearchResultType.CONCEPT:
            return self._hybrid_search_concepts(intent, filters, query.limit)
        elif intent.target_type == SearchResultType.STUDY_MATERIAL:
            return self._hybrid_search_study_material(intent, filters, query.limit)
        else:
            # Broad scatter-gather across all entities
            per_type = max(2, query.limit // 4)
            courses = self._hybrid_search_courses(intent, filters, limit=per_type)
            topics = self._hybrid_search_topics(intent, filters, limit=per_type)
            families = self._hybrid_search_families(intent, filters, limit=per_type)
            questions = self._hybrid_search_questions(intent, filters, limit=per_type)
            concepts = self._hybrid_search_concepts(intent, filters, limit=per_type)
            materials = self._hybrid_search_study_material(intent, filters, limit=per_type)
            
            combined = courses + topics + families + questions + concepts + materials
            combined.sort(key=lambda x: x.relevance_score, reverse=True)
            return combined[:query.limit]
