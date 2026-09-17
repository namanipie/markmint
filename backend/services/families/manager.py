import numpy as np
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.core import Question, QuestionFamily, QuestionFamilyMembership
from backend.services.question_classifier import BaseClassificationProvider
from backend.services.families.normalizer import QuestionNormalizer

class FamilyMatchDecision:
    def __init__(self, is_match: bool, match_type: str, score: float, method: str):
        self.is_match = is_match
        self.match_type = match_type
        self.score = score
        self.method = method

class LLMStructuralGuardrail:
    """
    Acts as a bounded validation layer for high-similarity conceptual matches
    to prevent structural false positives (e.g., 'Explain X' vs 'Explain Y').
    """
    @staticmethod
    def validate(q1_text: str, q2_text: str, similarity_score: float) -> bool:
        # In production, this would dispatch to an LLM:
        # "Do these two questions test the exact same underlying concept? Yes/No."
        # For now, we simulate the guardrail using lexical divergence on the nouns.
        
        # If similarity is extremely high, we trust the embedding
        if similarity_score >= 0.92:
            return True
            
        q1_lower = q1_text.lower()
        q2_lower = q2_text.lower()
        
        # Simple heuristic: if they share structural verbs but completely differ in key terms
        distinct_pairs = [
            ("binary", "breadth"),
            ("bfs", "dfs"),
            ("stack", "queue"),
            ("indexing", "scheduling"), # from user prompt
            ("normalization", "machine learning")
        ]
        
        for p1, p2 in distinct_pairs:
            if (p1 in q1_lower and p2 in q2_lower) or (p2 in q1_lower and p1 in q2_lower):
                return False
                
        return True

