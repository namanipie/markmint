"""
Generic data-driven deterministic taxonomy classifier.
Enforces conservative, auditable question-to-topic mapping rules.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re
import unicodedata


@dataclass
class TaxonomyTopicRule:
    """Structured configuration for a syllabus topic."""
    topic_id: int
    topic_name: str
    unit_id: int
    unit_name: str
    strong_phrases: List[str] = field(default_factory=list)
    specific_keywords: List[str] = field(default_factory=list)
    negative_guards: List[str] = field(default_factory=list)
    context_hints: List[str] = field(default_factory=list)


@dataclass
class ClassificationProposal:
    """Result of classifying a single question."""
    question_id: int
    topic_id: Optional[int]
    topic_name: Optional[str]
    unit_id: Optional[int]
    unit_name: Optional[str]
    confidence: str  # "HIGH", "MEDIUM", "AMBIGUOUS", "UNMAPPED"
    method: str      # "CANONICAL_PHRASE", "SPECIFIC_KEYWORD", "GUARDRAIL_REJECTED", "NO_MATCH"
    evidence: List[str] = field(default_factory=list)
    candidate_topics: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "unit_id": self.unit_id,
            "unit_name": self.unit_name,
            "confidence": self.confidence,
            "method": self.method,
            "evidence": self.evidence,
            "candidate_topics": self.candidate_topics,
        }


class TaxonomyClassifierService:
    """Generic deterministic taxonomy classifier consuming structured topic rules."""

    def __init__(self, rules: List[TaxonomyTopicRule]):
        self.rules = rules
        self._rule_map = {r.topic_id: r for r in rules}

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize question text while preserving alphanumeric and core math tokens."""
        if not text:
            return ""
        # Unicode decomposition to strip accents while preserving non-Latin scripts (CJK, Hangul, Kana)
        decomposed = unicodedata.normalize("NFKD", text)
        ascii_text = "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()
        # Normalize mathematical LaTeX operators before stripping symbols
        ascii_text = re.sub(r'\\iiint\b', ' triple integral ', ascii_text)
        ascii_text = re.sub(r'\\iint\b', ' double integral ', ascii_text)
        ascii_text = re.sub(r'\\nabla\s*\\cdot|\\nabla\s*\.', ' divergence ', ascii_text)
        ascii_text = re.sub(r'\\nabla\s*\\times|\\nabla\s*x\b', ' curl ', ascii_text)
        ascii_text = re.sub(r'\\nabla\^2', ' laplacian ', ascii_text)
        ascii_text = re.sub(r'\\nabla\b', ' gradient ', ascii_text)
        ascii_text = re.sub(r'\\frac\{\\partial|\\partial\b', ' partial derivative ', ascii_text)
        ascii_text = re.sub(r'\\oint\b', ' contour integral ', ascii_text)
        ascii_text = re.sub(r'\\sum\b', ' summation series ', ascii_text)
        # Clean latex and math symbols into spaced tokens
        cleaned = re.sub(r'[\$\\_{}\[\]\(\)]', ' ', ascii_text)
        # Normalize hyphens surrounded by whitespace (e.g. 'uv- vis' -> 'uv-vis', 'pilling - bedworth' -> 'pilling-bedworth')
        cleaned = re.sub(r'\s*-\s*', '-', cleaned)
        # Normalize whitespace and non-alphanumerics (preserve unicode word characters like CJK/Hangul)
        cleaned = re.sub(r'[^\w+*-]+', ' ', cleaned, flags=re.UNICODE)
        return " ".join(cleaned.split())

    def classify(self, question_id: int, original_text: str) -> ClassificationProposal:
        """
        Classify a single question against registered topic rules.
        Enforces conservative matching:
        - Rejects candidate if negative guard matches.
        - High confidence for unique strong phrase matches.
        - Medium confidence for unique specific keyword matches.
        - Marks as AMBIGUOUS if multiple distinct topics are plausible candidates.
        - Marks as UNMAPPED if no strong/specific evidence found.
        """
        norm_text = self.normalize_text(original_text)
        padded_norm = f" {norm_text} "

        if not norm_text or len(norm_text.strip()) < 3:
            return ClassificationProposal(
                question_id=question_id,
                topic_id=None,
                topic_name=None,
                unit_id=None,
                unit_name=None,
                confidence="UNMAPPED",
                method="NO_MATCH",
                evidence=["Empty or truncated question text"],
            )

        candidates: List[Dict[str, Any]] = []
        guardrail_rejections: List[str] = []

        for rule in self.rules:
            # 1. Check negative guards
            guard_matched = False
            for neg in rule.negative_guards:
                neg_norm = self.normalize_text(neg)
                if neg_norm and f" {neg_norm} " in padded_norm:
                    guardrail_rejections.append(f"Topic '{rule.topic_name}' rejected by guardrail: '{neg}'")
                    guard_matched = True
                    break

            if guard_matched:
                continue

            # 2. Check strong phrases (multi-word high-specificity canonical phrases)
            matched_strong = []
            for phrase in rule.strong_phrases:
                p_norm = self.normalize_text(phrase)
                if p_norm and f" {p_norm} " in padded_norm:
                    matched_strong.append(phrase)

            # 3. Check specific keywords (distinctive single or double tokens with word boundaries)
            matched_keywords = []
            for kw in rule.specific_keywords:
                kw_norm = self.normalize_text(kw)
                if kw_norm and f" {kw_norm} " in padded_norm:
                    matched_keywords.append(kw)

            if matched_strong:
                candidates.append({
                    "rule": rule,
                    "level": "HIGH",
                    "method": "CANONICAL_PHRASE",
                    "evidence": matched_strong,
                })
            elif matched_keywords:
                candidates.append({
                    "rule": rule,
                    "level": "MEDIUM",
                    "method": "SPECIFIC_KEYWORD",
                    "evidence": matched_keywords,
                })

        # Evaluate candidate findings
        if not candidates:
            if guardrail_rejections:
                return ClassificationProposal(
                    question_id=question_id,
                    topic_id=None,
                    topic_name=None,
                    unit_id=None,
                    unit_name=None,
                    confidence="UNMAPPED",
                    method="GUARDRAIL_REJECTED",
                    evidence=guardrail_rejections,
                )
            return ClassificationProposal(
                question_id=question_id,
                topic_id=None,
                topic_name=None,
                unit_id=None,
                unit_name=None,
                confidence="UNMAPPED",
                method="NO_MATCH",
                evidence=["No matching syllabus keywords or phrases"],
            )

        # Distinct topic candidates
        distinct_topic_candidates = {}
        for c in candidates:
            t_id = c["rule"].topic_id
            if t_id not in distinct_topic_candidates:
                distinct_topic_candidates[t_id] = c

        if len(distinct_topic_candidates) == 1:
            chosen = list(distinct_topic_candidates.values())[0]
            rule = chosen["rule"]
            return ClassificationProposal(
                question_id=question_id,
                topic_id=rule.topic_id,
                topic_name=rule.topic_name,
                unit_id=rule.unit_id,
                unit_name=rule.unit_name,
                confidence=chosen["level"],
                method=chosen["method"],
                evidence=chosen["evidence"],
            )

        # Multiple distinct topics matched -> strictly conservative policy: mark as AMBIGUOUS.
        # Questions with concepts across multiple syllabus topics are left unmapped rather than arbitrarily forced.
        cand_summaries = [
            {
                "topic_id": c["rule"].topic_id,
                "topic_name": c["rule"].topic_name,
                "evidence": c["evidence"],
                "level": c["level"],
            }
            for c in distinct_topic_candidates.values()
        ]
        return ClassificationProposal(
            question_id=question_id,
            topic_id=None,
            topic_name=None,
            unit_id=None,
            unit_name=None,
            confidence="AMBIGUOUS",
            method="GUARDRAIL_REJECTED" if guardrail_rejections else "NO_MATCH",
            evidence=[
                f"Conflicting candidates: {', '.join([c['topic_name'] for c in cand_summaries])}"
            ] + guardrail_rejections,
            candidate_topics=cand_summaries,
        )

    def classify_batch(self, questions: List[Dict[str, Any]]) -> List[ClassificationProposal]:
        """Classify a list of questions (each dict having 'id' and 'original_text')."""
        return [self.classify(q["id"], q.get("original_text") or "") for q in questions]
