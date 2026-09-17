"""
Unit tests for deterministic Chemistry classifier behavior and guardrails.
Verifies conservative matching, ambiguity handling, and normalized representations.
"""
import pytest
from backend.services.taxonomy_classifier import TaxonomyClassifierService, TaxonomyTopicRule
from backend.services.taxonomy_rules.chemistry_rules import CHEMISTRY_TAXONOMY_RULES


@pytest.fixture
def classifier() -> TaxonomyClassifierService:
    return TaxonomyClassifierService(CHEMISTRY_TAXONOMY_RULES)


def test_obvious_topic_match(classifier: TaxonomyClassifierService) -> None:
    """Verifies that an unambiguous canonical prompt maps to the expected topic with HIGH confidence."""
    proposal = classifier.classify(1, "Derive time independent Schrodinger wave equation.")
    assert proposal.confidence == "HIGH"
    assert proposal.method == "CANONICAL_PHRASE"
    assert proposal.topic_id == 45
    assert proposal.topic_name == "Quantum Mechanics and Atomic Structure"
    assert proposal.unit_id == 27
    assert proposal.unit_name == "Quantum and Atomic Structure"
    assert any("schrodinger wave equation" in e for e in proposal.evidence)


def test_medium_keyword_match(classifier: TaxonomyClassifierService) -> None:
    """Verifies that a specific domain keyword produces MEDIUM confidence when unambiguous."""
    proposal = classifier.classify(2, "HASB principle was formulated by Pearson.")
    assert proposal.confidence == "MEDIUM"
    assert proposal.method == "SPECIFIC_KEYWORD"
    assert proposal.topic_id == 62
    assert proposal.topic_name == "Hard and Soft Acids and Bases"
    assert "pearson" in proposal.evidence or "hsab" in proposal.evidence


def test_ambiguous_question_remains_unmapped(classifier: TaxonomyClassifierService) -> None:
    """Verifies that questions matching multiple conflicting topics are flagged AMBIGUOUS with topic_id=None."""
    # Question mentioning both Enantiomers and Diastereomers (conflicts across Stereoisomers vs Optical Activity)
    proposal = classifier.classify(3, "Differentiate between Enantiomers and Diastereomers with examples.")
    assert proposal.confidence == "AMBIGUOUS"
    assert proposal.topic_id is None
    assert proposal.topic_name is None
    assert proposal.unit_id is None
    assert proposal.unit_name is None
    assert len(proposal.candidate_topics) >= 2


def test_unmapped_question_without_keywords(classifier: TaxonomyClassifierService) -> None:
    """Verifies that questions with generic or missing syllabus terminology are left UNMAPPED."""
    proposal = classifier.classify(4, "Answer any five questions from this section. Write neat answers.")
    assert proposal.confidence == "UNMAPPED"
    assert proposal.method == "NO_MATCH"
    assert proposal.topic_id is None
    assert proposal.topic_name is None


def test_domain_guardrail_rejection(classifier: TaxonomyClassifierService) -> None:
    """Verifies negative guardrails disqualify candidate topics (e.g., polarizability cannot be ionization energy)."""
    proposal = classifier.classify(
        5, "Explain polarizability and polarizing power using Fajan's rule and ionization potential."
    )
    # Polarizability is guarded against being labeled Ionization Energy; it should match Polarizability
    assert proposal.topic_id == 44
    assert proposal.topic_name == "Polarizability and Polarizing Power"


def test_malformed_and_short_questions(classifier: TaxonomyClassifierService) -> None:
    """Verifies short 2-word questions map accurately if terminology is exact, and single-char text fails cleanly."""
    # Short exact prompt
    p1 = classifier.classify(6, "Elastic body")
    assert p1.confidence == "HIGH"
    assert p1.topic_id == 30
    assert p1.topic_name == "Material Properties"

    # Empty / malformed text
    p2 = classifier.classify(7, "  ")
    assert p2.confidence == "UNMAPPED"
    assert p2.topic_id is None

    p3 = classifier.classify(8, "x")
    assert p3.confidence == "UNMAPPED"
    assert p3.topic_id is None


def test_latex_and_chemical_notation_normalization(classifier: TaxonomyClassifierService) -> None:
    """Verifies mathematical LaTeX syntax and chemical formulas normalize for matching."""
    proposal = classifier.classify(
        9, "Explain why $H_2^+$ molecular ion is less stable than $H_2$ molecule with LCAO diagram."
    )
    assert proposal.confidence == "HIGH"
    assert proposal.topic_id == 48
    assert proposal.topic_name == "Molecular Orbital Theory"