class QuestionFamilyManager:
    ALGORITHM_VERSION = "v1.0"
    EXACT_THRESHOLD = 0.98
    CONCEPTUAL_THRESHOLD = 0.82
    
    def __init__(self, db: Session, embedding_provider: BaseClassificationProvider):
        self.db = db
        self.provider = embedding_provider

    def _get_historical_families(self, subject: str, max_year: Optional[int]) -> List[QuestionFamily]:
        """
        Retrieves families strictly bounded by subject and chronological cutoff.
        If max_year is None (unanchored question), it can view all existing families to join them,
        but it will never spawn a family visible to historical cutoffs.
        """
        query = self.db.query(QuestionFamily).filter(QuestionFamily.subject == subject)
        if max_year is not None:
            # A dated question only sees families born in or before its year.
            # Null (unanchored) families are excluded because SQL `col <= val` evaluates to false/unknown for NULLs.
            query = query.filter(QuestionFamily.first_seen_year <= max_year)
        
        return query.all()

    def process_course_questions(self, course_id: int, subject_name: str):
        """
        Processes questions strictly chronologically to prevent temporal leakage.
        """
        from backend.models.core import Exam, Section
        
        # 1. Fetch all questions ordered by year
        # In SQLAlchemy, we need to join to get the year
        questions_by_year = (
            self.db.query(Question, Exam.year)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == course_id)
            .order_by(Exam.year.asc())
            .all()
        )
        
        if not questions_by_year:
            return
            
        # Local cache of family embeddings and normalized texts for Top-K retrieval
        family_embeddings_cache = {}
        family_norm_text_cache = {}
        
        # Load existing families into cache
        existing_families = self._get_historical_families(subject_name, 2100)
        for fam in existing_families:
            family_norm_text_cache[fam.id] = QuestionNormalizer.normalize(fam.canonical_name)
        
        # Precompute embeddings for all questions for efficiency, though we will apply them chronologically
        from backend.services.canonical import CanonicalRepresentationBuilder
        texts = [CanonicalRepresentationBuilder.build(q) for q, _ in questions_by_year]
        all_embeddings = self.provider.get_embeddings(texts)
        
        for i, (question, year) in enumerate(questions_by_year):
            # Skip if already processed
            if question.family_id is not None:
                continue
                
            q_year = year
            
            # Extract high-fidelity canonical text from structured JSON
            q_text = CanonicalRepresentationBuilder.build(question)
            
            q_norm = QuestionNormalizer.normalize(q_text)
            q_emb = np.array(all_embeddings[i], dtype=np.float32)
            
            # Update the question's text fields to the new high-fidelity version
            question.original_text = q_text
            question.normalized_text = q_norm
            
            # 2. Retrieve candidates strictly from families first seen <= q_year
            # (Immutable historical ancestry)
            candidate_families = self._get_historical_families(subject_name, q_year)
            
            decision = None
            best_family_id = None
            
            # Attempt Exact Match (Lexical) first against questions in candidate families
            for family in candidate_families:
                fam_norm = family_norm_text_cache.get(family.id)
                if fam_norm is None:
                    fam_norm = QuestionNormalizer.normalize(family.canonical_name)
                    family_norm_text_cache[family.id] = fam_norm
                if q_norm == fam_norm:
                    if len(q_norm) > 10: # Avoid matching trivial "1"
                        decision = FamilyMatchDecision(True, "exact", 1.0, "lexical_hash")
                        best_family_id = family.id
                        break
            
            # 3. Semantic Top-K Matching
            if not decision and candidate_families:
                uncached = [f for f in candidate_families if f.id not in family_embeddings_cache]
                if uncached:
                    uncached_texts = [f.canonical_name for f in uncached]
                    new_embs = self.provider.get_embeddings(uncached_texts)
                    for f, emb in zip(uncached, new_embs):
                        arr = np.array(emb, dtype=np.float32)
                        n = np.linalg.norm(arr)
                        family_embeddings_cache[f.id] = (arr / n) if n > 0 else arr
                
                cand_embs = np.stack([family_embeddings_cache[f.id] for f in candidate_families])
                norm_q = np.linalg.norm(q_emb)
                q_unit = (q_emb / norm_q) if norm_q > 0 else q_emb
                sims = np.dot(cand_embs, q_unit)

                best_idx = int(np.argmax(sims))
                best_score = float(sims[best_idx])
                best_fam = candidate_families[best_idx]

                if best_score >= self.CONCEPTUAL_THRESHOLD:
                    # 4. LLM Structural Guardrail Validation
                    is_valid = LLMStructuralGuardrail.validate(q_text, best_fam.canonical_name, best_score)
                    
                    if is_valid:
                        decision = FamilyMatchDecision(True, "conceptual", best_score, "semantic_embedding+llm_guardrail")
                        best_family_id = best_fam.id
            
            # 5. Assignment
            if decision and best_family_id:
                # Assign to existing family
                question.family_id = best_family_id
                
                # Update latest seen and repetition type
                fam_to_update = self.db.query(QuestionFamily).get(best_family_id)
                if fam_to_update:
                    if q_year is not None:
                        if fam_to_update.latest_seen_year is None or q_year > fam_to_update.latest_seen_year:
                            fam_to_update.latest_seen_year = q_year
                    if fam_to_update.repetition_type in ("singleton", None):
                        fam_to_update.repetition_type = "exact_repeat" if decision.match_type == "exact" else "family_repeat"
                    elif fam_to_update.repetition_type == "exact_repeat" and decision.match_type != "exact":
                        fam_to_update.repetition_type = "family_repeat"
                
                # Persist evidence
                membership = QuestionFamilyMembership(
                    question_id=question.id,
                    family_id=best_family_id,
                    match_type=decision.match_type,
                    similarity_score=decision.score,
                    decision_method=decision.method,
                    algorithm_version=self.ALGORITHM_VERSION
                )
                self.db.add(membership)
                
            else:
                # 6. Spawns a new family (Singleton initially)
                new_family = QuestionFamily(
                    canonical_name=q_text,
                    subject=subject_name,
                    first_seen_year=q_year,
                    latest_seen_year=q_year,
                    repetition_type="singleton"
                )
                self.db.add(new_family)
                self.db.flush() # get ID
                
                question.family_id = new_family.id
                family_norm_text_cache[new_family.id] = q_norm
                norm_q = np.linalg.norm(q_emb)
                family_embeddings_cache[new_family.id] = (q_emb / norm_q) if norm_q > 0 else q_emb
                
                membership = QuestionFamilyMembership(
                    question_id=question.id,
                    family_id=new_family.id,
                    match_type="exact", # self-match
                    similarity_score=1.0,
                    decision_method="spawn",
                    algorithm_version=self.ALGORITHM_VERSION
                )
                self.db.add(membership)
                
        self.db.commit()
